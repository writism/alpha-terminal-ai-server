"""투자 워크플로우 YouTube 수집 데이터 저장소.

MySQL  : investment_youtube_logs, investment_youtube_videos
PostgreSQL : investment_youtube_video_comments
"""
import traceback
from datetime import datetime, timezone
from typing import List, Optional

from app.domains.youtube.domain.entity.youtube_comment import YouTubeComment
from app.domains.youtube.domain.entity.youtube_video import YouTubeVideo
from app.domains.investment.infrastructure.orm.investment_youtube_log_orm import InvestmentYouTubeLogORM
from app.domains.investment.infrastructure.orm.investment_youtube_video_orm import InvestmentYouTubeVideoORM
from app.domains.investment.infrastructure.orm.investment_youtube_comment_orm import InvestmentYouTubeCommentORM
from app.infrastructure.database.session import SessionLocal
from app.infrastructure.database.pg_session import PgSessionLocal

# ---------------------------------------------------------------------------
# 댓글 조회 (감성 분석 UseCase용)
# ---------------------------------------------------------------------------

def fetch_video_ids_by_company(company: str, max_logs: int = 3) -> list[str]:
    """MySQL: 종목명으로 최근 수집 log의 video_id 목록을 반환한다.

    정확 일치 → 유사 검색(LIKE) 순으로 시도한다.
    max_logs 개의 최근 로그에 속한 영상 ID만 반환한다.
    """
    mysql_db = SessionLocal()
    try:
        logs = (
            mysql_db.query(InvestmentYouTubeLogORM)
            .filter(InvestmentYouTubeLogORM.company == company)
            .order_by(InvestmentYouTubeLogORM.created_at.desc())
            .limit(max_logs)
            .all()
        )
        if not logs:
            logs = (
                mysql_db.query(InvestmentYouTubeLogORM)
                .filter(InvestmentYouTubeLogORM.company.like("%{}%".format(company.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")), escape="\\"))
                .order_by(InvestmentYouTubeLogORM.created_at.desc())
                .limit(max_logs)
                .all()
            )
        log_ids = [log.id for log in logs]
        if not log_ids:
            print(f"[Repository] ⚠ company={company!r} 수집 로그 없음")
            return []

        videos = (
            mysql_db.query(InvestmentYouTubeVideoORM)
            .filter(InvestmentYouTubeVideoORM.log_id.in_(log_ids))
            .all()
        )
        video_ids = [v.video_id for v in videos]
        print(f"[Repository] company={company!r} → log {len(log_ids)}건 → video {len(video_ids)}건")
        return video_ids
    finally:
        mysql_db.close()


def fetch_video_ids_by_log_id(log_id: int) -> list[str]:
    """MySQL: log_id로 video_id 목록을 반환한다."""
    mysql_db = SessionLocal()
    try:
        videos = (
            mysql_db.query(InvestmentYouTubeVideoORM)
            .filter(InvestmentYouTubeVideoORM.log_id == log_id)
            .all()
        )
        video_ids = [v.video_id for v in videos]
        print(f"[Repository] log_id={log_id} → video {len(video_ids)}건")
        return video_ids
    finally:
        mysql_db.close()


def fetch_comment_texts(video_ids: list[str], limit: int = 250) -> list[str]:
    """PostgreSQL: video_id 목록에 속한 댓글 텍스트를 최신순으로 반환한다.

    Args:
        video_ids: 조회 대상 video_id 목록
        limit: 최대 댓글 수 (기본 250건 — LLM 입력 상한)

    Returns:
        댓글 텍스트 리스트. video_ids 가 비어 있으면 [] 반환.
    """
    if not video_ids:
        print("[Repository] ⚠ video_ids 없음 → 댓글 조회 건너뜀")
        return []
    pg_db = PgSessionLocal()
    try:
        comments = (
            pg_db.query(InvestmentYouTubeCommentORM)
            .filter(InvestmentYouTubeCommentORM.video_id.in_(video_ids))
            .order_by(InvestmentYouTubeCommentORM.created_at.desc())
            .limit(limit)
            .all()
        )
        texts = [c.text for c in comments]
        print(f"[Repository] video {len(video_ids)}건 → 댓글 {len(texts)}건 조회")
        return texts
    finally:
        pg_db.close()


def _parse_published_at(value: str) -> Optional[datetime]:
    """ISO 8601 문자열을 datetime으로 변환한다. 실패 시 None 반환."""
    if not value:
        return None
    for fmt in ("%Y-%m-%dT%H:%M:%SZ", "%Y-%m-%dT%H:%M:%S%z", "%Y-%m-%d"):
        try:
            dt = datetime.strptime(value.replace("+00:00", "Z"), fmt)
            return dt.replace(tzinfo=None)  # DB 저장용 naive datetime
        except ValueError:
            continue
    print(f"[Repository] ⚠ published_at 파싱 실패 (None 처리): {value!r}")
    return None


def save_youtube_collection(
    query: str,
    company: Optional[str],
    videos: List[YouTubeVideo],
    comments_by_video: dict[str, List[YouTubeComment]],
) -> None:
    """YouTube 수집 결과를 MySQL + PostgreSQL에 저장한다.

    부분 실패 허용: 개별 저장 실패 시 traceback을 출력하고 계속 진행한다.

    Args:
        query: 원본 투자 질의
        company: 파싱된 종목명 (없으면 None)
        videos: YouTubeVideo 엔티티 목록
        comments_by_video: video_id → YouTubeComment 목록
    """
    log_id: Optional[int] = None

    # --- MySQL: 로그 + 영상 저장 ---
    mysql_db = SessionLocal()
    try:
        # 1. 수집 로그 생성
        log_orm = InvestmentYouTubeLogORM(
            query=query,
            company=company,
            video_count=len(videos),
            status="success" if videos else "partial",
        )
        mysql_db.add(log_orm)
        mysql_db.flush()
        log_id = log_orm.id
        print(f"[Repository][MySQL] 로그 생성 log_id={log_id} video_count={len(videos)}")

        # 2. 영상 저장
        for video in videos:
            try:
                video_orm = InvestmentYouTubeVideoORM(
                    log_id=log_id,
                    video_id=video.video_id,
                    title=video.title,
                    channel_name=video.channel_name,
                    published_at=_parse_published_at(video.published_at),
                    video_url=video.video_url,
                    view_count=video.view_count,
                )
                mysql_db.add(video_orm)
                print(f"[Repository][MySQL] 영상 저장: {video.video_id} | {video.title[:40]}")
            except Exception:
                print(f"[Repository][MySQL] ✗ 영상 저장 실패: {video.video_id}")
                traceback.print_exc()

        mysql_db.commit()
        print(f"[Repository][MySQL] commit 완료")

    except Exception:
        mysql_db.rollback()
        print(f"[Repository][MySQL] ✗ 트랜잭션 실패 → rollback")
        traceback.print_exc()
    finally:
        mysql_db.close()

    # --- PostgreSQL: 댓글 저장 ---
    if not comments_by_video:
        print(f"[Repository][PG] 댓글 없음 — 저장 건너뜀")
        return

    pg_db = PgSessionLocal()
    try:
        total_comments = 0
        for video_id, comments in comments_by_video.items():
            for comment in comments:
                try:
                    existing = (
                        pg_db.query(InvestmentYouTubeCommentORM)
                        .filter(InvestmentYouTubeCommentORM.comment_id == comment.comment_id)
                        .first()
                    )
                    if existing:
                        continue  # 중복 건너뜀
                    comment_orm = InvestmentYouTubeCommentORM(
                        video_id=video_id,
                        comment_id=comment.comment_id,
                        author_name=comment.author_name,
                        text=comment.text,
                        published_at=comment.published_at,
                        like_count=comment.like_count,
                    )
                    pg_db.add(comment_orm)
                    total_comments += 1
                except Exception:
                    print(f"[Repository][PG] ✗ 댓글 저장 실패: {comment.comment_id}")
                    traceback.print_exc()

        pg_db.commit()
        print(f"[Repository][PG] commit 완료 | 댓글 {total_comments}건 저장")

    except Exception:
        pg_db.rollback()
        print(f"[Repository][PG] ✗ 트랜잭션 실패 → rollback")
        traceback.print_exc()
    finally:
        pg_db.close()

# 세션 기록: 2026-03-25 — 모바일 OAuth 인증 & API 프록시 수정

## 배경 / 문제

모바일(외부 기기)에서 `http://192.168.1.1:3000`에 접속 시 카카오 인증 버튼을 누르면
`localhost:33333 사이트에 연결할 수 없음` 오류가 발생.
인증 성공 후에도 로그인 화면으로 다시 돌아가는 문제.

## 원인 분석

| 단계 | 문제 |
|---|---|
| 1 | 프론트 `NEXT_PUBLIC_API_BASE_URL=http://localhost:33333` → 모바일 브라우저가 자기 자신의 localhost에 접속 시도 |
| 2 | `KAKAO_REDIRECT_URI=http://localhost:33333/...` → 카카오 인증 후 모바일이 localhost:33333에 직접 접속 시도 |
| 3 | `FRONTEND_AUTH_CALLBACK_URL=http://localhost:3000/auth-callback` → 인증 완료 후 리다이렉트가 localhost:3000으로 가서 모바일에서 실패 |

## 해결 내용

### BL-FE-37 — Next.js rewrites API 프록시 (프론트엔드)

- `next.config.ts` — `rewrites()` 추가: `/api/:path*` → `http://localhost:33333/:path*`
- `.env.local` — `NEXT_PUBLIC_API_BASE_URL=http://localhost:33333` → `/api`
- `.env.example` — 동일하게 업데이트 + 주석 추가
- `docs/backlog/BL-FE-37-nextjs-rewrite-api-proxy.md` — 백로그 신규 생성

### BL-BE-18 — 모바일 OAuth 리다이렉트 URL 환경변수화 (백엔드)

- `.env` — 세 환경변수 수정:
  - `KAKAO_REDIRECT_URI` → `http://192.168.1.1:3000/api/kakao-authentication/request-access-token-after-redirection`
  - `CORS_ALLOWED_FRONTEND_URL` → `http://192.168.1.1:3000`
  - `FRONTEND_AUTH_CALLBACK_URL` → `http://192.168.1.1:3000/auth-callback`
- `.env.example` — 위 세 변수 예시값 및 주석 추가
- `docs/backlog/BL-BE-18-mobile-oauth-env-config.md` — 백로그 신규 생성

## 커밋

### 프론트엔드 (`feat/bl-fe-30-37-heatmap-pagination-proxy`)
- `db796ec` — `feat(front): heatmap UI, pagination, Storybook, API rewrites` (BL-FE-37 포함)
- `5760617` — `docs(front): backlog BL-FE-30 through BL-FE-37`

### 백엔드 (`feat/bl-be-04-17-backlog-heatmap-pipeline`)
- `e8717c5` — `docs(backlog): BL-BE-18 모바일 OAuth 리다이렉트 URL 환경변수화`

## PR

| 저장소 | PR | 상태 |
|---|---|---|
| alpha-desk-frontend (upstream) | https://github.com/EDDI-RobotAcademy/alpha-desk-frontend/pull/19 | OPEN |
| alpha-desk-ai-server (upstream) | https://github.com/EDDI-RobotAcademy/alpha-desk-ai-server/pull/28 | OPEN |

## 주의사항

- 카카오 개발자 콘솔에 `http://192.168.1.1:3000/api/kakao-authentication/request-access-token-after-redirection` Redirect URI 추가 등록 필요
- `.env`는 `.gitignore` 처리 — 실제 IP/시크릿은 팀원 각자 설정
- 로컬 PC 개발 시 `.env`의 세 값을 `localhost` 기준으로 맞춰야 함

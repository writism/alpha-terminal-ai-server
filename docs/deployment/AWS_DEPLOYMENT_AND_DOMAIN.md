# Alpha Desk — AWS 배포 및 도메인 연결 가이드

> **실제 운영 구성 문서**: [AWS_EC2_HTTPS_RUNBOOK.md](./AWS_EC2_HTTPS_RUNBOOK.md)  
> 이 문서는 일반 옵션 개요이며, 실제 alpha-desk에 적용된 구성(DuckDNS + Let's Encrypt + nginx)은 위 Runbook을 참고한다.

---

> **대상 스택(가정):** Next.js 프론트엔드, FastAPI 백엔드(`alpha-desk-ai-server`), MySQL, Redis, 외부 API·OAuth 콜백 URL 의존.

이 문서는 **처음 AWS에 올려볼 때의 절차**와 **도메인을 사서(또는 무료에 가깝게) 연결하는 흐름**을 순서대로 정리한 보고용 자료입니다. 실제 비용·한도는 AWS 및 등록기관 정책이 바뀔 수 있으므로, 작업 전에 각 서비스 공식 가격·무료 범위를 한 번 더 확인하세요.

---

## 1. 배포 전에 결정할 것

| 항목 | 선택지 요약 |
|------|-------------|
| **컴퓨트** | 단일 EC2 + Docker(학습·소규모) / ECS Fargate 또는 EKS(운영 확장) / Elastic Beanstalk(간단 PaaS) |
| **DB** | EC2와 같은 머신의 Docker MySQL(초기) / **Amazon RDS for MySQL**(권장·백업·패치) |
| **Redis** | Docker Redis(초기) / **ElastiCache for Redis**(권장) |
| **프론트** | S3 + CloudFront 정적 호스팅, 또는 **Vercel**(AWS 밖)에 FE만 두고 API만 AWS |
| **HTTPS** | **ACM(인증서)** + ALB 또는 CloudFront |
| **비밀** | `.env` 대신 **SSM Parameter Store** 또는 **Secrets Manager** |

Alpha Desk는 **쿠키 기반 인증·CORS·Kakao 리다이렉트 URI**가 있으므로, 배포 후 **`CORS_ALLOWED_FRONTEND_URL`**, **`FRONTEND_AUTH_CALLBACK_URL`**, Kakao 개발자 콘솔의 **사이트 도메인·Redirect URI**를 **실제 도메인/HTTPS**로 맞추는 작업이 필수입니다.

---

## 2. AWS 계정 준비

1. [AWS 가입](https://aws.amazon.com/) — 결제 수단 등록(무료 한도 내에서도 필요한 경우가 많음).
2. **루트 계정 MFA** 설정.
3. 일상 작업용으로 **IAM 사용자** 생성(AdministratorAccess 또는 최소 권한 정책).
4. **리전 선택** (예: `ap-northeast-2` 서울) — 리소스·도메인·인증서는 리전에 종속되는 항목이 있음(ACM은 **us-east-1**에서 발급한 인증서를 CloudFront에 쓰는 등 예외 규칙이 있음).

**무료 티어:** 12개월 제한이 있는 항목과, Always Free에 가까운 항목이 섞여 있습니다. EC2 `t2.micro`/`t3.micro` 등은 조건·기간을 반드시 확인하세요.

---

## 3. 권장 학습용 경로: EC2 한 대 + Docker Compose

소규모·PoC에 적합합니다. 프로덕션에서는 RDS·ElastiCache·다중 AZ·백업 정책을 검토합니다.

### 3.1 VPC·네트워크

1. 기본 VPC를 쓰거나 VPC를 새로 만듭니다.
2. **퍼블릭 서브넷**에 EC2를 두고, 보안 그룹에서 **22(SSH, 관리용·나중에 닫거나 bastion 사용)**, **80/443(웹)**, 백엔드 포트(예: **33333** 직접 노출은 피하고 **443만 열고 리버스 프록시** 권장)를 정의합니다.

### 3.2 EC2 인스턴스

1. Amazon Linux 2023 또는 Ubuntu LTS AMI 선택.
2. 인스턴스 타입: 무료 티어 가능한 `t3.micro` 등.
3. 키 페어 생성·다운로드(분실 시 SSH 불가).
4. 퍼블릭 IP(또는 탄력적 IP 할당해 고정).
5. SSH 접속 후 Docker·Docker Compose 설치.

### 3.3 애플리케이션 배치

1. 저장소 클론 또는 CI에서 아티팩트 전송.
2. **백엔드:** `uvicorn` 또는 Gunicorn+Uvicorn worker, 프로덕션에서는 `systemd` 또는 `docker compose`로 상주 실행.
3. **MySQL·Redis:** 같은 호스트의 Compose 서비스로 시작하거나, RDS·ElastiCache로 분리.
4. 환경 변수: DB URL, Redis, `AUTH_SECRET`, API 키 등은 파일 대신 **SSM/Secrets Manager** 주입을 권장.

### 3.4 리버스 프록시(권장)

- EC2에 **Nginx** 또는 **Caddy**를 두고 `443` → `127.0.0.1:33333`(FastAPI)로 프록시.
- TLS 종료는 **ACM + ALB**로 할 수도 있고, EC2에서 **Let’s Encrypt**(Certbot)로 직접 발급할 수도 있습니다(ALB 없이 단순화할 때).

---

## 4. 운영에 가까운 경로(요약)

- **컴퓨트:** ECS Fargate + ALB(또는 App Runner로 단순화).
- **DB:** RDS MySQL(Multi-AZ는 비용 증가).
- **Redis:** ElastiCache.
- **이미지:** ECR에 빌드한 Docker 이미지 푸시.
- **배포:** CodePipeline / GitHub Actions → ECR 푸시 → ECS 서비스 업데이트.

이 경로는 초기 설정 공수가 크지만 장애 대응·스케일에 유리합니다.

---

## 5. “무료 도메인”과 현실

| 구분 | 설명 |
|------|------|
| **AWS Route 53에서 도메인 “무료”** | 일반적으로 **없음**. 도메인 등록은 연 단위 과금, 호스팅 영역(Hosted Zone)도 월 소액이 붙는 것이 일반적입니다. |
| **진짜 $0에 가까운 방법** | (1) **테스트용**으로만 `nip.io` / `sslip.io` 형태의 **IP 기반 호스트명** 사용. (2) 일부 **학생/스타트업 패키지**(GitHub Student 등)에서 제공하는 크레딧·쿠폰. (3) **서브도메인**만 무료인 서비스(Vercel 기본 도메인 등)에 FE를 두고 API는 IP·별도 호스트. |
| **저렴한 유료 도메인** | `.xyz`, `.site` 등 프로모션 시 **1년 1~2달러대**인 경우가 있음(등록기관·시기별 상이). **Cloudflare Registrar**는 많은 TLD를 원가에 가깝게 판매. |
| **무료 도메인 함정** | 과거 Freenom 등 일부 무료 TLD는 **불안정·악용·회수 이슈**가 보고된 바 있어, **서비스 신뢰용으로는 비권장**입니다. |

**보고 결론:** “AWS에 올리면서 완전 무료 커스텀 도메인”은 기대하기 어렵고, **저렴한 1년 등록 + Route 53 또는 Cloudflare DNS** 조합이 현실적입니다.

---

## 6. 도메인 구입 후 AWS에 연결하는 절차

아래는 **가장 흔한 패턴: 도메인은 Cloudflare(또는 가비아 등)에서 구입, DNS만 관리** 또는 **Route 53에서 도메인+DNS 일원화**입니다.

### 패턴 A — Route 53에 도메인 등록

1. Route 53 → **도메인 등록**에서 원하는 이름 검색·구매.
2. 자동으로 **Hosted Zone**이 생깁니다.
3. **ACM**에서 인증서 요청(도메인·와일드카드 `*.example.com` 등).
4. **DNS 검증** 레코드는 Route 53에 자동 생성 가능.
5. **ALB** 생성 → 리스너 HTTPS(443)에 ACM 인증서 연결 → 대상 그룹에 EC2(또는 ECS) 연결.
6. Hosted Zone에 **A 레코드(별칭)** 로 ALB를 가리킵니다.

### 패턴 B — 외부(Cloudflare 등)에서 도메인 구입

1. 등록기관에서 도메인 구매.
2. **네임서버**를 Cloudflare로 바꾸거나, AWS Route 53 Hosted Zone을 만들고 등록기관 쪽 NS를 Route 53이 안내하는 값으로 설정.
3. ACM 검증용 **CNAME**을 등록기관 DNS에 추가.
4. **A/AAAA 또는 CNAME**으로 ALB·CloudFront·EC2(고정 IP)를 가리킵니다.

### 프론트·백엔드 분리 예시

- `app.example.com` → CloudFront + S3(Next.js export 또는 SSR은 Lambda@Edge/별도 호스팅).
- `api.example.com` → ALB → FastAPI.

쿠키 **`Domain`·`SameSite`** 와 CORS는 **같은 eTLD+1** 또는 명시적 설정으로 맞춥니다.

---

## 7. 배포 후 필수 체크리스트 (Alpha Desk)

- [ ] `CORS_ALLOWED_FRONTEND_URL` = 실제 프론트 URL(HTTPS).
- [ ] `FRONTEND_AUTH_CALLBACK_URL` = Kakao 로그인 후 돌아올 프론트 콜백 URL.
- [ ] Kakao 개발자 콘솔: **Redirect URI**, **JavaScript 키 도메인** 등록.
- [ ] `OPENAI_API_KEY` 등 시크릿이 이미지·로그에 노출되지 않음.
- [ ] MySQL·Redis **비밀번호** 강도 및 보안 그룹(내부망만 DB 포트 오픈).
- [ ] **HTTPS** 강제(HTTP → HTTPS 리다이렉트).
- [ ] (선택) **WAF**, **백업 스냅샷**, **CloudWatch 알람**.

---

## 8. 요약 보고

1. **AWS 배포**는 **EC2 + Docker**로 빠르게 학습하거나, **ECS + RDS + ElastiCache**로 운영 품질을 올리는 두 갈래가 일반적입니다.  
2. **무료 커스텀 도메인**은 사실상 제한적이며, **저렴한 유료 도메인 + Route 53 또는 외부 DNS**가 안정적입니다.  
3. **도메인 연결**의 핵심은 **DNS A/별칭/CNAME**으로 **ALB 또는 CloudFront**를 가리키고, **ACM으로 TLS**를 적용하는 것입니다.  
4. Alpha Desk는 **OAuth·CORS·쿠키**가 도메인에 묶이므로, 인프라 올린 뒤 **환경 변수와 Kakao 콘솔을 같은 도메인 체계로 재설정**하는 단계가 반드시 필요합니다.

---

## 9. 참고 링크

- [AWS 시작하기](https://aws.amazon.com/getting-started/)
- [Route 53 도메인 등록](https://docs.aws.amazon.com/Route53/latest/DeveloperGuide/domain-register.html)
- [ACM 인증서 요청](https://docs.aws.amazon.com/acm/latest/userguide/gs-acm-request-public.html)
- [Elastic Load Balancing + ACM](https://docs.aws.amazon.com/elasticloadbalancing/latest/application/listener-authenticate-users.html) (리스너 설정 시 ACM 연동 문서 트리 참고)

---

*문서 작성 목적: 내부 보고 및 온보딩. 인프라 비용·규정은 배포 시점의 AWS 공식 문서를 우선합니다.*

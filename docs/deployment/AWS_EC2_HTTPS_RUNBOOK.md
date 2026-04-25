# Alpha Desk — AWS EC2 HTTPS 배포 Runbook

> 이 문서는 실제 운영 중인 구성을 기준으로 작성되었다.  
> 처음부터 다시 구축하거나, 인스턴스를 교체할 때 이 순서대로 따라가면 동일한 환경이 된다.

---

## 전체 구성 요약

```
인터넷
  │ HTTPS (443)
  ▼
DuckDNS (alpha-desk.duckdns.org → 52.79.151.142)
  │
  ▼
AWS EC2 t4g.small (ap-northeast-2, Amazon Linux 2023, arm64)
  │
  ├─ [alphadesk-nginx]  포트 80/443, SSL 종료, Let's Encrypt 인증서
  │       │
  │       └─ proxy_pass → alphadesk-web:3000
  │
  ├─ [alphadesk-web]    Next.js (포트 3000)
  ├─ [alphadesk-api]    FastAPI (포트 33333)
  ├─ [alphadesk-mysql]  MySQL (포트 3306)
  ├─ [alphadesk-redis]  Redis (포트 6379)
  └─ [pg-container]     PostgreSQL (포트 5432)

네트워크:
  alphadesk-network                      ← api, mysql, redis, pg, nginx
  alpha-terminal-frontend_multi-agent-net ← web, nginx (둘 다 연결됨)
```

---

## 1. EC2 인스턴스 정보

| 항목 | 값 |
|------|----|
| 인스턴스 ID | `i-0ed097f3ac9e9f5ae` (alpha-desk) |
| 인스턴스 타입 | `t4g.small` (ARM64 Graviton2, 2GB RAM) |
| AMI | Amazon Linux 2023 (arm64) |
| 리전 | `ap-northeast-2` (서울) |
| 퍼블릭 IP | `52.79.151.142` (**Elastic IP 미적용** — 재시작 시 변경 가능) |
| SSH 접속 | `ssh -i ~/dev/codelab/alpha-desk.pem ec2-user@52.79.151.142` |

> **주의**: Elastic IP가 없으므로 인스턴스 Stop/Start 시 퍼블릭 IP가 바뀐다.  
> IP가 바뀌면 DuckDNS를 수동으로 업데이트해야 한다 (→ [섹션 5](#5-ec2-ip-변경-시-duckdns-업데이트) 참고).

### 보안 그룹 인바운드 규칙

| 포트 | 프로토콜 | 허용 대상 | 용도 |
|------|----------|-----------|------|
| 22 | TCP | 관리자 IP 지정 | SSH |
| 80 | TCP | 0.0.0.0/0 | HTTP (→ HTTPS 리다이렉트) |
| 443 | TCP | 0.0.0.0/0 | HTTPS |

> 33333(API), 3306(MySQL), 6379(Redis), 5432(PostgreSQL) 포트는 **외부 미노출**.  
> 내부 컨테이너 간 Docker 네트워크로만 통신한다.

---

## 2. EC2 초기 설정 (처음 인스턴스 생성 시)

```bash
# SSH 접속
ssh -i ~/dev/codelab/alpha-desk.pem ec2-user@<EC2_IP>

# Docker 설치 (Amazon Linux 2023)
sudo dnf update -y
sudo dnf install -y docker
sudo systemctl enable docker
sudo systemctl start docker
sudo usermod -aG docker ec2-user
# → 재접속 후 sudo 없이 docker 사용 가능

# Docker 네트워크 생성
docker network create alphadesk-network
```

---

## 3. DuckDNS 도메인 설정

DuckDNS는 무료 DDNS 서비스다. 별도 도메인 구매 없이 `*.duckdns.org` 서브도메인을 사용한다.

### 3.1 도메인 등록

1. [https://www.duckdns.org](https://www.duckdns.org) 에서 GitHub/Google 계정으로 로그인
2. 도메인명 입력 → `alpha-desk` 등록
3. **토큰 확인**: `8bd95764-6942-488f-b5cb-b173de9032a1`
4. EC2 퍼블릭 IP 입력 → `update domain` 클릭

### 3.2 IP 업데이트 방법 (수동)

브라우저 또는 curl로 아래 URL을 호출하면 IP가 업데이트된다:

```
https://www.duckdns.org/update?domains=alpha-desk&token=8bd95764-6942-488f-b5cb-b173de9032a1&ip=<새IP>
```

---

## 4. Let's Encrypt SSL 인증서 발급 (certbot)

nginx 컨테이너를 올리기 전에 인증서를 먼저 발급한다.

### 4.1 certbot 설치

```bash
sudo dnf install -y python3-certbot
# 또는
sudo pip3 install certbot
```

### 4.2 인증서 발급 (standalone 모드)

standalone 모드는 certbot이 직접 80포트를 열어 인증한다.  
nginx가 이미 실행 중이면 먼저 중단한다.

```bash
# nginx 컨테이너가 실행 중이면 중단
docker stop alphadesk-nginx 2>/dev/null || true

# 인증서 발급
sudo certbot certonly --standalone -d alpha-desk.duckdns.org

# 이메일 입력, 이용약관 동의 → 발급 완료
```

### 4.3 발급 결과

```
인증서 위치: /etc/letsencrypt/live/alpha-desk.duckdns.org/
  - fullchain.pem   ← nginx ssl_certificate
  - privkey.pem     ← nginx ssl_certificate_key
만료: 90일 (자동 갱신 설정 필요)
현재 만료일: 2026-07-08
```

### 4.4 자동 갱신 설정

```bash
# crontab 편집
sudo crontab -e

# 아래 라인 추가 (매일 새벽 3시 갱신 시도)
0 3 * * * certbot renew --quiet && docker restart alphadesk-nginx
```

### 4.5 수동 갱신 (만료 임박 시)

```bash
docker stop alphadesk-nginx
sudo certbot renew
docker start alphadesk-nginx
```

---

## 5. Docker 컨테이너 구성

### 5.1 nginx

nginx 컨테이너가 SSL 종료와 리버스 프록시를 담당한다.

**설정 파일 위치**:
- EC2: `/home/ec2-user/nginx/default.conf`
- 로컬: `/Users/sulee/dev/codelab/nginx/default.conf`

**`default.conf` 내용**:

```nginx
server {
    listen 80;
    server_name alpha-desk.duckdns.org;
    return 301 https://$host$request_uri;
}

server {
    listen 443 ssl;
    server_name alpha-desk.duckdns.org;

    ssl_certificate     /etc/letsencrypt/live/alpha-desk.duckdns.org/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/alpha-desk.duckdns.org/privkey.pem;
    ssl_protocols       TLSv1.2 TLSv1.3;

    error_page 502 503 504 /maintenance.html;
    location = /maintenance.html {
        root /usr/share/nginx/html;
        internal;
    }

    # SSE 스트리밍 전용 (파이프라인, AI 분석)
    location /api/pipeline/run-stream {
        proxy_pass http://alphadesk-web:3000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_http_version 1.1;
        proxy_set_header Connection "";
        proxy_buffering off;
        proxy_cache off;
        proxy_read_timeout 300s;
    }

    location / {
        proxy_pass http://alphadesk-web:3000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_read_timeout 60s;
    }
}
```

**nginx 컨테이너 실행**:

```bash
docker run -d \
  --name alphadesk-nginx \
  -p 80:80 -p 443:443 \
  -v /home/ec2-user/nginx/default.conf:/etc/nginx/conf.d/default.conf:ro \
  -v /etc/letsencrypt:/etc/letsencrypt:ro \
  --network alphadesk-network \
  --restart unless-stopped \
  nginx:alpine

# alphadesk-web은 별도 네트워크에 있으므로 nginx를 거기에도 연결
docker network connect alpha-terminal-frontend_multi-agent-net alphadesk-nginx
```

### 5.2 MySQL

```bash
docker run -d \
  --name alphadesk-mysql \
  -e MYSQL_ROOT_PASSWORD=<비밀번호> \
  -e MYSQL_DATABASE=alphadesk \
  -e MYSQL_USER=alphadesk \
  -e MYSQL_PASSWORD=<비밀번호> \
  -v alphadesk-mysql-data:/var/lib/mysql \
  --network alphadesk-network \
  --restart unless-stopped \
  mysql:8.0
```

### 5.3 Redis

```bash
docker run -d \
  --name alphadesk-redis \
  -v alphadesk-redis-data:/data \
  --network alphadesk-network \
  --restart unless-stopped \
  redis:alpine redis-server --appendonly yes
```

### 5.4 PostgreSQL (pgvector)

```bash
docker run -d \
  --name pg-container \
  -e POSTGRES_USER=eddi \
  -e POSTGRES_PASSWORD=<비밀번호> \
  -e POSTGRES_DB=appdb \
  -v alphadesk-pg-data:/var/lib/postgresql/data \
  --network alphadesk-network \
  --restart unless-stopped \
  pgvector/pgvector:pg16
```

### 5.5 백엔드 (FastAPI)

CI/CD가 자동 배포하지만, 수동으로 실행할 때는 아래 명령을 사용한다.

```bash
docker run -d \
  --name alphadesk-api \
  --env-file /home/ec2-user/alpha-terminal-ai-server/.env \
  --network alphadesk-network \
  --ulimit nofile=32768:65536 \
  --restart unless-stopped \
  ghcr.io/writism/alpha-terminal-api:latest
```

### 5.6 프론트엔드 (Next.js)

```bash
docker run -d \
  --name alphadesk-web \
  -e BACKEND_URL=http://alphadesk-api:33333 \
  --network alpha-terminal-frontend_multi-agent-net \
  --restart unless-stopped \
  ghcr.io/writism/multi-agent-ui:latest
```

> alphadesk-web은 CI/CD 자동 배포 시 `alpha-terminal-frontend_multi-agent-net` 네트워크로 기동된다.  
> nginx가 이 네트워크에도 연결되어 있어야 `proxy_pass http://alphadesk-web:3000` 이 동작한다.

---

## 6. GitHub Actions CI/CD

### 6.1 배포 흐름

```
main 브랜치 push / PR merge
  │
  ├─ [GitHub 서버 - ubuntu-latest]
  │    1. docker buildx build (linux/arm64)
  │    2. ghcr.io push
  │
  └─ [EC2 self-hosted runner]
       1. docker pull 최신 이미지
       2. docker stop/rm 기존 컨테이너
       3. docker run --env-file
       4. 헬스체크
```

### 6.2 워크플로우 파일

| 레포 | 파일 | 이미지 | Runner 레이블 |
|------|------|--------|---------------|
| alpha-terminal-ai-server | `.github/workflows/main.yml` | `ghcr.io/writism/alpha-terminal-api:latest` | `alpha-terminal-api` |
| alpha-terminal-frontend | `.github/workflows/main.yml` | `ghcr.io/writism/multi-agent-ui:latest` | `multi-agent-ui` |

### 6.3 Self-hosted Runner 위치 및 관리

```bash
# Runner 상태 확인
sudo systemctl status actions.runner.*

# Runner 재시작 (멈췄을 때)
sudo systemctl restart actions.runner.writism-alpha-terminal-ai-server.alpha-terminal-api
```

### 6.4 GitHub Secrets

| Secret | 내용 |
|--------|------|
| `REPO_USER` | `writism` |
| `GHCR_TOKEN` | ghcr.io push 권한 PAT (`write:packages`) |
| `FRONTEND_ENV` | FE `.env` 파일 전체 내용 |

### 6.5 주의: Dockerfile `--platform` 하드코딩 금지

EC2는 arm64인데, GitHub Actions 빌드 서버는 x86_64다. QEMU 에뮬레이션으로 arm64 이미지를 빌드하므로 `FROM --platform` 하드코딩 시 크래시가 난다.

```dockerfile
# ❌ 금지 — QEMU SIGILL 크래시
FROM --platform=linux/arm64 node:20-alpine

# ✅ 올바른 방식
FROM node:20-alpine
```

---

## 7. 배포 후 환경 변수 설정

### 7.1 백엔드 `.env` 위치

```
EC2: /home/ec2-user/alpha-terminal-ai-server/.env
```

OAuth, CORS, 콜백 URL을 HTTPS 도메인 기준으로 설정해야 한다.

```bash
# 현재 운영 중 값
KAKAO_REDIRECT_URI=https://alpha-desk.duckdns.org/api/kakao-authentication/request-access-token-after-redirection
CORS_ALLOWED_FRONTEND_URL=https://alpha-desk.duckdns.org
FRONTEND_AUTH_CALLBACK_URL=https://alpha-desk.duckdns.org/auth-callback
```

### 7.2 카카오 개발자 콘솔

[카카오 개발자 콘솔](https://developers.kakao.com) → 앱 → 카카오 로그인 설정에서:
- **Redirect URI** 등록: `https://alpha-desk.duckdns.org/api/kakao-authentication/request-access-token-after-redirection`
- **사이트 도메인** 등록: `https://alpha-desk.duckdns.org`

---

## 8. 운영 중 자주 발생하는 문제

### 8.1 배포 후 502 Bad Gateway

**원인**: 컨테이너 재배포 시 Docker 내부 IP가 바뀌는데 nginx가 기존 IP를 캐싱한다.

**즉시 해결**:
```bash
ssh -i ~/dev/codelab/alpha-desk.pem ec2-user@52.79.151.142
docker restart alphadesk-nginx
```

**근본 해결 (미적용)**: nginx.conf에 Docker 내장 DNS resolver 추가:
```nginx
resolver 127.0.0.11 valid=30s;
set $upstream_web alphadesk-web;
proxy_pass http://$upstream_web:3000;
```

### 8.2 EC2 IP 변경 시 (인스턴스 재시작 후)

Elastic IP가 없으므로 Stop/Start 시 IP가 바뀐다.

```bash
# 1. 새 IP 확인 (AWS 콘솔 또는 인스턴스 내부)
curl http://169.254.169.254/latest/meta-data/public-ipv4

# 2. DuckDNS 업데이트
curl "https://www.duckdns.org/update?domains=alpha-desk&token=8bd95764-6942-488f-b5cb-b173de9032a1&ip=<새IP>"

# 3. SSH 보안 그룹 IP도 업데이트 필요 (현재 특정 IP로 제한됨)
#    AWS 콘솔 → EC2 → Security Groups → 인바운드 규칙 편집
```

### 8.3 nginx 재시작 루프 (`host not found in upstream`)

alphadesk-web이 nginx보다 늦게 기동되면 발생한다.

```bash
# alphadesk-web이 완전히 뜬 후 nginx 재시작
docker ps | grep alphadesk-web   # Running 상태 확인
docker restart alphadesk-nginx
```

### 8.4 nginx가 alphadesk-web에 접근 못하는 경우 (네트워크 불일치)

```bash
# nginx가 연결된 네트워크 확인
docker inspect alphadesk-nginx | grep -A 20 '"Networks"'

# alphadesk-web의 네트워크 확인
docker inspect alphadesk-web | grep -A 20 '"Networks"'

# nginx를 alphadesk-web의 네트워크에 추가 연결
docker network connect alpha-terminal-frontend_multi-agent-net alphadesk-nginx
docker restart alphadesk-nginx
```

---

## 9. 인증서 갱신 (수동)

Let's Encrypt 인증서는 90일마다 만료된다. 자동 갱신 크론이 설정되어 있지만, 수동으로 갱신할 때는:

```bash
# nginx 중단
docker stop alphadesk-nginx

# 갱신
sudo certbot renew

# nginx 재시작
docker start alphadesk-nginx
```

**현재 인증서 만료일**: 2026-07-08

---

## 10. 전체 재구축 순서 (처음부터 다시 할 때)

1. **EC2 생성** — t4g.small, Amazon Linux 2023 (arm64), 보안 그룹 80/443/22 오픈
2. **Docker 설치** — (섹션 2 참고)
3. **Docker 네트워크 생성** — `docker network create alphadesk-network`
4. **DuckDNS IP 등록** — 새 EC2 IP 입력 (섹션 3 참고)
5. **컨테이너 기동 순서**:
   1. `alphadesk-mysql`
   2. `alphadesk-redis`
   3. `pg-container`
   4. `alphadesk-api`
   5. `alphadesk-web` ← 이 컨테이너가 `alpha-terminal-frontend_multi-agent-net` 네트워크 생성
6. **certbot 인증서 발급** — (섹션 4 참고, nginx 실행 전에 진행)
7. **nginx 설정 파일 업로드**
   ```bash
   scp -i ~/dev/codelab/alpha-desk.pem \
     /Users/sulee/dev/codelab/nginx/default.conf \
     ec2-user@<IP>:/home/ec2-user/nginx/default.conf
   ```
8. **nginx 컨테이너 실행** — (섹션 5.1 참고)
9. **nginx를 두 번째 네트워크에 연결** — `docker network connect alpha-terminal-frontend_multi-agent-net alphadesk-nginx`
10. **자동 갱신 크론 설정** — (섹션 4.4 참고)
11. **GitHub Actions Runner 설치** — BE/FE 각각
12. **카카오 개발자 콘솔** Redirect URI 등록
13. **접속 확인** — `https://alpha-desk.duckdns.org`

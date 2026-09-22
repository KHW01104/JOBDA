# JOBDA

## 공고 수집 스케줄러

- 수동 실행: `docker compose --profile batch run --rm batch`
- Linux Cron 템플릿: `deploy/cron/jobda-collect`
- 실행 시각: Asia/Seoul 기준 매일 13:00, 18:00
- 서버에서 `/opt/jobda`를 실제 배포 경로로 바꾼 뒤 `crontab deploy/cron/jobda-collect`로 등록
- 수집 로그: `/var/log/jobda/collect.log`
- 네이버 메일 수집은 IMAP 활성화와 앱 비밀번호 설정 후 실행
- 사람인 알림 메일은 `NAVER_IMAP_ALLOWED_SENDERS=saramin.co.kr` 기본값으로 수집

## 운영 배포

- `.env.example`을 `.env`로 복사 후 운영 비밀값 설정
- `docker compose -f docker-compose.prod.yml up -d --build`로 운영 컨테이너 시작
- Nginx는 80 포트에서 정적 PWA와 `/api` 프록시 제공
- HTTPS는 Lightsail 도메인 연결 후 인증서 발급·443 포트 설정 필요
- PostgreSQL 백업: `POSTGRES_USER=jobda POSTGRES_DB=jobda sh deploy/backup-postgres.sh`
- 자동 백업은 서버 Cron에서 `deploy/backup-postgres.sh` 실행 권장

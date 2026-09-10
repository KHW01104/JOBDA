# JOBDA

## 공고 수집 스케줄러

- 수동 실행: `docker compose --profile batch run --rm batch`
- Linux Cron 템플릿: `deploy/cron/jobda-collect`
- 실행 시각: Asia/Seoul 기준 매일 13:00, 18:00
- 서버에서 `/opt/jobda`를 실제 배포 경로로 바꾼 뒤 `crontab deploy/cron/jobda-collect`로 등록
- 수집 로그: `/var/log/jobda/collect.log`
- Gmail 수집은 계정 연동 전까지 실행 대상에서 제외

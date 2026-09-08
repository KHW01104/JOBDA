from datetime import date
from math import ceil

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.models import User
from app.schemas.jobs import JobDetail, JobListItem, JobListResponse
from app.security.auth import get_current_user

router = APIRouter(prefix="/jobs", tags=["공고"])

_FIXTURE_JOBS = [
    JobDetail(id=1, company="JOBDA", title="백엔드 플랫폼 개발자", job_category="Backend", location="서울", experience="신입·2년 이하", employment_type="정규직", company_size="스타트업", deadline=date(2026, 10, 18), source="사람인", source_url="https://www.saramin.co.kr", status="OPEN", education="학력 무관", description="채용 데이터 플랫폼과 API를 개발합니다.", published_at=date(2026, 9, 5)),
    JobDetail(id=2, company="그린랩스", title="프론트엔드 엔지니어", job_category="Frontend", location="서울", experience="1·5년", employment_type="정규직", company_size="중견", deadline=date(2026, 9, 30), source="ALIO", source_url="https://job.alio.go.kr", status="OPEN", education="대졸 이상", description="사용자 중심의 채용 서비스를 개발합니다.", published_at=date(2026, 9, 4)),
    JobDetail(id=3, company="브릭메이트", title="데이터 엔지니어", job_category="Data", location="경기", experience="3·7년", employment_type="정규직", company_size="중소", deadline=date(2026, 10, 2), source="사람인", source_url="https://www.saramin.co.kr", status="OPEN", education="대졸 이상", description="대규모 데이터 파이프라인을 설계하고 운영합니다.", published_at=date(2026, 9, 3)),
    JobDetail(id=4, company="서울교통공사", title="IT 시스템 운영", job_category="DevOps", location="서울", experience="경력 무관", employment_type="정규직", company_size="공공기관", deadline=date(2026, 9, 24), source="ALIO", source_url="https://job.alio.go.kr", status="OPEN", education="학력 무관", description="공공 서비스 시스템 운영과 개선을 담당합니다.", published_at=date(2026, 9, 1)),
    JobDetail(id=5, company="모노랩", title="풀스택 웹 개발자", job_category="Fullstack", location="부산", experience="2·5년", employment_type="정규직", company_size="스타트업", deadline=date(2026, 10, 10), source="사람인", source_url="https://www.saramin.co.kr", status="OPEN", education="학력 무관", description="B2B 웹 제품의 전반적인 개발을 담당합니다.", published_at=date(2026, 8, 30)),
    JobDetail(id=6, company="한국콘텐츠진흥원", title="서비스 기획 및 개발", job_category="Product", location="전국", experience="경력 무관", employment_type="계약직", company_size="공공기관", deadline=date(2026, 9, 28), source="ALIO", source_url="https://job.alio.go.kr", status="OPEN", education="대졸 이상", description="콘텐츠 산업 지원 서비스의 기획과 개발을 담당합니다.", published_at=date(2026, 8, 28)),
]


@router.get("", response_model=JobListResponse)
def list_jobs(
    q: str | None = Query(default=None),
    sort: str = Query(default="latest"),
    job_category: str | None = Query(default=None),
    location: str | None = Query(default=None),
    experience: str | None = Query(default=None),
    employment_type: str | None = Query(default=None),
    company_size: str | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=6, ge=1, le=50),
    _current_user: User = Depends(get_current_user),
) -> JobListResponse:
    jobs = list(_FIXTURE_JOBS)
    if q:
        keyword = q.casefold()
        jobs = [job for job in jobs if keyword in f"{job.company} {job.title}".casefold()]
    for field, value in (("job_category", job_category), ("location", location), ("experience", experience), ("employment_type", employment_type), ("company_size", company_size)):
        if value:
            jobs = [job for job in jobs if getattr(job, field) == value]
    if sort == "deadline":
        jobs.sort(key=lambda job: job.deadline)
    else:
        jobs.sort(key=lambda job: job.published_at, reverse=True)
    total = len(jobs)
    start = (page - 1) * page_size
    return JobListResponse(items=jobs[start : start + page_size], total=total, page=page, page_size=page_size, total_pages=max(1, ceil(total / page_size)))


@router.get("/{job_id}", response_model=JobDetail)
def get_job(job_id: int, _current_user: User = Depends(get_current_user)) -> JobDetail:
    job = next((item for item in _FIXTURE_JOBS if item.id == job_id), None)
    if job is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="공고를 찾을 수 없습니다.")
    return job

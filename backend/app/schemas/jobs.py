from datetime import date

from pydantic import BaseModel


class JobListItem(BaseModel):
    id: int
    company: str
    title: str
    job_category: str
    location: str
    experience: str
    employment_type: str
    company_size: str
    deadline: date
    source: str
    source_url: str
    status: str


class JobListResponse(BaseModel):
    items: list[JobListItem]
    total: int
    page: int
    page_size: int
    total_pages: int


class JobDetail(JobListItem):
    education: str
    description: str
    published_at: date

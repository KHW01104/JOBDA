from pydantic import BaseModel, Field


class UserFilterBase(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    job_categories: list[str] = []
    experience_min: int | None = None
    experience_max: int | None = None
    locations: list[str] = []
    employment_types: list[str] = []
    company_sizes: list[str] = []
    minimum_employee_count: int | None = None
    included_keywords: list[str] = []
    excluded_keywords: list[str] = []
    is_active: bool = True


class UserFilterCreate(UserFilterBase):
    pass


class UserFilterResponse(UserFilterBase):
    id: int

    class Config:
        from_attributes = True


class CompanyWatchCreate(BaseModel):
    company_name: str = Field(min_length=1, max_length=200)
    company_id: int | None = None


class CompanyWatchResponse(CompanyWatchCreate):
    id: int

    class Config:
        from_attributes = True


class JobScrapCreate(BaseModel):
    job_id: int
    status: str = "SCRAPPED"
    memo: str | None = None


class JobScrapResponse(JobScrapCreate):
    id: int

    class Config:
        from_attributes = True

from pydantic import BaseModel, Field, model_validator


class UserFilterBase(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    job_categories: list[str] = []
    experience_min: int | None = Field(default=None, ge=0)
    experience_max: int | None = Field(default=None, ge=0)
    locations: list[str] = []
    employment_types: list[str] = []
    company_sizes: list[str] = []
    minimum_employee_count: int | None = Field(default=None, ge=1)
    included_keywords: list[str] = []
    excluded_keywords: list[str] = []
    is_active: bool = True

    @model_validator(mode="after")
    def validate_experience_range(self):
        if self.experience_min is not None and self.experience_max is not None and self.experience_min > self.experience_max:
            raise ValueError("최소 경력은 최대 경력보다 클 수 없습니다.")
        return self


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

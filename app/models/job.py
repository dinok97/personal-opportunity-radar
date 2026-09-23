from pydantic import BaseModel, Field, field_validator
from email.utils import parsedate_to_datetime
from typing import List, Optional, Literal
from datetime import datetime

class Job(BaseModel):
    source: str 
    external_id: str
    url: str = Field(description="URL of job to uniquely identify the job")
    title: str = Field(description="Job title")
    company: Optional[str] = None
    location: Optional[str] = None  
    posted_at: Optional[datetime] = None
    executive_summary: str
    role_type: Literal["Thesis", "Internship", "Part-time", "Full-time"] = "Full-time"
    is_active: bool = True
    is_deleted: bool = False


class JobExtraction(BaseModel):
    title: str
    company: Optional[str] = Field(description="Hiring company, e.g. 'Ericsson'. Always present in the posting.")
    location: Optional[str] = Field(description="City, Country, e.g. 'Stockholm, Sweden'. 'Not specified' only if truly absent.")
    role_type: Literal["Thesis", "Internship", "Part-time", "Full-time"] = "Full-time"
    is_accepting_applications: bool = True
    executive_summary: str = Field(
        description=(
            "3-5 sentences in English only. Start with the main responsibilities, then key "
            "required skills and education, then dates or duration if given. Do NOT mention "
            "title, company, location, role type or work model. If something is not in the "
            "posting, leave it out; never write 'not specified' or 'not stated'."
        )
    )


class JobSearch(BaseModel):
    external_id: str = Field(description="URL of job to uniquely identify the job")
    title: str = Field(description="Job title")
    url: str = Field(description="URL of the job")
    content: str = Field(description="Search result content returned by Tavily")
    raw_content: str = ""
    published_datetime: Optional[datetime] = Field(
        default=None, description="Datetime the job posting was published"
    )

    @field_validator("published_datetime", mode="before")
    @classmethod
    def parse_published_datetime(cls, value):
        if value is None or isinstance(value, datetime):
            return value

        if isinstance(value, str):
            try:
                return parsedate_to_datetime(value)
            except (TypeError, ValueError):
                return None

        return None


class JobSearchResponse(BaseModel):
    jobs: List[JobSearch] = []
    queries: List[str] = []
    total_results: int = 0
from pydantic import BaseModel, Field, field_validator
from email.utils import parsedate_to_datetime
from typing import List, Optional, Literal
from datetime import datetime

JOB_EMPLOYMENT_TYPES=Literal["Full-time", "Part-time", "Internship", "Thesis", "Contract"]

class Job(BaseModel):
    title: str
    company: str
    source: str 
    external_id: str
    url: str 
    posted_at: Optional[datetime] = None
    locations: str
    specialization: str
    employment_type: Optional[JOB_EMPLOYMENT_TYPES] = None
    skills: str

    executive_summary: str = ""
    embedding_text: str = ""

    is_active: bool = True
    is_deleted: bool = False


class JobExtraction(BaseModel):
    title: str
    company: str
    source: str
    is_closed: bool
    is_in_accepted_location: bool
    locations: List[str] = Field(
        description='Each location as "City, Country", one per item, e.g. "Stockholm, Sweden". Empty list if missing.'
    )
    employment_type: JOB_EMPLOYMENT_TYPES | None = None
    specialization: List[str] | None = Field(
        default=None,
        description="Up to 3 broad kinds of work, one per item, most relevant first.",
    )
    skills: List[str] | None = Field(
        default=None,
        description="Up to 10 core skills/tools, one per item, exact terms from the ad, most relevant first.",
    )
    role_overview: str | None = Field(
        default=None, 
        description="One sentence: the role at a glance."
    )
    work_overview: str | None = Field(
        default=None, 
        description="One sentence: the kind of work, industry and project."
    )
    daily_tasks: str | None = Field(
        default=None, 
        description="One sentence starting with 'You will'."
    )
    requirements: str | None = Field(
        default=None, 
        description="One sentence: skills, degrees, experience, languages."
    )
    practical_details: str | None = Field(
        default=None, 
        description="One sentence: salary, deadline, start date or duration."
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
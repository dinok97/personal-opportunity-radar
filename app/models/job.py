from pydantic import BaseModel, Field, field_validator
from email.utils import parsedate_to_datetime
from typing import List, Optional, Literal
from datetime import datetime

class Job(BaseModel):
    title: str
    company: str
    source: str 
    external_id: str
    url: str 
    posted_at: Optional[datetime] = None
    locations: str
    specialization: str
    work_mode: Literal["Remote", "Hybrid", "Onsite"]
    employment_type: Literal["Full-time", "Part-time", "Internship", "Thesis", "Contract"]
    seniority: Literal["Student", "Entry", "Mid", "Senior", "Lead", "Not specified"]
    skills: str
    industry_domain: str | None
    education: str | None 
    experience: str | None 

    executive_summary: str = ""
    embedding_text: str = ""

    is_active: bool = True
    is_deleted: bool = False


class JobExtraction(BaseModel):
    title: str
    company: str
    source: str
    specialization: str = Field(
        description='Up to 3 broad kinds of work, comma-separated, e.g. "Machine Learning, Computer Vision".'
    )
    locations: str = Field(
        description='Each as "City, Country", separated by "; ", e.g. "Stockholm, Sweden; Kraków, Poland". Empty string if missing.'
    )
    work_mode: Literal["Remote", "Hybrid", "Onsite"]
    employment_type: Literal["Full-time", "Part-time", "Internship", "Thesis", "Contract"]
    seniority: Literal["Student", "Entry", "Mid", "Senior", "Lead", "Not specified"]
    skills: str = Field(
        description="Up to 10 core skills/tools, exact terms from the ad."
    )
    responsibilities: str = Field(
        description="1 sentence: what the person will do."
    )
    industry_domain: str | None =  Field(
        default=None,
        description='Up to 2 industries the employer serves, e.g. "Telecommunications", "Healthcare". None if unclear.'
    )
    education: str | None  = Field(
        default=None,
        description='Accepted degrees, comma-separated, e.g. "Master\'s in Computer Science, Master\'s in Data Science".'
    )
    experience: str | None = Field(
        default=None,
        description='One short phrase, e.g. "5+ years in backend development".'
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
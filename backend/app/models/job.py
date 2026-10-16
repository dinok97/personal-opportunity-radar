from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel

EmploymentType = Literal[
    "PhD",
    "Full-time",
    "Part-time",
    "Internship",
    "Thesis",
    "Contract",
]

class Job(BaseModel):
    title: str
    company: str
    source: str 
    external_id: str
    url: str 
    posted_at: Optional[datetime] = None
    locations: str
    specialization: str
    employment_type: Optional[EmploymentType] = None
    skills: str
    application_deadline_at: datetime

    executive_summary: str = ""
    embedding_text: str = ""

    is_active: bool = True
    is_deleted: bool = False


class JobSearchResult(BaseModel):
    job: Job
    score: float

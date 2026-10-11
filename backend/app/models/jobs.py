from typing import Literal

from pydantic import BaseModel


EmploymentType = Literal["Full-time", "Part-time", "Internship", "Thesis", "Contract"]


class JobMatch(BaseModel):
    id: str
    title: str
    company: str
    location: str
    salary: str
    type: str
    matchScore: int
    description: str
    tags: list[str]
    reasons: list[str]
    missingSkills: list[str]
    source: str
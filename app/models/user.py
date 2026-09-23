from pydantic import BaseModel
from typing import List, Optional

class WorkExperience(BaseModel):
    role: str
    company: str
    years: float
    description: str
    key_work_skills: List[str]


class Project(BaseModel):
    name: str
    description: str
    tech_stack: List[str]


class UserProfile(BaseModel):
    user_id: int
    target_roles: List[str]
    skills: List[str]
    preferred_cities: List[str] = []
    additional_requirements: List[str] = []

    work_history: List[WorkExperience] = []
    projects: List[Project] = []
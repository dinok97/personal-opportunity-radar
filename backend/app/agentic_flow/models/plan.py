from pydantic import BaseModel
from typing import Literal

AGENT = Literal["job_advisor", "cv_advisor"]

class Plan(BaseModel):
    agent: AGENT
    task: str 

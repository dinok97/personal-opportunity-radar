from pydantic import BaseModel
from typing import Optional, Literal
from datetime import datetime

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))

from helpers.constants import EMP_TYPES

EmploymentType = Literal[*EMP_TYPES]

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

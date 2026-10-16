from pydantic import BaseModel
from typing import Optional

class JobAd(BaseModel):
    id: str
    title: str
    employer: str
    cities: list[str]
    application_deadline: Optional[str]
    publication_date: Optional[str]
    description: str
    url: str
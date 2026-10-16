from pydantic import BaseModel
from datetime import datetime

class SearchSchedule(BaseModel):
    searchschedules_id: int = 0
    last_ran_on: datetime
    total_found: int 
    total_unseen: int 
    total_saved: int 
    saved_job_ids: list[str]


class SearchScheduleRequest(BaseModel):
    date_windows: list[tuple] = []

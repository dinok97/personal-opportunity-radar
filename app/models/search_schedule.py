from pydantic import BaseModel
from datetime import datetime
from typing import List, Literal

class SearchSchedule(BaseModel):
    searchschedules_id: int = 0
    last_ran_on: datetime
    total_found: int 
    total_unseen: int 
    total_saved: int 
    saved_job_ids: List[str]


class SearchScheduleRequest(BaseModel):
    time_range: Literal["d", "w", "m", "y"] = "w"
    date_windows: List[tuple] = []

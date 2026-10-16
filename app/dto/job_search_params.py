from pydantic import BaseModel
from datetime import datetime


class QueryPlan(BaseModel):
    queries: list[str]
    emp_type: str

class JobSearchParams(BaseModel):
    query_plans: QueryPlan
    start_date: datetime
    end_date: datetime
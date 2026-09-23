from pydantic import BaseModel
from typing import List, Literal
from helpers.constants import (
    JOBSEARCH_DOMAINS, 
    JOBSEARCH_DEFAULT_LOCATION, 
    JOBSEARCH_MAX_RESULTS
)

class WebSearchParams(BaseModel):
    queries: List[str]
    search_domains: List[str] = JOBSEARCH_DOMAINS
    start_date: str = ""
    end_date: str = ""
    time_range: Literal["d", "w", "m", "y"] = "w"
    max_results: int = JOBSEARCH_MAX_RESULTS
    country: str = JOBSEARCH_DEFAULT_LOCATION
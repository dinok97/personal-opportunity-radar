from pydantic import BaseModel, Field
from typing import Optional, Literal

EmploymentType = Literal["PhD", "Full-time", "Part-time", "Internship", "Thesis", "Contract"]

class PostedFilter(BaseModel):
    after_days: Optional[int] = Field(description="Posted within the last N days. null if unused.")
    before_days: Optional[int] = Field(description="Posted N or more days ago. null if unused.")
    on_days: Optional[int] = Field(description="Posted exactly N days ago. null if unused.")

class DeadlineFilter(BaseModel):
    after_days: Optional[int] = Field(description="Deadline is N or more days away. null if unused.")
    before_days: Optional[int] = Field(description="Deadline is within N days. null if unused.")
    on_days: Optional[int] = Field(description="Deadline is exactly N days away. null if unused.")

class SearchPlan(BaseModel):
    """One independent job search."""
    query: str = Field(description="Everything that is not a company, location, employment type or date limit: "
                                    "job titles, fields of study, domains, skills, tools, seniority, language requirements. "
                                    "Remove filler words like 'jobs', 'positions', 'roles'. Use 'jobs' only if nothing is left."
                )   
    employment_types: list[EmploymentType] = Field(default_factory=list, description="Employment types for THIS search. [] if none.")
    locations: list[str] = Field(default_factory=list, description="Swedish cities for THIS search, Swedish spelling. [] if none.")
    posted: Optional[PostedFilter] = Field(default=None, description="null unless a posting date limit was mentioned.")
    deadline: Optional[DeadlineFilter] = Field(default=None, description="null unless a deadline limit was mentioned.")

class SearchPlans(BaseModel):
    """Split the user's request into 1-3 independent job searches."""
    reasoning: str = Field(
        default="",
        description="First list each distinct need and decide whether to split.",
    )
    searches: list[SearchPlan] = Field(
        description="1 to 3 searches, one per distinct need. Each search carries ONLY its own locations and types."
    )
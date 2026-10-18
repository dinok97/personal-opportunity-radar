from pydantic import BaseModel, Field
from typing import Optional

from ..models.plan import Plan

class SupervisorOutput(BaseModel):
    plans: list[Plan] = Field(default_factory=list, description="Ordered steps for the agents. Empty when you reply yourself.")
    direct_ans: Optional[str] = Field(None, description="Your own reply when plans is empty.")
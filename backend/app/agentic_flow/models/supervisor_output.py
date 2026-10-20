from pydantic import BaseModel, Field
from typing import Optional, Literal

from ..models.plan import Plan

class SupervisorOutput(BaseModel):
    topic: Literal["job", "cv", "job_and_cv", "greeting", "invalid", "other"] = Field(
        description=(
            "Decide this first. 'job': job search or a question about job postings. "
            "'cv': a question about the candidate's own CV. "
            "'job_and_cv': both, or comparing the CV with a job. "
            "'greeting': greeting, thanks or acknowledgement. "
            "'invalid': message is empty, random characters, or a fragment. "
            "'other': anything else."
        )
    )
    off_topic_part: bool = Field(
        default=False,
        description="True when the message also holds a request that is about neither jobs nor the CV.",
    )
    plans: list[Plan] = Field(default_factory=list, description="Ordered steps for the agents. Empty when you reply yourself.")
    direct_ans: Optional[str] = Field(None, description="Your own reply when plans is empty.")
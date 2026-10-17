from pydantic import BaseModel, Field

from ..models.plan import Plan

class SupervisorOutput(BaseModel):
    plans: list[Plan] = Field(description="Steps for the agents, in running order. Empty when the message needs no agent.")
    direct_ans: str = Field(description="Reply to the candidate when plans is empty (greetings, thanks, small talk, off-topic). Empty string when plans has steps.",)
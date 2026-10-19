from .models.plan import Plan
from ..models.job import JobSearchResult, Job

from langchain_core.messages import AnyMessage
from langgraph.graph.message import add_messages
from typing import TypedDict, Annotated


class FlowStep(TypedDict):
    messages: Annotated[list[AnyMessage], add_messages]
    plans: list[Plan]
    steps: list[Plan]
    route_summary: str
    results: list[dict]
    jobs: list[JobSearchResult]
    latest_searched_jobs: list[Job]
    direct_ans: str
    ans: str
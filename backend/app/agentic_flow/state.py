from .models.plan import Plan

from langchain_core.messages import AnyMessage
from langgraph.graph.message import add_messages
from typing import TypedDict, Annotated


class FlowStep(TypedDict):
    question: str
    messages: Annotated[list[AnyMessage], add_messages]
    plans: list[Plan]
    steps: list[Plan]
    route_summary: str
    results: list[dict]
    direct_ans: str
    ans: str
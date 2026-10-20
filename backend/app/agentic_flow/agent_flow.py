from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import END, START, StateGraph
from langchain_core.messages import HumanMessage

from .state import FlowStep
from .agents.supervisor import supervisor_node
from .agents.job_advisor import job_advisor_node
from .agents.cv_advisor import cv_advisor_node
from .agents.finish import finish_node
from .helpers.agent_constants import (
    SUPERVISOR,
    JOB_SEARCH_AGENT,
    CV_AGENT,
    FINISH,
)
from ..models.chat import ChatResponse
from .prompts import EMPTY_REQUEST_REPLY


def route(state: FlowStep) -> str:
    plans = state.get("plans") or []
    return plans[0].agent if plans else FINISH


def build_graph():
    g = StateGraph(FlowStep)
    g.add_node(SUPERVISOR, supervisor_node)
    g.add_node(JOB_SEARCH_AGENT, job_advisor_node)
    g.add_node(CV_AGENT, cv_advisor_node)
    g.add_node(FINISH, finish_node)

    targets = {JOB_SEARCH_AGENT: JOB_SEARCH_AGENT, CV_AGENT: CV_AGENT, FINISH: FINISH}

    g.add_edge(START, SUPERVISOR)
    g.add_conditional_edges(SUPERVISOR, route, targets)
    g.add_conditional_edges(JOB_SEARCH_AGENT, route, targets)
    g.add_conditional_edges(CV_AGENT, route, targets)
    g.add_edge(FINISH, END)

    return g.compile(checkpointer=InMemorySaver())


graph = build_graph()  


async def run_agent(question: str, thread_id: str) -> ChatResponse:
    if not question or not question.strip():
        return ChatResponse(
            thread_id=thread_id,
            message=EMPTY_REQUEST_REPLY,
            jobs=[],
            source="demo",
            plan_used="direct reply",
        )

    result = await graph.ainvoke(
        {"messages": [HumanMessage(content=question)]},
        {"configurable": {"thread_id": thread_id}}
    )

    return ChatResponse(
        thread_id=thread_id,
        message=result.get('ans', ''),
        jobs=result.get('jobs', []),
        source="demo",
        plan_used= result.get('route_summary', "")
    )



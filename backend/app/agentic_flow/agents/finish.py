from langchain_core.messages import HumanMessage, AIMessage

from ..state import FlowStep
from ..prompts import FALLBACK_ANSWER
from ..helpers.agent_constants import SUPERVISOR


def finish_node(state: FlowStep):
    if state.get("direct_ans"):
        final = state["direct_ans"]
    else:
        parts = [r["output"].strip() for r in state.get("results", []) if (r.get("output") or "").strip()]
        final = "\n\n".join(parts) or FALLBACK_ANSWER

    route_summary = ""
    steps_list = state.get("steps", [])

    if steps_list:
        route_summary += " -> ".join([SUPERVISOR] + [step.agent for step in steps_list if step])
    else:
        route_summary = f"{SUPERVISOR} -> direct reply"

    return {
        "ans": final,
        "messages": [AIMessage(content=final)],
        "steps": [],
        "route_summary": route_summary
    }
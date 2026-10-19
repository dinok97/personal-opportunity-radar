from langchain_core.messages import HumanMessage, AIMessage, SystemMessage

from ..state import FlowStep
from ..prompts import EMPTY_REPLY, FINAL_PROMPT
from ..helpers.agent_constants import SUPERVISOR
from ..generation.llm_service import get_groq
from ..helpers.agent_util import clean_text

FINAL_NODE_TEMP = 0.1
FINAL_NODE_MAX_TOKENS = 900
FINAL_NODE_LLM="openai/gpt-oss-20b"
FINAL_NODE_REASONING="low"

llm = get_groq(temp=FINAL_NODE_TEMP, max_tokens=FINAL_NODE_MAX_TOKENS, model=FINAL_NODE_LLM, reasoning_effort=FINAL_NODE_REASONING)


def finish_node(state: FlowStep) -> dict:
    results = state.get("results", [])
    reply = (state.get("direct_ans") or "").strip()

    if not reply:
        outputs = [r["output"] for r in results]
        if len(outputs) <= 1:
            reply = "\n".join(outputs)
        else:
            try:
                body = "\n\n".join(f"[{r['agent']}] {r['output']}" for r in results)
                msg = llm.invoke([SystemMessage(content=FINAL_PROMPT),
                                  HumanMessage(content=f"Question: {state['messages'][-1]}\n\nResults:\n{body}")])
                reply = clean_text(msg.content)
            except Exception:
                print("Final answer failed")
                reply = "\n\n".join(outputs)

    reply = reply or EMPTY_REPLY

    route_summary = ""
    steps_list = state.get("steps", [])

    if steps_list:
        route_summary += " -> ".join([SUPERVISOR] + [step.agent for step in steps_list if step])
    else:
        route_summary = f"{SUPERVISOR} -> direct reply"

    return {
            "ans": reply,
            "messages": [AIMessage(content=reply)],
            "steps": [],
            "route_summary": route_summary
        }

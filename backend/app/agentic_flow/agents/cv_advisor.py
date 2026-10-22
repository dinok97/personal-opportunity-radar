from langchain_core.messages import HumanMessage
from langchain.agents import create_agent
from langgraph.errors import GraphRecursionError

from ..state import FlowStep
from ..generation.llm_service import get_groq
from ..helpers.agent_util import get_last_ai_text, task_with_context, called_a_tool
from ..tools import get_user_profile
from ..prompts import (
    CV_ADVISOR_PROMPT,
    ONE_JOB_REPLY
)

CV_ADVISOR_TEMP = 0.1
CV_ADVISOR_MAX_TOKENS = 800
FORCE_TOOL_CALL_CONTEXT = "Call get_user_profile first, then answer."


llm = get_groq(temp=CV_ADVISOR_TEMP, max_tokens=CV_ADVISOR_MAX_TOKENS)

advisor_prompt = CV_ADVISOR_PROMPT.format(
    ONE_JOB_REPLY=ONE_JOB_REPLY
)

cv_advisor_agent = create_agent(
    model=llm,
    tools=[get_user_profile],
    system_prompt=advisor_prompt
)

def cv_advisor_node(state: FlowStep) -> dict:
    step, *rest = state["plans"]

    content = task_with_context(step, state)

    try:
        out = cv_advisor_agent.invoke(
            {"messages": [HumanMessage(content=content)]},
        )

        if not called_a_tool(out):
                out = cv_advisor_agent.invoke({"messages": [HumanMessage(
                    content=f"{content}\n\n{FORCE_TOOL_CALL_CONTEXT}"
                )]})

        output = get_last_ai_text(out["messages"]) or "The CV advisor did not produce an answer."
    except GraphRecursionError:
        output = "The CV analysis took too many steps. Try a narrower question."
    except Exception:
        output = "The CV analysis could not be completed."


    return {"results": [*state.get("results", []), {"agent": step.agent, "task": step.task, "output": output}],
            "plans": rest} 
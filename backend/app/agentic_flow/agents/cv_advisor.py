from langchain_core.messages import HumanMessage, SystemMessage
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

CV_ADVISOR_TEMP = 0.2
CV_ADVISOR_MAX_TOKENS = 800
FORCE_TOOL_CALL_CONTEXT = "Call get_user_profile first, then answer."
CV_QUERY_FULL = "skills, experience, education and projects"
MAX_TOOL_RETRIES = 2


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
        out = cv_advisor_agent.invoke({"messages": [HumanMessage(content=content)]})

        retries = 0
        
        while not called_a_tool(out) and retries < MAX_TOOL_RETRIES:
            retries += 1
            
            print(f"cv advisor skipped the tool, retry {retries}/{MAX_TOOL_RETRIES}")

            out = cv_advisor_agent.invoke({"messages": [HumanMessage(
                content=f"{content}\n\n{FORCE_TOOL_CALL_CONTEXT}"
            )]})

        if called_a_tool(out):
            output = get_last_ai_text(out["messages"]) or "The CV analysis did not produce an answer."
        else:
            output = "The CV analysis could not be completed."
    except GraphRecursionError:
        output = "The CV analysis took too many steps. Try a narrower question."
    except Exception as e:
        print(f"cv advisor failed for task {step.task!r}: {e!r}")
        output = "The CV analysis could not be completed."


    return {"results": [*state.get("results", []), {"agent": step.agent, "task": step.task, "output": output}],
            "plans": rest} 
from langchain_core.messages import HumanMessage
from langchain.agents import create_agent
from langgraph.errors import GraphRecursionError

from ..state import FlowStep
from ..generation.llm_service import get_groq
from ..helpers.agent_util import get_last_ai_text
from ..prompts import JOB_ADVISOR_PROMPT
from ..tools import get_job_details, search_jobs


JOB_ADVISOR_TEMP = 0.1
JOB_ADVISOR_MAX_TOKENS = 800
JOB_ADVISOR_RECURSION_LIMIT = 5


llm = get_groq(temp=JOB_ADVISOR_TEMP, max_tokens=JOB_ADVISOR_MAX_TOKENS)

job_advisor_agent = create_agent(
    model=llm,
    tools=[search_jobs, get_job_details],
    system_prompt=JOB_ADVISOR_PROMPT
)

def job_advisor_node(state: FlowStep) -> dict:
    step, *rest = state["plans"]

    try:
        out = job_advisor_agent.invoke(
            {"messages": [HumanMessage(content=step.task)]},
            {"recursion_limit": JOB_ADVISOR_RECURSION_LIMIT},
        )
        output = get_last_ai_text(out["messages"]) or "The job search did not produce an answer."
    except GraphRecursionError:
            output = "The job analysis took too many steps. Try a narrower question."
    except Exception:
        output = "The job search could not be completed."


    return {"results": [*state.get("results", []), {"agent": step.agent, "task": step.task, "output": output}],
            "plans": rest} 
from langchain_core.messages import HumanMessage
from langchain.agents import create_agent
from langgraph.errors import GraphRecursionError

from ..state import FlowStep
from ..generation.llm_service import get_groq
from ..helpers.agent_util import get_last_ai_text
from ..prompts import JOB_ADVISOR_PROMPT
from ..tools import get_job_details, search_jobs
from ...models.job import JobSearchResult


JOB_ADVISOR_TEMP = 0
JOB_ADVISOR_MAX_TOKENS = 800


llm = get_groq(temp=JOB_ADVISOR_TEMP, max_tokens=JOB_ADVISOR_MAX_TOKENS)

job_advisor_agent = create_agent(
    model=llm,
    tools=[search_jobs, get_job_details],
    system_prompt=JOB_ADVISOR_PROMPT
)

def job_advisor_node(state: FlowStep) -> dict:
    step, *rest = state["plans"]
    new_jobs: list[JobSearchResult] = []  

    try:
        out = job_advisor_agent.invoke(
            {"messages": [HumanMessage(content=step.task)]}
        )
    except GraphRecursionError:
            output = "The job analysis took too many steps. Try a narrower question."
    except Exception:
        print("agent run failed for task: %s", step.task) 
        out, output = None, "The job search could not be completed."


    if out is not None:
        try:
            new_jobs = collect_jobs(out["messages"])
        except Exception:
            print("collect_jobs failed")
        
        output = get_last_ai_text(out["messages"]) or "The job search did not produce an answer."

    return {"results": [*state.get("results", []), {"agent": step.agent, "task": step.task, "output": output}],
            "plans": rest,
            "jobs": [*state.get("jobs", []), *new_jobs]} 



def collect_jobs(messages: list) -> list[JobSearchResult]:
    cards: list[JobSearchResult] = []
    for m in messages:
        if m.type == "tool" and getattr(m, "name", "") == "search_jobs" and getattr(m, "artifact", None):
            for c in m.artifact:
                cards.append(c)
                    
    return cards
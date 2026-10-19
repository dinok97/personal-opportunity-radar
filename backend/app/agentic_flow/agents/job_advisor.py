from langchain_core.messages import HumanMessage
from langchain.agents import create_agent
from langgraph.errors import GraphRecursionError

from ..state import FlowStep
from ..generation.llm_service import get_groq
from ..helpers.agent_util import get_last_ai_text
from ..prompts import JOB_ADVISOR_PROMPT
from ..tools import get_job_details, search_jobs
from ...models.job import JobSearchResult


JOB_ADVISOR_TEMP = 0.1
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
    new_job_ids: list[str] | None = None
    out = None

    content = step.task

    try:
        out = job_advisor_agent.invoke(
            {"messages": [HumanMessage(content=content)]}
        )
    except GraphRecursionError:
            output = "The job analysis took too many steps. Try a narrower question."
    except Exception:
        print("agent run failed for task: %s", step.task) 
        out, output = None, "The job search could not be completed."

    if out is not None:
        try:
            new_jobs, new_job_ids = collect_jobs(out["messages"])
        except Exception:
            print("collect_jobs failed")

        if not new_job_ids or len(new_job_ids) == 0:
            for m in out["messages"]:
                print ("msg type=%s name=%s artifact=%s", m.type, getattr(m, "name", None),
                        type(getattr(m, "artifact", None)).__name__)
            
        output = get_last_ai_text(out["messages"]) or "The job search did not produce an answer."

    update = {}
    if new_job_ids is not None:
        old = state.get("latest_searched_job_ids", []) if state.get("jobs") else []
        update["latest_searched_job_ids"] = old + new_job_ids

    return {"results": [*state.get("results", []), {"agent": step.agent, "task": step.task, "output": output}],
            "plans": rest,
            "jobs": [*state.get("jobs", []), *new_jobs],
            **update} 



def collect_jobs(messages: list) -> tuple[list[JobSearchResult], list[str] | None]:
    """Returns (cards, ids). ids is None when no useful tool call happened, so the list stays unchanged."""
    cards: list[JobSearchResult] = []
    job_ids: list[str] | None = None
    for m in messages:
        if m.type != "tool":
            continue
        name = getattr(m, "name", "")
        artifact = getattr(m, "artifact", None)
        if name == "search_jobs":
            job_ids = job_ids or []                  
            for c in artifact or []:
                cards.append(c)
                job_ids.append(str(c.job.external_id))
        elif name == "get_job_details" and artifact:    
            job_ids = (job_ids or []) + [str(artifact)]
    return cards, job_ids
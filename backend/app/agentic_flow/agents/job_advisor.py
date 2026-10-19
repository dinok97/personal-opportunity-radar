from langchain_core.messages import HumanMessage
from langchain.agents import create_agent
from langgraph.errors import GraphRecursionError

from ..state import FlowStep
from ..generation.llm_service import get_groq
from ..helpers.agent_util import get_last_ai_text
from ..prompts import JOB_ADVISOR_PROMPT
from ..tools import get_job_details, search_jobs
from ...models.job import JobSearchResult, Job


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


    new_jobs_search = []
    update_cache = False
    old_jobs = state.get("latest_searched_jobs", [])


    if out is not None:
        collected = True

        try:
            new_jobs_search = collect_jobs(out["messages"])
        except Exception:
            print("collect_jobs failed")
            collected = False

        searched = any(
            m.type == "tool" and getattr(m, "name", "") == "search_jobs"
            for m in out["messages"]
        )

        if searched and collected:
            first_search_this_turn = not state.get("jobs")
            base = [] if first_search_this_turn else old_jobs
            known = {job.external_id for job in base}
            old_jobs = base + [card.job for card in new_jobs_search if card.job.external_id not in known]
            update_cache = True
        
    output = get_last_ai_text(out["messages"]) or "The job search did not produce an answer."
    

    update = {
        "results": [*state.get("results", []), {"agent": step.agent, "task": step.task, "output": output}],
        "plans": rest,
        "jobs": [*state.get("jobs", []), *new_jobs_search],
    }

    if update_cache:
        update["latest_searched_jobs"] = old_jobs

    return update

def collect_jobs(messages: list) -> list[JobSearchResult]:
    cards: list[JobSearchResult] = []
    for message in messages:
        if message.type != "tool" or getattr(message, "name", "") != "search_jobs":
            continue
        if getattr(message, "status", "success") == "error":
            continue
        cards.extend(getattr(message, "artifact", None) or [])
    return cards

# def collect_jobs(messages: list) -> list[JobSearchResult] | None:
#     """Returns (cards, ids). ids is None when no useful tool call happened, so the list stays unchanged."""
#     cards: list[JobSearchResult] = []
#     print(messages)
#     for m in messages:
#         if m.type != "tool":
#             continue
#         name = getattr(m, "name", "")
#         artifact = getattr(m, "artifact", None)
#         is_invalid = getattr(m, "invalid_tool_calls", None)
#         if name == "search_jobs" and not is_invalid:
#             job_ids = job_ids or []                  
#             for c in artifact or []:
#                 cards.append(c)

#     return cards
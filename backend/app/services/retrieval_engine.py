from ..helpers.retriever_utils import get_decomposition_prompt
from .llm_service import get_groq
from ..models.search_plan import SearchPlans, SearchPlan  
from ..models.job import Job
from ..services.job_service import get_job_service, JobSearchResult

from typing import Any

MAX_SEARCHES = 3
MIN_RERANK_SCORE = -2.0 

def get_job_search_plan(request: str, retry_attempts: int = 2) -> list[SearchPlan]:
    fallback = [SearchPlan(query=request)]
    structured_llm = get_groq(temp=0).with_structured_output(SearchPlans, method="function_calling")
    prompt_value = get_decomposition_prompt(request)

    plans = None

    for _ in range(1, retry_attempts + 1):
        try:
            plans = structured_llm.invoke(prompt_value)
            if plans and plans.searches:
                break
        except Exception as e:
            print("decomposition attempt failed")
            continue

    searches = [s for s in (plans.searches if plans else []) if (s.query or "").strip()]
    if searches:
        return searches[:MAX_SEARCHES]

    return fallback


def retrieve_jobs(request: str, top_n_limit=10) -> list[JobSearchResult]:
    plans = get_job_search_plan(request=request)

    print(f"Query plans: {plans}")

    all_jobs: dict[Any, JobSearchResult] = {}

    for plan in plans:
        posted = plan.posted
        deadline = plan.deadline

        searched_jobs: list[JobSearchResult] = get_job_service().search_jobs(
            query=plan.query,
            employment_types=plan.employment_types,
            locations=plan.locations,
            posted_before_days=posted.before_days if posted else None,
            posted_after_days=posted.after_days if posted else None,
            posted_on_days=posted.on_days if posted else None,
            deadline_before_days=deadline.before_days if deadline else None,
            deadline_after_days=deadline.after_days if deadline else None,
            deadline_on_days=deadline.on_days if deadline else None,
        )

        for j in searched_jobs:
            key = j.job.external_id
            if key not in all_jobs:     
                all_jobs[key] = j

    found_jobs = get_job_service().rerank_jobs(query=request, jobs=list(all_jobs.values()), top_k=top_n_limit)

    jobs_cutoff = [jb for jb in found_jobs if jb.score >= MIN_RERANK_SCORE]

    return jobs_cutoff[:top_n_limit]
from langchain_core.tools import tool
from typing import Any, Optional, Literal

from ..services.job_service import get_job_service
from ..models.job import JobSearchResult, Job
from ..services.cv_vector_service import CvVectorService
from ..config import get_settings
from .helpers.agent_util import deadline_text
from .helpers.agent_constants import MAX_JOB_IDS_HANDLE
from ..services.retrieval_engine import retrieve_jobs


EmploymentType = Literal["Thesis", "PhD", "Full-time", "Part-time", "Internship", "Contract"]
TOP_N_LIMIT=6

@tool(response_format="content_and_artifact", parse_docstring=True)
def search_jobs(request: str, top_n: int = TOP_N_LIMIT) -> tuple[str, list[JobSearchResult]]:
    """Search the job database for job postings matching the user's request.
    Use this only when the user wants to find or browse jobs.

    Args:
        request: The user's job search request, passed through unchanged.
        top_n: How many jobs to return. Set this only if the user asked for a
            specific number, e.g. "top 5" -> 5. Otherwise leave it empty.
    """

    results: list[JobSearchResult] = []
    summaries = []

    capped = top_n is not None and top_n > TOP_N_LIMIT
    top_n = max(1, min(top_n or TOP_N_LIMIT, TOP_N_LIMIT))

    try:
        results = retrieve_jobs(request=request, top_n_limit=top_n)
        summaries.append(f"Total {len(results)} jobs found" if len(results) > 0 else f"Query '{request}': no matching jobs found")
    except Exception as e:
        print(f"Job search failed: {e}")
        return "Job search failed due to an internal error. Tell the user to try again.", []

    if not results:
        return f"No matching jobs found for '{request}'. Suggest broadening the search.", []

    lines = [f"{i}. [id: {j.job.external_id}] {j.job.title} | {j.job.company} | {j.job.locations}"
             for i, j in enumerate(results, 1)]

    note = f" (the user asked for more, but at most {TOP_N_LIMIT} can be shown)" if capped else ""
    
    return f"Found {len(results)} jobs{note}:\n" + "\n".join(lines), results
    


# @tool(response_format="content_and_artifact")
# def search_jobs(queries: list[str],
#                 employment_types: Optional[list[EmploymentType]] = None,
#                 locations: Optional[list[str]] = None,
#                 posted_before_days: Optional[int] = None,
#                 posted_after_days: Optional[int] = None,
#                 posted_on_days: Optional[int] = None,
#                 deadline_before_days: Optional[int] = None,
#                 deadline_after_days: Optional[int] = None,
#                 deadline_on_days: Optional[int] = None,) -> tuple[str, list[JobSearchResult]]:
#     """Search stored job postings. Pass ALL searches in ONE call, as a list with one short
#     plain-language query per separate need (a different city, employment type, company or
#     field), for example ["Thesis computer vision Linköping", "Internship data engineering Gothenburg"].
#     Don't send several rewordings of the same need.
#     Filters are optional and apply to ALL queries in the call, so set one only when it is the same
#     for every query. When the needs differ (different cities or types), leave the filter empty and
#     keep the place and type in each query.
#     employment_types: set only when the task names a type (Thesis, PhD, Full-time, Internship, Contract, Part-time).
#     locations: city or municipality names the task names, in their Swedish spelling (Göteborg, not Gothenburg), e.g. ["Stockholm"]. Not regions.
#     Date limits are optional whole numbers of days (0 or more). Leave them empty when the task gives no date limit.
#     Posting date, counted in days ago: posted_on_days = posted exactly N days ago;
#     posted_after_days = posted in the last N days; posted_before_days = posted N or more days ago.
#     Application deadline, counted in days from today: deadline_on_days = deadline exactly N days from today;
#     deadline_after_days = deadline N or more days from today (0 = still open);
#     deadline_before_days = deadline within N days from today or earlier.
#     Set an after and a before value together for 'between'.
#     The matching jobs are shown to the user automatically as cards; you only get a short
#     summary, so don't list jobs in your reply."""

#     print("From search_jobs tool:\n\n")

#     cards: dict[Any, JobSearchResult] = {}
#     summaries = []

#     try:
#         for q in queries:
#             jobs: list[JobSearchResult] = get_job_service().search_jobs(
#                 q,
#                 employment_types=employment_types,
#                 locations=locations,
#                 posted_before_days=posted_before_days,
#                 posted_after_days=posted_after_days,
#                 posted_on_days=posted_on_days,
#                 deadline_before_days=deadline_before_days,
#                 deadline_after_days=deadline_after_days,
#                 deadline_on_days=deadline_on_days,
#             )
#             for j in jobs:
#                 cards[j.job.external_id] = j

#         summaries.append(f"Total {len(jobs)} jobs found" if len(cards) > 0 else f"Query '{q}': no matching jobs found")
#     except Exception:
#         print("search_jobs failed for queries: %s", queries)
#         return "Search failed.", []

#     return "\n".join(summaries), list(cards.values())


@tool
def get_job_details(job_ids: list[str]) -> str:
    """Read job postings by id. One id returns the full posting. Several ids return one short line per job
    (title, company, location, type, posted date, deadline). Call it once with all ids of the task."""

    ids = list(dict.fromkeys(str(i).strip() for i in job_ids if str(i).strip()))[:MAX_JOB_IDS_HANDLE]
    if not ids:
        return "No information is available for that job."

    blocks = []
    for job_id in ids:
        try:
            job = get_job_service().get_job(job_id)
        except Exception:
            print("get_job_details failed for id %s", job_id)
            blocks.append("The job could not be looked up.")
            continue
        if not job:
            blocks.append("No information is available for that job.")
            continue

        posted = job.posted_at.date().isoformat() if job.posted_at else "not given"
        deadline = deadline_text(job.application_deadline_at)

        if len(ids) == 1:
            description = (job.executive_summary or "").strip()[:2500]
            blocks.append(
                f"{job.title} | {job.company} | {job.locations} | {job.employment_type} | {job.url}\n"
                f"Specialization: {job.specialization}\n"
                f"Skills: {job.skills}\n"
                f"Posted: {posted}\n"
                f"Application deadline: {deadline}\n"
                f"Description: {description}"
            )
        else:
            blocks.append(
                f"{job.title} | {job.company} | {job.locations} | {job.employment_type} | "
                f"Locations: {job.locations} |"
                f"Posted: {posted} | Application deadline: {deadline}"
            )
    return "\n\n".join(blocks)


@tool
def get_user_profile(query: str) -> str:
    """Read the candidate's stored CV and profile. Input: what to look for in the CV, in plain words,
    e.g. 'skills and experience', 'projects with LLMs', 'education'. Returns the matching parts of the CV."""

    print("From get_user_profile tool:\n\n")

    try:
        documents = CvVectorService(get_settings()).search(query=query, k=5)
    except Exception:
        print("get_user_profile failed for query: %s", query)

    if not documents:
        return "No CV has been uploaded yet."

    parts = [d.page_content.strip() for d in documents if d.page_content and d.page_content.strip()]
    
    return "\n\n".join(parts)[:5000]
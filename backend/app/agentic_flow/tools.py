from langchain_core.tools import tool
from typing import Any, Optional

from ..services.job_service import get_job_service
from ..models.job import JobSearchResult, Job
from ..services.cv_vector_service import CvVectorService
from ..config import get_settings
from .helpers.agent_util import deadline_text


@tool(response_format="content_and_artifact")
def search_jobs(queries: list[str],
                posted_before_days: Optional[int] = None,
                posted_after_days: Optional[int] = None,
                posted_on_days: Optional[int] = None,
                deadline_before_days: Optional[int] = None,
                deadline_after_days: Optional[int] = None,
                deadline_on_days: Optional[int] = None,) -> tuple[str, list[JobSearchResult]]:
    """Search stored job postings. Pass ALL searches in ONE call, as a list with one short
    plain-language query per separate need (a different city, employment type, company or
    field), for example ["Thesis computer vision Linköping", "Internship data engineering Gothenburg"].
    Don't send several rewordings of the same need.
    Date limits are optional whole numbers of days (0 or more). Leave them empty when the task gives no date limit.
    Posting date, counted in days ago: posted_on_days = posted exactly N days ago;
    posted_after_days = posted in the last N days; posted_before_days = posted N or more days ago.
    Application deadline, counted in days from today: deadline_on_days = deadline exactly N days from today;
    deadline_after_days = deadline N or more days from today (0 = still open);
    deadline_before_days = deadline within N days from today or earlier.
    Set an after and a before value together for 'between'.
    The matching jobs are shown to the user automatically as cards; you only get a short
    summary, so don't list jobs in your reply."""

    limits = {
        "posted on": posted_on_days, "posted after": posted_after_days, "posted before": posted_before_days,
        "deadline on": deadline_on_days, "deadline after": deadline_after_days, "deadline before": deadline_before_days,
    }
    limits_text = ", ".join(f"{name} {n} days" for name, n in limits.items() if n is not None)

    print("From tool:-----\n\n")

    cards: dict[Any, JobSearchResult] = {}
    summaries = []

    try:
        for q in queries:
            jobs: list[JobSearchResult] = get_job_service().search_jobs(
                q,
                posted_before_days=posted_before_days,
                posted_after_days=posted_after_days,
                posted_on_days=posted_on_days,
                deadline_before_days=deadline_before_days,
                deadline_after_days=deadline_after_days,
                deadline_on_days=deadline_on_days,
            )
            for j in jobs:
                cards[j.job.external_id] = j

        summaries.append(f"Total {len(jobs)} jobs found" if len(cards) > 0 else f"Query '{q}': no matching jobs found")
    except Exception:
        print("search_jobs failed for queries: %s", queries)
        return "Search failed.", []

    print("From tool:-----\n\n", len(cards))

    if limits_text:
        summaries.append(f"Date limits applied: {limits_text}.")

    return "\n".join(summaries), list(cards.values())


@tool
def get_job_details(job_id: str) -> str:
    """Read the details of one job posting: title, company, location, type, skills and description.
    Input: the job id, a number given in the task or in the earlier results."""

    try:
        job = get_job_service().get_job(job_id)
    except Exception:
        print("get_job_details failed for id %s", job_id)
        return "The job could not be loaded."
    if not job:
        return "Job not found."

    description = (job.executive_summary or "").strip()[:2500]
    return (
        f"{job.title} | {job.company} | {job.locations} | {job.employment_type} | {job.url}\n"
        f"Specialization: {job.specialization}\n"
        f"Skills: {job.skills}\n"
        f"Application deadline: {deadline_text(job.application_deadline_at)}\n"
        f"Description: {description}"
    )


@tool
def get_user_profile(query: str) -> str:
    """Read the candidate's stored CV and profile. Input: what to look for in the CV, in plain words,
    e.g. 'skills and experience', 'projects with LLMs', 'education'. Returns the matching parts of the CV."""

    try:
        documents = CvVectorService(get_settings()).search(query=query, k=5)
    except Exception:
        print("get_user_profile failed for query: %s", query)

    if not documents:
        return "No CV has been uploaded yet."

    parts = [d.page_content.strip() for d in documents if d.page_content and d.page_content.strip()]
    
    return "\n\n".join(parts)[:5000]
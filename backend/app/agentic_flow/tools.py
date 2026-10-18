from langchain_core.tools import tool
from typing import Any

from ..services.job_service import get_job_service
from ..models.job import JobSearchResult
from ..services.cv_vector_service import CvVectorService
from ..config import get_settings


@tool(response_format="content_and_artifact")
def search_jobs(queries: list[str]) -> tuple[str, list[JobSearchResult]]:
    """Search stored job postings. Pass ALL searches in ONE call, as a list with one short
    plain-language query per separate need (a different city, employment type, company or
    field), for example ["Thesis computer vision Linköping", "Internship data engineering Gothenburg"].
    Don't send several rewordings of the same need.
    The matching jobs are shown to the user automatically as cards; you only get a short
    summary, so don't list jobs in your reply."""

    cards: dict[Any, JobSearchResult] = {}
    summaries = []

    try:
        for q in queries:
            jobs: list[JobSearchResult] = get_job_service().search_jobs(q)
            for j in jobs:
                cards[j.job.external_id] = j
            
            summaries.append(f"Query '{q}': {len(jobs)} jobs found" if len(jobs) > 0 else "No matching jobs found.") 
    except Exception as e:
        return f"Search failed: {e}", []
    
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
        f"[{job.external_id}] {job.title} | {job.company} | {job.locations} | {job.employment_type} | {job.url}\n"
        f"Specialization: {job.specialization}\n"
        f"Skills: {job.skills}\n"
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



#TODO: Search job by title
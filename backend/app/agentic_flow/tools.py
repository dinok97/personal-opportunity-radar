from langchain_core.tools import tool

@tool
def search_jobs(queries: list[str]) -> str:
    """Search stored job postings. Pass ALL searches in ONE call, as a list with one short plain-language
    query per separate need (a different city, employment type, company or field), for example
    ["Thesis computer vision Linköping", "Internship data engineering Gothenburg"].
    Returns the jobs for each query, one job per line with its id."""

    return f"from serach job"


@tool
def get_job_details(job_id: int) -> str:
    """Read the requirements of one job. Input: the id in square brackets from search_jobs."""
    return f"Job details"


@tool
def get_user_profile() -> str:
    """Read the candidate's stored profile: target roles, skills and background."""
    return "Get user profile"


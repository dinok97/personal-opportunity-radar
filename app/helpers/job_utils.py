import sys 
from pathlib import Path

from typing import List, Optional
from models.job import Job, JobExtraction, JobSearch

sys.path.append(str(Path(__file__).resolve().parent))

from helpers.constants import JOBSEARCH_DEFAULT_LOCATION, JOBSEARCH_SITE_REF

def build_search_queries(target_roles: List[str],
                         cities: Optional[List[str]] = None,
                         country: str = JOBSEARCH_DEFAULT_LOCATION) -> List[str]:

    if not target_roles:
        return []

    generated_queries = []

    target_locations = [f'{city} {country}'.strip() for city in cities] if cities else [country]

    for role in target_roles:
        for location in target_locations:
            query_text = f'"{role}" {location}'.strip()
            query_text = " ".join(query_text.split())
            
            generated_queries.append(query_text)

    unique_queries = list(dict.fromkeys(generated_queries))

    return unique_queries


def add_site_refs_to_queries(queries: List[str], domains: List[str]) -> List[str]:
    sited_queries = []

    for domain in domains:
        ref_site = JOBSEARCH_SITE_REF.get(domain, "")

        if ref_site:
            core_queries =  [f"{ref_site} {query}" for query in queries]

            sited_queries.extend(core_queries)

    unique_queries = list(dict.fromkeys(sited_queries))

    return unique_queries

def isknown(value):
    return value if value and value != "Not specified" else None

def build_embedding_text(job: Job) -> str:
    lines = [
        f"Title: {job.title}",
        f"Company: {job.company}",
        f"Specialization: {job.specialization}" if isknown(job.specialization) else None,
        f"Employment Type: {job.employment_type}" if isknown(job.employment_type) else None,
        f"Locations: {job.locations}" if isknown(job.locations) else None,
        f"Required Skills: {job.skills}" if isknown(job.skills) else None,
        f"Summary: {job.executive_summary}" if isknown(job.executive_summary) else None,
    ]

    return "\n".join(line for line in lines if line)


def to_job(extracted: JobExtraction, job_res: JobSearch) -> Job:

    parts = [extracted.role_overview, extracted.work_overview, extracted.daily_tasks,
             extracted.requirements, extracted.practical_details]
    
    executive_summary = " ".join(p.strip() for p in parts if p)

    job = Job(
        title=extracted.title,
        company=extracted.company,
        source=extracted.source,
        external_id=job_res.external_id,
        url=job_res.url,
        posted_at=job_res.published_datetime,
        locations=extracted.locations,
        specialization=extracted.specialization,
        employment_type=extracted.employment_type,
        skills=extracted.skills,
        executive_summary=executive_summary
    )

    job.embedding_text = build_embedding_text(job)

    return job
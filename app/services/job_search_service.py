from dotenv import load_dotenv
from typing import List, Dict, Any
import sys 
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))

from helpers.constants import (
    JOBSEARCH_RELEVANCE_SCORE_CUTOFF,
    JOBSEARCH_DOMAINS
)
from models.job import JobSearch, JobSearchResponse
from helpers.utils import normalize_url,get_hashed_id, get_datetime_utc
from services.websearch_service import get_websearch_result, get_websearch_by_date_result
from services.job_source_factory import JobSourceFactory
from configs.app_container import Container
from helpers.job_utils import build_search_queries, add_site_refs_to_queries
from models.websearch_request import WebSearchParams

load_dotenv()


def get_job_search_queries() -> List[str]:

   # TODO: Get search queries based on user profile (pre-built)

    queries = build_search_queries(["AI Engineer", "ML Engineer"])
    queries = add_site_refs_to_queries(queries, JOBSEARCH_DOMAINS)

    return queries


def is_job_listing_url(url: str) -> bool:
    service = JobSourceFactory.create(url)
    job_path = service.get_job_post_path()

    if not job_path:
        return False

    return job_path in url


def process_searched_result(results: List[Dict[Any, Any]]):
    jobs: List[JobSearch] = []

    for item in results:
        url = item.get("url", "")

        if not is_job_listing_url(url):
            continue

        url = normalize_url(item.get("url", ""))
        score = item.get("score", 0)

        job_source_service = JobSourceFactory.create(url)
        external_id = get_hashed_id(job_source_service.get_canonical_id(url))

        if score >= JOBSEARCH_RELEVANCE_SCORE_CUTOFF:
            job = JobSearch(
                external_id = external_id,
                title = item.get("title", "Unknown Title"),
                url = url,
                content = item.get("content", ""),
                raw_content = item.get("raw_content") or "",
                published_datetime=item.get("published_date") or get_datetime_utc()
            )

            jobs.append(job)

    return jobs

def print_searched_jobs(jobs):
    for idx, job in enumerate(jobs):
        print(f"\n*********************** {idx + 1} **************************")
        print(f"Title: {job.title}")
        print(f"URL: {job.url}")
        print(f"Published data: {job.published_datetime}")


def search_jobs_by_queries(websearch_request: WebSearchParams,  
                           print_result: bool = False) -> JobSearchResponse:
    
    final_response: JobSearchResponse = JobSearchResponse()

    for domain in websearch_request.search_domains:
        for query in websearch_request.queries:

            if websearch_request.start_date and websearch_request.end_date:
                results = get_websearch_by_date_result(query=query,
                                                       start_date=websearch_request.start_date,
                                                       end_date=websearch_request.end_date,
                                                       search_domains=[domain],
                                                       country=websearch_request.country,
                                                       max_results=websearch_request.max_results)

            else:
                results = get_websearch_result(query=query,
                                               search_domains=[domain],
                                               country=websearch_request.country,
                                               max_results=websearch_request.max_results)

            final_response.jobs.extend(process_searched_result(results))

    final_response.jobs = list({job.url: job for job in final_response.jobs}.values())
    final_response.queries = websearch_request.queries
    final_response.total_results = len(final_response.jobs)

    if print_result:
        print_searched_jobs(final_response.jobs)


    return final_response
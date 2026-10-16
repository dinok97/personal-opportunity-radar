import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent.parent))

from job_ingestion.job_fetcher import get_jobs
from dto.job_ad import JobAd
from dto.job_search_params import JobSearchParams
from helpers.constants import JOBTECH_REQUEST_LIMIT
from helpers.utils import format_datetime, clean_text, parse_datetime_isoformat, get_datetime_local
from helpers.job_utils import TITLE_RULES, DESC_SPECIFIC, DESC_GENERIC

from datetime import datetime
from typing import Optional, Any


TITLE_BY_TYPE = dict(TITLE_RULES)
DESC_BY_TYPE = dict(DESC_SPECIFIC + DESC_GENERIC)

def matches_plan(emp_type: str, title: str, description: str) -> bool:
    if not emp_type:
        return True        

    if any(rx.search(title) for label, rx in TITLE_RULES if label != emp_type):
        return False

    if emp_type == "Full-time":
        return not any(rx.search(description) for _, rx in DESC_SPECIFIC)       

    if TITLE_BY_TYPE[emp_type].search(title):
        return True

    rx = DESC_BY_TYPE.get(emp_type)

    return bool(rx and rx.search(description))


def is_job_application_open(application_deadline) -> bool:
    if not application_deadline:
        return False

    return parse_datetime_isoformat(application_deadline) >= get_datetime_local()


def extract_cities(ad: dict) -> list[str]:
    addresses = ad.get("workplace_addresses") or []
    cities = [a["municipality"] for a in addresses if isinstance(a, dict) and a.get("municipality")]
    cities = list(dict.fromkeys(cities))     
    return cities


def ad_text(ad: dict) -> str:
    return (ad.get("description") or {}).get("text") or ""


def normalize(ad: dict) -> Optional[JobAd]:
    if ad and ad.get("id"):
        return JobAd(
            id = ad.get("id") or "",
            title = clean_text(ad.get("headline") or ""),
            employer = clean_text((ad.get("employer") or {}).get("name") or ""),
            cities = extract_cities(ad),
            application_deadline = ad.get("application_deadline"),
            publication_date = ad.get("publication_date"),
            description = clean_text(ad_text(ad)),
            url = ad.get("webpage_url") or ""
        )

    return None


def get_search_params(query: str, start_date: datetime, end_date: datetime) -> dict[str, Any]:
    params = {"q": query, "limit": JOBTECH_REQUEST_LIMIT}
    if start_date:
        params["published-after"] = format_datetime(start_date)
    
    if end_date:
        params["published-before"] = format_datetime(end_date)

    return params


def fetch_jobs(query: str, 
               emp_type: str,
               start_date: datetime, 
               end_date: datetime) -> list[JobAd]:
    
    all_ads: list[JobAd] = []
    new_job_ids: set[str] = set()

    params = get_search_params(query=query, 
                               start_date=start_date, 
                               end_date=end_date)
    hits = get_jobs(params)
    print(f"{query}: total {len(hits)} job ads")

    for ad in hits:
        ad_id = ad.get("id")
        if not ad_id or (ad_id in new_job_ids):
            continue

        if not matches_plan(emp_type, 
                            ad.get("headline") or "",
                            clean_text(ad_text(ad))):
            continue


        if is_job_application_open(ad.get('application_deadline')):
            normalized_ad = normalize(ad)

            new_job_ids.add(ad_id)

            if normalized_ad:
                all_ads.append(normalized_ad)
    
    print(f"{len(hits)} ads checked, {len(all_ads)} kept")
        

    return all_ads


def search_jobs_by_queries(job_search_request: JobSearchParams) -> list[JobAd]:
    queries = job_search_request.query_plans.queries
    emp_type = job_search_request.query_plans.emp_type
    all_ads: list[JobAd] = []

    for query in queries:
        job_ads: list[JobAd] = fetch_jobs(query=query, 
                                          emp_type=emp_type,
                                          start_date=job_search_request.start_date, 
                                          end_date=job_search_request.end_date)
 
        all_ads.extend(job_ads)
            
    jobs = list({job.id: job for job in all_ads}.values())
    
    print(f"Finally kept total {len(jobs)} kept")

    return jobs
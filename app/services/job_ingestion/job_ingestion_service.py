from dotenv import load_dotenv
from datetime import datetime

import sys 
from pathlib import Path
from typing import Optional

sys.path.append(str(Path(__file__).resolve().parent.parent))

from dto.user_job_pref import UserJobPreference
from dto.job_search_params import JobSearchParams, QueryPlan
from dto.job_ad import JobAd
from models.job import Job
from services.user_service.user_profile_service import get_user_job_preference
from services.job_ingestion.job_discovery_service import search_jobs_by_queries
from services.job_ingestion.job_extract_service import extract_jobs_info
from services.job_ingestion.job_search_schedule_service import get_schedule_timeline
from services.job_ingestion.job_search_schedule_service import save_search_schedule
from configs.app_container import Container
from helpers.utils import get_datetime_local
from helpers.constants import EMPLOYMENT_TYPE_QUERIES

load_dotenv()


def get_user_preferred_roles() -> list[str]:
    user_job_pref: Optional[UserJobPreference] = get_user_job_preference()

    if user_job_pref:
        return [role.strip() for role in user_job_pref.target_roles.split(";")]

    print("No user profile found. Please upload your CV to create a profile.")

    return []

def get_job_search_queries(preferred_types: list[str] | None = None) -> list[QueryPlan]:
    roles = [r for r in get_user_preferred_roles()]
    plans: list[QueryPlan] = []
    seen: set[str] = set()

    for emp_type, phrases in EMPLOYMENT_TYPE_QUERIES.items():
        if preferred_types and emp_type not in preferred_types:
            continue

        texts = [f"{role} {p}" for role in roles for p in phrases] if phrases else list(roles)

        texts = [t for t in texts if t.lower() not in seen] 
        seen.update(t.lower() for t in texts)

        if texts:
            plans.append(QueryPlan(queries=texts, emp_type=emp_type))

    return plans


def get_jobsearch_params():
    params: list[JobSearchParams] = []

    query_plans = get_job_search_queries()
    searchSchedule = get_schedule_timeline()

    if len(searchSchedule.date_windows) > 0: 
        for start_date, end_date in searchSchedule.date_windows:
            for plan in query_plans:
                params.append(JobSearchParams(
                    query_plans=plan,
                    start_date=start_date,
                    end_date=end_date,
                ))
    return params


def filter_unseen_jobs(job_ads: list[JobAd], should_print: bool = False) -> list[JobAd]:
    unseen_jobs: list[JobAd] = []
    
    searched_job_ids: list[str] =  [job.id for job in job_ads]
    existing_job_ids = Container.job_repository.get_existing_ids(searched_job_ids)

    new_job_ids = [ext_id for ext_id in searched_job_ids if ext_id not in existing_job_ids]

    filtered_set = set(new_job_ids)
    
    new_jobs: list[JobAd] = [
        job for job in job_ads
        if job.id in filtered_set
    ]

    if should_print:
        print("Existing Job IDs: ")
        print(", ".join(existing_job_ids))

        print("New Job IDs: ")
        print(", ".join(new_job_ids))


    unseen_jobs.extend(new_jobs)

    return unseen_jobs


def run_ingestion_pipeline():

    # TODO: Add logging mechanism
    
    search_params: list[JobSearchParams] = get_jobsearch_params()

    target_roles = get_user_preferred_roles()

    for request in search_params:
        total_found: int = 0
        total_unseen: int = 0
        total_saved: int = 0
        saved_job_ids: list[str] = []
        lastrun_scheduler: datetime

        print(f"""Search params:\nstart_date - {request.start_date},\nend_date - {request.end_date}""")

        try:
            print(f"Searching.....{request}")

            job_ads: list[JobAd] = search_jobs_by_queries(request)
            total_found = len(job_ads)
            print(f"Found {total_found} jobs")

            unseen_jobs: list[JobAd] = filter_unseen_jobs(job_ads)
            total_unseen = len(unseen_jobs)

            if total_unseen > 0:
                print(f"Found {total_unseen} unseen jobs")
        
                jobs: list[Job] = extract_jobs_info(target_roles, unseen_jobs)
                print(f"Successfully extracted {len(jobs)} job info")
        
                job_ids = Container.job_repository.save_jobs(jobs)
                print(f"Saved: {len(job_ids)} new jobs, job_ids: {', '.join(job_ids)}")
        
                total_saved=len(job_ids)
                saved_job_ids = job_ids
        
            else:
                print("No unseen jobs found")

            
            if request.end_date:
                lastrun_scheduler = request.end_date

            else:
                lastrun_scheduler = get_datetime_local()


            save_search_schedule(total_found=total_found,
                                 total_saved=total_saved,
                                 total_unseen=total_unseen,
                                 saved_job_ids=saved_job_ids,
                                 last_run=lastrun_scheduler)
            
        except Exception as e:
            print(f"Ingestion failed for window {request.start_date} → {request.end_date}: {e}")
            # TODO: proper logging
            continue


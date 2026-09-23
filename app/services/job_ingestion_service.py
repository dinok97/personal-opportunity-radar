from dotenv import load_dotenv
from typing import List
from datetime import datetime

import sys 
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))

from services.job_search_service import get_job_search_queries, search_jobs_by_queries
from models.job import JobSearchResponse, Job, JobSearch
from models.websearch_request import WebSearchParams
from services.job_extraction_service import scrape_raw_job_content, extract_jobs_info
from services.job_search_schedule_service import get_schedule_timeline, save_search_schedule
from configs.app_container import Container
from helpers.utils import get_datetime_utc, get_datetime_from_str_utc

load_dotenv()

def get_websearch_params() -> List[WebSearchParams]:
    params: List[WebSearchParams] = []

    queries = get_job_search_queries()
    searchSchedule = get_schedule_timeline()

    if len(searchSchedule.date_windows) > 0: 
        for item in searchSchedule.date_windows:
            params.append(WebSearchParams(queries=queries, start_date=item[0], end_date=item[1]))

    else:
        params.append(WebSearchParams(queries=queries, time_range=searchSchedule.time_range))

    return params
        

def filter_unseen_jobs(job_search_resp: JobSearchResponse, should_print: bool = False) -> JobSearchResponse:
    searched_job_ids: List[str] =  [job.external_id for job in job_search_resp.jobs]

    existing_job_ids = Container.job_repository.get_existing_ids(searched_job_ids)

    new_job_ids = [ext_id for ext_id in searched_job_ids if ext_id not in existing_job_ids]

    filtered_set = set(new_job_ids)
    
    new_jobs: List[JobSearch] = [
        job for job in job_search_resp.jobs 
        if job.external_id in filtered_set
    ]

    if should_print:
        print("Existing Job IDs: ")
        print(", ".join(existing_job_ids))

        print("New Job IDs: ")
        print(", ".join(new_job_ids))


    job_search_resp.jobs = new_jobs

    return job_search_resp


def run_ingestion_pipeline():

    # TODO: Add logging mechanism
    
    search_params: List[WebSearchParams] = get_websearch_params()

    for request in search_params:

        total_found: int = 0
        total_unseen: int = 0
        total_saved: int = 0
        saved_job_ids: List[str] = []
        lastrun_scheduler: datetime

        print(f"""Search params:\nstart_date - {request.start_date},\nend_date - {request.end_date},\ntime_range - {request.time_range}""")

        try:
            print(f"Searching.....")
            job_search_resp: JobSearchResponse = search_jobs_by_queries(request)
            total_found = len(job_search_resp.jobs)
            print(f"Found {total_found} jobs")

            unseen_jobs: JobSearchResponse = filter_unseen_jobs(job_search_resp)
            total_unseen = len(unseen_jobs.jobs)

            if len(unseen_jobs.jobs) > 0:
                print(f"Found {len(unseen_jobs.jobs)} unseen jobs")

                job_details: JobSearchResponse = scrape_raw_job_content(unseen_jobs)
                print(f"Scraped {len(job_details.jobs)} job details")

                # TODO: Keep only valid jobs accpting application & located in sweden

                jobs: List[Job] = extract_jobs_info(job_details)
                print(f"Successfully extracted {len(jobs)} job info")

                job_ids = Container.job_repository.save_jobs(jobs)
                print(f"Saved: {len(job_ids)} new jobs, job_ids: {', '.join(job_ids)}")

                total_saved=len(job_ids)
                saved_job_ids = job_ids

            else:
                print("No unseen jobs found")


            if request.end_date:
                parsed_datetime = get_datetime_from_str_utc(request.end_date)
                lastrun_scheduler = parsed_datetime if parsed_datetime else get_datetime_utc()

            else:
                lastrun_scheduler = get_datetime_utc()


            save_search_schedule(total_found=total_found,
                                 total_saved=total_saved,
                                 total_unseen=total_unseen,
                                 saved_job_ids=saved_job_ids,
                                 last_run=lastrun_scheduler)

        except Exception as e:
            print(f"Ingestion pipeline failed: {e}")
            # TODO: proper logging
            continue
    

    


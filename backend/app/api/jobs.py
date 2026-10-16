import logging

from fastapi import APIRouter, Depends, HTTPException, Query

from ..models.job import Job, JobSearchResult
from ..services.job_service import (
    JobService,
    JobServiceUnavailableError,
    get_job_service,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/jobs", tags=["jobs"])


def provide_job_service() -> JobService:
    try:
        return get_job_service()
    except JobServiceUnavailableError as exc:
        logger.exception("Job service could not be initialized")
        raise HTTPException(status_code=503, detail="Job search is unavailable") from exc


@router.get("/search", response_model=list[JobSearchResult])
def search_jobs(
    query: str = Query(min_length=1, max_length=500),
    k: int = Query(default=10, ge=1, le=50),
    service: JobService = Depends(provide_job_service),
) -> list[JobSearchResult]:
    try:
        return service.search_jobs(query, k)
    except Exception as exc:
        logger.exception("Job search failed")
        raise HTTPException(status_code=503, detail="Job search is unavailable") from exc


@router.get("/{job_id}", response_model=Job)
def get_job(
    job_id: str,
    service: JobService = Depends(provide_job_service),
) -> Job:
    try:
        job = service.get_job(job_id)
    except Exception as exc:
        logger.exception("Job lookup failed")
        raise HTTPException(status_code=503, detail="Job lookup is unavailable") from exc

    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")
    return job

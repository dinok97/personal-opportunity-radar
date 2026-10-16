from functools import lru_cache
from typing import Protocol

from langchain_core.documents import Document

from ..config import get_settings
from ..models.job import Job, JobSearchResult
from ..repositories.database import get_database
from ..repositories.job_repository import JobRepository
from .embedding_service import HuggingFaceEmbeddingClient


class JobServiceUnavailableError(RuntimeError):
    """The job database or embedding service is unavailable."""


class JobService:
    def __init__(self, repository: JobRepository) -> None:
        self.repository = repository

    def get_job(self, job_id: str) -> Job | None:
        return self.repository.get_job_by_id(job_id)

    def search_jobs(self, query: str, k: int = 10) -> list[JobSearchResult]:
        clean_query = query.strip()
        if not clean_query:
            raise ValueError("Job search query must not be empty")
        if k <= 0:
            raise ValueError("k must be greater than 0")

        matches = self.repository.get_jobs_by_query(clean_query, k)
        results = []
        for document, score in matches:
            job_data = dict(document.metadata)
            job_id = document.id or job_data.get("jobs_id")
            job_data["external_id"] = job_id
            job_data["embedding_text"] = document.page_content
            results.append(
                JobSearchResult(
                    job=Job.model_validate(job_data),
                    score=float(score),
                )
            )
        return results


@lru_cache(maxsize=1) # singleton, return same instance every call
def get_job_service() -> JobService:
    settings = get_settings()
    if not settings.pgvector_connection_string:
        raise JobServiceUnavailableError("The jobs database is not configured")

    try:
        database = get_database()
        embeddings = HuggingFaceEmbeddingClient(
            settings.embedding_model,
            settings.embedding_model_revision,
        )
        return JobService(JobRepository(database, embeddings))
    except Exception as exc:
        raise JobServiceUnavailableError("The job search service could not be initialized") from exc

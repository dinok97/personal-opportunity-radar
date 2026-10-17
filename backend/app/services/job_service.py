from functools import lru_cache
from typing import Protocol

from langchain_core.documents import Document
from sentence_transformers import CrossEncoder

from ..config import get_settings
from ..helpers.constants import JOB_RERANKER_MODEL
from ..models.job import Job, JobSearchResult
from ..repositories.database import get_database
from ..repositories.job_repository import JobRepository
from .embedding_service import HuggingFaceEmbeddingClient

@lru_cache(maxsize=1)
def _get_reranker() -> CrossEncoder:
    return CrossEncoder(JOB_RERANKER_MODEL)


class JobServiceUnavailableError(RuntimeError):
    """The job database or embedding service is unavailable."""


class JobService:
    def __init__(
        self,
        repository: JobRepository,
        *,
        reranker: CrossEncoder | None = None,
    ) -> None:
        self.repository = repository
        self.reranker = reranker

    def get_job(self, job_id: str) -> Job | None:
        return self.repository.get_job_by_id(job_id)

    def search_jobs(
        self,
        query: str,
        k: int = 10,
        candidate_k: int = 20,
    ) -> list[JobSearchResult]:
        clean_query = query.strip()
        if not clean_query:
            raise ValueError("Job search query must not be empty")
        if k <= 0:
            raise ValueError("k must be greater than 0")
        if candidate_k < k:
            raise ValueError("candidate_k must be greater than or equal to k")

        matches = self.repository.get_jobs_by_query(clean_query, candidate_k)
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

        if not results:
            return []

        reranker = self.reranker or _get_reranker()
        ranked = reranker.rank(
            clean_query,
            [result.job.embedding_text for result in results],
            top_k=min(k, len(results)),
        )
        return [
            JobSearchResult(
                job=results[item["corpus_id"]].job,
                score=float(item["score"]), # the similarity score, not relevance score
            )
            for item in ranked
        ]


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

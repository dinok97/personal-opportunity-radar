from functools import lru_cache
from typing import Optional, Literal

from langchain_core.documents import Document
from sentence_transformers import CrossEncoder

from ..config import get_settings
from ..helpers.constants import JOB_RERANKER_MODEL
from ..models.job import Job, JobSearchResult
from ..repositories.database import get_database
from ..repositories.job_repository import JobRepository
from .embedding_service import HuggingFaceEmbeddingClient


EmploymentType = Literal["Thesis", "PhD", "Full-time", "Part-time", "Internship", "Contract"]

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

    def rerank_text(self, job: Job) -> str:
        return (
            f"Title: {job.title}\n"
            f"Employment type: {job.employment_type or ''}\n"
            f"Company: {job.company or ''}\n"
            f"Locations: {job.locations or ''}\n"
            f"Specialization/Target Role: {job.specialization or ''}\n"
            f"Required Skills: {job.skills or ''}\n"
            f"Summary: {(job.executive_summary or '')}"
        )

    def rerank_jobs(self, query: str, jobs: list[JobSearchResult], top_k: int) -> list[JobSearchResult]:
        if not jobs:
            return []
        if len(jobs) == 1:
            return jobs


        reranker = self.reranker or _get_reranker()
        ranked_jobs = reranker.rank(
            query,
            [self.rerank_text(result.job) for result in jobs],
            top_k=min(top_k, len(jobs)),
        )
        return [
            JobSearchResult(
                job=jobs[item["corpus_id"]].job,
                score=float(item["score"]),
            )
            for item in ranked_jobs
        ]

    def get_job(self, job_id: str) -> Job | None:
        return self.repository.get_job_by_id(job_id)

    def search_jobs(
        self,
        query: str,
        k: int = 20,
        candidate_k: int = 30,
        employment_types: Optional[list[EmploymentType]] = None,
        locations: Optional[list[str]] = None,
        posted_before_days: Optional[int] = None,
        posted_after_days: Optional[int] = None,
        posted_on_days: Optional[int] = None,
        deadline_before_days: Optional[int] = None,
        deadline_after_days: Optional[int] = None,
        deadline_on_days: Optional[int] = None
    ) -> list[JobSearchResult]:
        clean_query = query.strip()
        if not clean_query:
            raise ValueError("Job search query must not be empty")
        if k <= 0:
            raise ValueError("k must be greater than 0")
        if candidate_k < k:
            raise ValueError("candidate_k must be greater than or equal to k")

        matches = self.repository.get_jobs_by_query(clean_query, 
                                                    candidate_k,
                                                    employment_types=employment_types,
                                                    locations=locations,
                                                    posted_before_days=posted_before_days,
                                                    posted_after_days=posted_after_days,
                                                    posted_on_days=posted_on_days,
                                                    deadline_before_days=deadline_before_days,
                                                    deadline_after_days=deadline_after_days,
                                                    deadline_on_days=deadline_on_days)
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

        print(results)

        return self.rerank_jobs(query=clean_query, jobs=results, top_k=k)


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

from datetime import datetime

import pytest
from langchain_core.documents import Document

from backend.app.models.job import Job, JobSearchResult
from backend.app.services.job_service import JobService


class FakeJobRepository:
    def __init__(self, job: Job, additional_jobs: list[Job] | None = None) -> None:
        self.job = job
        self.jobs = [job, *(additional_jobs or [])]
        self.query = None
        self.k = None
        self.job_id = None

    def get_job_by_id(self, job_id: str) -> Job | None:
        self.job_id = job_id
        return self.job if job_id == self.job.external_id else None

    def get_jobs_by_query(self, query: str, k: int):
        self.query = query
        self.k = k
        return [
            (
                Document(
                    id=job.external_id,
                    page_content=job.embedding_text,
                    metadata=job.model_dump(exclude={"external_id", "embedding_text"}),
                ),
                0.12 + index,
            )
            for index, job in enumerate(self.jobs[:k])
        ]


class FakeReranker:
    def __init__(self, rankings: list[dict[str, float | int]]) -> None:
        self.rankings = rankings
        self.query = None
        self.documents = None
        self.top_k = None

    def rank(self, query: str, documents: list[str], *, top_k: int):
        self.query = query
        self.documents = documents
        self.top_k = top_k
        return self.rankings[:top_k]


def make_job() -> Job:
    return Job(
        external_id="job-123",
        title="ML Engineer",
        company="Example Labs",
        source="Job Board",
        url="https://example.com/jobs/123",
        posted_at=None,
        locations="Remote",
        specialization="Machine Learning",
        employment_type="Full-time",
        skills="Python, PyTorch",
        application_deadline_at=datetime(2026, 12, 31),
        executive_summary="Build ML systems.",
        embedding_text="ML Engineer at Example Labs",
        is_active=True,
        is_deleted=False,
    )


def test_search_jobs_maps_repository_documents_to_typed_results() -> None:
    repository = FakeJobRepository(make_job())
    service = JobService(repository, reranker=FakeReranker([{"corpus_id": 0, "score": 0.88}]))

    results = service.search_jobs("  machine learning ", k=4)

    assert results == [JobSearchResult(job=make_job(), score=0.88)]
    assert repository.query == "machine learning"
    assert repository.k == 20


def test_search_jobs_returns_candidates_in_reranker_order() -> None:
    first_job = make_job()
    second_job = first_job.model_copy(
        update={"external_id": "job-456", "title": "Senior ML Engineer"}
    )
    repository = FakeJobRepository(first_job, [second_job])
    reranker = FakeReranker(
        [
            {"corpus_id": 1, "score": 0.95},
            {"corpus_id": 0, "score": 0.20},
        ]
    )
    service = JobService(repository, reranker=reranker)

    results = service.search_jobs("machine learning", k=1, candidate_k=2)

    assert [result.job.external_id for result in results] == ["job-456"]
    assert results[0].score == 0.95
    assert reranker.query == "machine learning"
    assert reranker.documents == [first_job.embedding_text, second_job.embedding_text]
    assert reranker.top_k == 1
    assert repository.k == 2


def test_search_jobs_rejects_empty_query_and_invalid_limit() -> None:
    service = JobService(FakeJobRepository(make_job()))

    with pytest.raises(ValueError, match="query must not be empty"):
        service.search_jobs("  ")
    with pytest.raises(ValueError, match="greater than 0"):
        service.search_jobs("Python", k=0)
    with pytest.raises(ValueError, match="candidate_k must be greater than or equal to k"):
        service.search_jobs("Python", k=2, candidate_k=1)


def test_get_job_delegates_to_repository() -> None:
    repository = FakeJobRepository(make_job())
    service = JobService(repository)

    assert service.get_job("job-123") == make_job()
    assert repository.job_id == "job-123"
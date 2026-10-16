from datetime import datetime

import pytest
from langchain_core.documents import Document

from backend.app.models.job import Job, JobSearchResult
from backend.app.services.job_service import JobService


class FakeJobRepository:
    def __init__(self, job: Job) -> None:
        self.job = job
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
                    id=self.job.external_id,
                    page_content=self.job.embedding_text,
                    metadata=self.job.model_dump(exclude={"external_id", "embedding_text"}),
                ),
                0.12,
            )
        ][:k]


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
    service = JobService(repository)

    results = service.search_jobs("  machine learning ", k=4)

    assert results == [JobSearchResult(job=make_job(), score=0.12)]
    assert repository.query == "machine learning"
    assert repository.k == 4


def test_search_jobs_rejects_empty_query_and_invalid_limit() -> None:
    service = JobService(FakeJobRepository(make_job()))

    with pytest.raises(ValueError, match="query must not be empty"):
        service.search_jobs("  ")
    with pytest.raises(ValueError, match="greater than 0"):
        service.search_jobs("Python", k=0)


def test_get_job_delegates_to_repository() -> None:
    repository = FakeJobRepository(make_job())
    service = JobService(repository)

    assert service.get_job("job-123") == make_job()
    assert repository.job_id == "job-123"
from datetime import datetime

from fastapi import FastAPI
from fastapi.testclient import TestClient

from backend.app.api.jobs import provide_job_service, router
from backend.app.models.job import Job, JobSearchResult


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
    )


class FakeJobService:
    def __init__(self) -> None:
        self.query = None
        self.k = None

    def search_jobs(self, query: str, k: int):
        self.query = query
        self.k = k
        return [JobSearchResult(job=make_job(), score=0.12)]

    def get_job(self, job_id: str):
        return make_job() if job_id == "job-123" else None


def make_client(service: FakeJobService) -> TestClient:
    app = FastAPI()
    app.include_router(router)
    app.dependency_overrides[provide_job_service] = lambda: service
    return TestClient(app)


def test_search_jobs_endpoint_returns_job_and_score() -> None:
    service = FakeJobService()
    client = make_client(service)

    response = client.get("/api/jobs/search", params={"query": "Python", "k": 3})

    assert response.status_code == 200
    assert response.json()[0]["job"]["external_id"] == "job-123"
    assert response.json()[0]["score"] == 0.12
    assert service.query == "Python"
    assert service.k == 3


def test_get_job_endpoint_returns_job_or_404() -> None:
    client = make_client(FakeJobService())

    response = client.get("/api/jobs/job-123")
    missing_response = client.get("/api/jobs/missing")

    assert response.status_code == 200
    assert response.json()["external_id"] == "job-123"
    assert missing_response.status_code == 404
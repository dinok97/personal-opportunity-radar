from langchain_core.documents import Document

from backend.app.models.job import Job
from backend.app.repositories.job_repository import JobRepository


class FakeDatabase:
    def __init__(self, row=None) -> None:
        self.engine = object()
        self.row = row
        self.sql = None
        self.params = None

    def fetch_one(self, sql, params=()):
        self.sql = sql
        self.params = params
        return self.row


class FakeEmbeddingService:
    model = object()


class FakeVectorStore:
    def __init__(self) -> None:
        self.search_args = None
        self.results = [(Document(page_content="Machine learning engineer"), 0.12)]

    def similarity_search_with_score(self, **kwargs):
        self.search_args = kwargs
        return self.results


def test_get_job_by_id_returns_database_row() -> None:
    row = {
        "jobs_id": "job-123",
        "title": "ML Engineer",
        "company": "Example Labs",
        "source": "Job Board",
        "url": "https://example.com/jobs/123",
        "posted_at": None,
        "locations": "Remote",
        "specialization": "Machine Learning",
        "employment_type": "Full-time",
        "skills": "Python, PyTorch",
        "application_deadline_at": "2026-12-31T00:00:00",
        "executive_summary": "Build ML systems.",
        "embedding_text": "ML Engineer at Example Labs",
        "is_active": True,
        "is_deleted": False,
    }
    database = FakeDatabase(row)
    repository = JobRepository(database, FakeEmbeddingService())

    result = repository.get_job_by_id("job-123")

    assert result == Job(
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
        application_deadline_at="2026-12-31T00:00:00",
        executive_summary="Build ML systems.",
        embedding_text="ML Engineer at Example Labs",
        is_active=True,
        is_deleted=False,
    )
    assert database.sql == "SELECT * FROM jobs WHERE jobs_id = %s"
    assert database.params == ("job-123",)


def test_get_job_by_id_skips_empty_id() -> None:
    database = FakeDatabase()
    repository = JobRepository(database, FakeEmbeddingService())

    assert repository.get_job_by_id("") is None
    assert database.sql is None


def test_get_jobs_by_query_uses_jobs_table_and_active_filters() -> None:
    database = FakeDatabase()
    vector_store = FakeVectorStore()
    captured = {}

    def vector_store_factory(**kwargs):
        captured.update(kwargs)
        return vector_store

    repository = JobRepository(
        database,
        FakeEmbeddingService(),
        vector_store_factory=vector_store_factory,
    )

    results = repository.get_jobs_by_query("machine learning", 4)

    assert results == vector_store.results
    assert captured["table_name"] == "jobs"
    assert captured["id_column"] == "jobs_id"
    assert captured["content_column"] == "embedding_text"
    assert vector_store.search_args == {
        "query": "machine learning",
        "k": 4,
        "filter": {
            "$and": [
                {"is_active": {"$eq": True}},
                {"is_deleted": {"$eq": False}},
            ]
        },
    }
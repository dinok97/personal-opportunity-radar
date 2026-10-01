import os
import uuid
from datetime import datetime, timezone
from types import SimpleNamespace

import pytest
from sqlalchemy import JSON
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from backend.app.config import Settings
from backend.app.repositories.cv_vector_repository import (
    CvVectorConfigurationError,
    CvVectorDimensionError,
    CvVectorRepository,
)
from backend.app.services.cv_chunking import CvChunk


class FakeBase(DeclarativeBase):
    pass


class FakeEmbeddingStore(FakeBase):
    __tablename__ = "fake_langchain_pg_embedding"

    id: Mapped[str] = mapped_column(primary_key=True)
    collection_id: Mapped[str] = mapped_column()
    embedding: Mapped[list] = mapped_column(JSON)
    document: Mapped[str] = mapped_column()
    cmetadata: Mapped[dict] = mapped_column(JSON)


class FakeTransaction:
    def __init__(self, session):
        self.session = session

    def __enter__(self):
        return self.session

    def __exit__(self, exc_type, exc_value, traceback):
        self.session.committed = exc_type is None
        self.session.rolled_back = exc_type is not None
        return False


class FakeQuery:
    def __init__(self, rows):
        self.rows = rows

    def filter(self, condition):
        return self

    def all(self):
        return self.rows


class FakeSession:
    def __init__(self, fail_merge_number=None, rows=None):
        self.fail_merge_number = fail_merge_number
        self.rows = list(rows or [])
        self.merged = []
        self.statements = []
        self.committed = False
        self.rolled_back = False

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        return False

    def begin(self):
        return FakeTransaction(self)

    def merge(self, record):
        self.merged.append(record)
        if len(self.merged) == self.fail_merge_number:
            raise SQLAlchemyError("injected write failure")

    def flush(self):
        pass

    def execute(self, statement):
        self.statements.append(statement)

    def query(self, model):
        return FakeQuery(self.rows)


class FakeVectorStore:
    def __init__(self, *, fail_merge_number=None, rows=None):
        self.EmbeddingStore = FakeEmbeddingStore
        self.session = FakeSession(fail_merge_number, rows)
        self.session_maker = lambda: self.session
        self.collection = SimpleNamespace(uuid="collection-id", cmetadata=None)

    def get_collection(self, session):
        return self.collection


class FakeEmbeddings:
    def embed_documents(self, texts):
        return [[0.1, 0.2, 0.3] for _ in texts]


def make_settings(table_name="cv_chunks", connection_string="postgresql://db/cv"):
    return Settings(
        _env_file=None,
        pgvector_connection_string=connection_string,
        pgvector_collection_name=table_name,
        pgvector_embedding_dimension=3,
    )


def make_repository(*, settings=None, store=None, fail_merge_number=None):
    store = store or FakeVectorStore(fail_merge_number=fail_merge_number)
    captured = {}

    def vector_store_factory(**kwargs):
        captured.update(kwargs)
        return store

    repository = CvVectorRepository(
        settings or make_settings(),
        embeddings=FakeEmbeddings(),
        vector_store_factory=vector_store_factory,
    )
    return repository, store, captured


def make_chunk(document_id="new-cv", chunk_id="chunk-1", page_number=1):
    return CvChunk(
        id=chunk_id,
        content=f"Text for {chunk_id}",
        metadata={
            "document_id": document_id,
            "filename": "resume.pdf",
            "uploaded_at": datetime(2026, 9, 27, tzinfo=timezone.utc).isoformat(),
            "page_number": page_number,
            "chunk_index": 0,
        },
    )


def test_repository_setup_is_idempotent_and_configures_langchain_store() -> None:
    repository, store, captured = make_repository()

    repository.setup()
    repository.setup()

    assert repository.vector_store is store
    assert captured == {
        "embeddings": repository.embeddings,
        "connection": "postgresql+psycopg://db/cv",
        "collection_name": "cv_chunks",
        "embedding_length": 3,
    }


def test_repository_requires_database_configuration() -> None:
    settings = make_settings(connection_string=None)

    with pytest.raises(CvVectorConfigurationError):
        CvVectorRepository(settings, embeddings=FakeEmbeddings())


def test_repository_reads_all_active_chunks_in_page_order() -> None:
    rows = [
        FakeEmbeddingStore(
            id="chunk-2",
            collection_id="collection-id",
            embedding=[0.1, 0.2, 0.3],
            document="Second page",
            cmetadata={"page_number": 2, "chunk_index": 0},
        ),
        FakeEmbeddingStore(
            id="chunk-1b",
            collection_id="collection-id",
            embedding=[0.1, 0.2, 0.3],
            document="Second chunk on first page",
            cmetadata={"page_number": 1, "chunk_index": 1},
        ),
        FakeEmbeddingStore(
            id="chunk-1a",
            collection_id="collection-id",
            embedding=[0.1, 0.2, 0.3],
            document="First chunk on first page",
            cmetadata={"page_number": 1, "chunk_index": 0},
        ),
    ]
    store = FakeVectorStore(rows=rows)
    repository, _, _ = make_repository(store=store)

    chunks = repository.get_active_cv_chunks()

    assert [chunk.id for chunk in chunks] == ["chunk-1a", "chunk-1b", "chunk-2"]
    assert [chunk.content for chunk in chunks] == [
        "First chunk on first page",
        "Second chunk on first page",
        "Second page",
    ]
    assert chunks[0].metadata == {"page_number": 1, "chunk_index": 0}


def test_repository_returns_no_chunks_when_collection_is_missing() -> None:
    repository, store, _ = make_repository()
    store.collection = None

    assert repository.get_active_cv_chunks() == []


def test_repository_persists_and_reads_user_profile() -> None:
    from backend.app.models import UserProfile

    repository, store, _ = make_repository()
    profile = UserProfile(name="Alicia Morgan", topSkills=["Python"])

    repository.save_user_profile(profile)

    assert repository.get_cached_user_profile() == profile
    assert store.collection.cmetadata["user_profile"] == profile.model_dump(mode="json")


def test_repository_invalidates_profile_when_replacing_active_cv() -> None:
    from backend.app.models import UserProfile

    repository, store, _ = make_repository()
    repository.save_user_profile(UserProfile(name="Previous CV"))

    repository.replace_active_cv([make_chunk()], [[0.1, 0.2, 0.3]])

    assert repository.get_cached_user_profile() is None


def test_repository_rejects_wrong_embedding_dimension_before_connecting() -> None:
    repository, _, _ = make_repository()

    with pytest.raises(CvVectorDimensionError):
        repository.replace_active_cv([make_chunk()], [[0.1, 0.2]])

    assert repository._vector_store is None


def test_repository_writes_new_chunks_before_removing_old_documents() -> None:
    repository, store, _ = make_repository()
    chunks = [make_chunk(chunk_id="chunk-1"), make_chunk(chunk_id="chunk-2", page_number=2)]

    count = repository.replace_active_cv(chunks, [[0.1, 0.2, 0.3], [0.4, 0.5, 0.6]])

    assert count == 2
    assert [record.id for record in store.session.merged] == ["chunk-1", "chunk-2"]
    assert [record.document for record in store.session.merged] == [
        "Text for chunk-1",
        "Text for chunk-2",
    ]
    assert len(store.session.statements) == 1
    assert store.session.committed


def test_repository_rolls_back_and_keeps_old_rows_when_a_write_fails() -> None:
    repository, store, _ = make_repository(fail_merge_number=2)

    with pytest.raises(SQLAlchemyError, match="injected write failure"):
        repository.replace_active_cv(
            [make_chunk(chunk_id="chunk-1"), make_chunk(chunk_id="chunk-2")],
            [[0.1, 0.2, 0.3], [0.4, 0.5, 0.6]],
        )

    assert store.session.rolled_back
    assert store.session.statements == []


CV_PGVECTOR_TEST_CONNECTION_STRING = os.getenv("CV_PGVECTOR_TEST_CONNECTION_STRING")


@pytest.mark.skipif(
    not CV_PGVECTOR_TEST_CONNECTION_STRING,
    reason="Set CV_PGVECTOR_TEST_CONNECTION_STRING to run the PGVector integration test",
)
def test_pgvector_setup_write_and_active_cv_replacement() -> None:
    collection_name = f"cv_test_{uuid.uuid4().hex}"
    settings = Settings(
        _env_file=None,
        pgvector_connection_string=CV_PGVECTOR_TEST_CONNECTION_STRING,
        pgvector_collection_name=collection_name,
        pgvector_embedding_dimension=3,
    )
    repository = CvVectorRepository(settings, embeddings=FakeEmbeddings())

    try:
        repository.setup()
        repository.setup()
        repository.replace_active_cv(
            [make_chunk(document_id="old-cv")],
            [[0.1, 0.2, 0.3]],
        )
        repository.replace_active_cv(
            [make_chunk(document_id="new-cv", chunk_id="new-1", page_number=2)],
            [[0.4, 0.5, 0.6]],
        )

        documents = repository.vector_store.similarity_search_by_vector(
            embedding=[0.4, 0.5, 0.6],
            k=10,
        )

        assert len(documents) == 1
        assert documents[0].page_content == "Text for new-1"
        assert documents[0].metadata["document_id"] == "new-cv"
        assert documents[0].metadata["page_number"] == 2
    finally:
        repository.vector_store.delete_collection()
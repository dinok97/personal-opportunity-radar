import os
import uuid
from datetime import datetime, timezone

import psycopg
import pytest
from psycopg import sql

from backend.app.config import Settings
from backend.app.repositories.cv_vector_repository import (
    CvVectorDimensionError,
    CvVectorRepository,
    CvVectorSchemaError,
)
from backend.app.services.cv_chunking import CvChunk


EXPECTED_COLUMNS = [
    ("id", "text", "text"),
    ("document_id", "text", "text"),
    ("content", "text", "text"),
    ("embedding", "USER-DEFINED", "vector"),
    ("metadata", "jsonb", "jsonb"),
]


class FakeCursor:
    def __init__(self, rows=()):
        self.rows = list(rows)

    def fetchall(self):
        return self.rows

    def fetchone(self):
        return self.rows[0] if self.rows else None


class FakeConnection:
    def __init__(self, *, embedding_type="vector(3)", fail_insert_number=None):
        self.embedding_type = embedding_type
        self.fail_insert_number = fail_insert_number
        self.insert_count = 0
        self.table_create_count = 0
        self.events = []
        self.committed = False
        self.rolled_back = False

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.committed = exc_type is None
        self.rolled_back = exc_type is not None
        return False

    def execute(self, query, parameters=None):
        if isinstance(query, str) and "information_schema.columns" in query:
            return FakeCursor(EXPECTED_COLUMNS)
        if isinstance(query, str) and "format_type" in query:
            return FakeCursor([(self.embedding_type,)])
        if isinstance(query, sql.Composed) and parameters is None:
            self.table_create_count += 1
        if isinstance(query, sql.Composed) and parameters and len(parameters) == 5:
            self.insert_count += 1
            self.events.append("insert")
            if self.insert_count == self.fail_insert_number:
                raise psycopg.OperationalError("injected write failure")
        elif isinstance(query, sql.Composed) and parameters and len(parameters) == 2:
            self.events.append("delete-stale")
        elif isinstance(query, sql.Composed) and parameters and len(parameters) == 1:
            self.events.append("delete-old")
        return FakeCursor()


def make_settings(table_name="cv_chunks", connection_string="postgresql://db/cv"):
    return Settings(
        _env_file=None,
        pgvector_connection_string=connection_string,
        pgvector_table_name=table_name,
        pgvector_embedding_dimension=3,
    )


def make_repository(connection, *, settings=None):
    return CvVectorRepository(
        settings or make_settings(),
        connection_factory=lambda connection_string: connection,
        vector_registrar=lambda connection: None,
    )


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


def test_repository_setup_is_idempotent_and_checks_table_dimension() -> None:
    connection = FakeConnection()
    repository = make_repository(connection)

    repository.setup()
    repository.setup()

    assert connection.committed
    assert connection.table_create_count == 2


def test_repository_setup_rejects_incompatible_existing_dimension() -> None:
    repository = make_repository(FakeConnection(embedding_type="vector(4)"))

    with pytest.raises(CvVectorSchemaError, match=r"expected vector\(3\)"):
        repository.setup()


def test_repository_normalizes_sqlalchemy_psycopg_connection_url() -> None:
    connection = FakeConnection()
    captured = {}

    def connection_factory(connection_string):
        captured["connection_string"] = connection_string
        return connection

    repository = CvVectorRepository(
        make_settings(connection_string="postgresql+psycopg://db/cv"),
        connection_factory=connection_factory,
        vector_registrar=lambda current_connection: None,
    )
    repository.setup()

    assert captured["connection_string"] == "postgresql://db/cv"


def test_repository_rejects_wrong_embedding_dimension_before_connecting() -> None:
    connection = FakeConnection()
    repository = make_repository(connection)

    with pytest.raises(CvVectorDimensionError):
        repository.replace_active_cv([make_chunk()], [[0.1, 0.2]])

    assert connection.events == []


def test_repository_writes_new_chunks_before_removing_old_documents() -> None:
    connection = FakeConnection()
    repository = make_repository(connection)
    chunks = [make_chunk(chunk_id="chunk-1"), make_chunk(chunk_id="chunk-2", page_number=2)]

    count = repository.replace_active_cv(chunks, [[0.1, 0.2, 0.3], [0.4, 0.5, 0.6]])

    assert count == 2
    assert connection.events == ["insert", "insert", "delete-stale", "delete-old"]
    assert connection.committed


def test_repository_rolls_back_and_keeps_old_rows_when_a_write_fails() -> None:
    connection = FakeConnection(fail_insert_number=2)
    repository = make_repository(connection)

    with pytest.raises(psycopg.OperationalError):
        repository.replace_active_cv(
            [make_chunk(chunk_id="chunk-1"), make_chunk(chunk_id="chunk-2")],
            [[0.1, 0.2, 0.3], [0.4, 0.5, 0.6]],
        )

    assert connection.rolled_back
    assert connection.events == ["insert", "insert"]


CV_PGVECTOR_TEST_CONNECTION_STRING = os.getenv("CV_PGVECTOR_TEST_CONNECTION_STRING")


@pytest.mark.skipif(
    not CV_PGVECTOR_TEST_CONNECTION_STRING,
    reason="Set CV_PGVECTOR_TEST_CONNECTION_STRING to run the PGVector integration test",
)
def test_pgvector_setup_write_and_active_cv_replacement() -> None:
    table_name = f"cv_test_{uuid.uuid4().hex}"
    settings = Settings(
        _env_file=None,
        pgvector_connection_string=CV_PGVECTOR_TEST_CONNECTION_STRING,
        pgvector_table_name=table_name,
        pgvector_embedding_dimension=3,
    )
    repository = CvVectorRepository(settings)

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

        with psycopg.connect(repository.connection_string) as connection:
            rows = connection.execute(
                sql.SQL("SELECT document_id, content, metadata FROM {}")
                .format(sql.Identifier(table_name))
            ).fetchall()

        assert len(rows) == 1
        assert rows[0][0] == "new-cv"
        assert rows[0][1] == "Text for new-1"
        assert rows[0][2]["page_number"] == 2
    finally:
        with psycopg.connect(repository.connection_string) as connection:
            connection.execute(sql.SQL("DROP TABLE IF EXISTS {}").format(sql.Identifier(table_name)))
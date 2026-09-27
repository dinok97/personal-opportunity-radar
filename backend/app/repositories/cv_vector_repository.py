from collections.abc import Callable, Sequence
from typing import Any

import psycopg
from pgvector.psycopg import register_vector
from psycopg import sql
from psycopg.types.json import Jsonb

from ..config import Settings
from ..services.cv_chunking import CvChunk


class CvVectorConfigurationError(ValueError):
    """The CV vector store is not configured."""


class CvVectorSchemaError(RuntimeError):
    """The existing CV vector table does not match the configured schema."""


class CvVectorDimensionError(ValueError):
    """An embedding does not match the configured vector dimension."""


class CvVectorRepository:
    def __init__(
        self,
        settings: Settings,
        *,
        connection_factory: Callable[..., Any] = psycopg.connect,
        vector_registrar: Callable[..., Any] = register_vector,
    ) -> None:
        if not settings.pgvector_connection_string:
            raise CvVectorConfigurationError("PGVECTOR_CONNECTION_STRING is not configured")

        self.connection_string = settings.pgvector_connection_string.replace(
            "postgresql+psycopg://", "postgresql://", 1
        )
        self.table_name = settings.pgvector_table_name
        self.embedding_dimension = settings.pgvector_embedding_dimension
        self._connection_factory = connection_factory
        self._vector_registrar = vector_registrar

    def setup(self) -> None:
        with self._connection_factory(self.connection_string) as connection:
            self._ensure_schema(connection)

    def _ensure_schema(self, connection: Any) -> None:
        connection.execute("CREATE EXTENSION IF NOT EXISTS vector")
        create_table = sql.SQL(
            """
            CREATE TABLE IF NOT EXISTS {} (
                id TEXT PRIMARY KEY,
                document_id TEXT NOT NULL,
                content TEXT NOT NULL,
                embedding vector({}) NOT NULL,
                metadata JSONB NOT NULL
            )
            """
        ).format(sql.Identifier(self.table_name), sql.Literal(self.embedding_dimension))
        connection.execute(create_table)

        rows = connection.execute(
            """
            SELECT column_name, data_type, udt_name
            FROM information_schema.columns
            WHERE table_schema = current_schema() AND table_name = %s
            """,
            (self.table_name,),
        ).fetchall()
        columns = {name: (data_type, udt_name) for name, data_type, udt_name in rows}
        expected_columns = {
            "id": ("text", "text"),
            "document_id": ("text", "text"),
            "content": ("text", "text"),
            "embedding": ("USER-DEFINED", "vector"),
            "metadata": ("jsonb", "jsonb"),
        }
        incompatible_columns = {
            name: (columns.get(name), expected)
            for name, expected in expected_columns.items()
            if columns.get(name) != expected
        }
        if incompatible_columns:
            raise CvVectorSchemaError(
                f"Table '{self.table_name}' is missing required columns or has incompatible types"
            )

        embedding_type = connection.execute(
            """
            SELECT format_type(attribute.atttypid, attribute.atttypmod)
            FROM pg_attribute AS attribute
            WHERE attribute.attrelid = to_regclass(%s)
                AND attribute.attname = 'embedding'
                AND attribute.attnum > 0
                AND NOT attribute.attisdropped
            """,
            (self.table_name,),
        ).fetchone()
        expected_type = f"vector({self.embedding_dimension})"
        if embedding_type is None or embedding_type[0] != expected_type:
            actual_type = embedding_type[0] if embedding_type else "missing"
            raise CvVectorSchemaError(
                f"Table '{self.table_name}' embedding type is {actual_type}; "
                f"expected {expected_type}"
            )

    def replace_active_cv(
        self,
        chunks: Sequence[CvChunk],
        embeddings: Sequence[Sequence[float]],
    ) -> int:
        if not chunks:
            raise ValueError("At least one CV chunk is required")
        if len(chunks) != len(embeddings):
            raise ValueError("Each CV chunk must have one embedding")

        document_ids = {chunk.metadata.get("document_id") for chunk in chunks}
        if len(document_ids) != 1 or not isinstance(next(iter(document_ids)), str):
            raise ValueError("All CV chunks must belong to one document")
        document_id = next(iter(document_ids))
        if not document_id:
            raise ValueError("CV chunks must have a non-empty document_id")
        if len({chunk.id for chunk in chunks}) != len(chunks):
            raise ValueError("CV chunk IDs must be unique")

        records = []
        for chunk, embedding in zip(chunks, embeddings):
            if len(embedding) != self.embedding_dimension:
                raise CvVectorDimensionError(
                    f"Embedding dimension {len(embedding)} does not match configured "
                    f"dimension {self.embedding_dimension}"
                )
            records.append(
                (
                    chunk.id,
                    document_id,
                    chunk.content,
                    list(embedding),
                    Jsonb(dict(chunk.metadata)),
                )
            )

        insert = sql.SQL(
            """
            INSERT INTO {} (id, document_id, content, embedding, metadata)
            VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT (id) DO UPDATE SET
                document_id = EXCLUDED.document_id,
                content = EXCLUDED.content,
                embedding = EXCLUDED.embedding,
                metadata = EXCLUDED.metadata
            """
        ).format(sql.Identifier(self.table_name))
        remove_stale_chunks = sql.SQL(
            "DELETE FROM {} WHERE document_id = %s AND NOT (id = ANY(%s))"
        ).format(sql.Identifier(self.table_name))
        remove_old_documents = sql.SQL(
            "DELETE FROM {} WHERE document_id <> %s"
        ).format(sql.Identifier(self.table_name))

        with self._connection_factory(self.connection_string) as connection:
            self._ensure_schema(connection)
            self._vector_registrar(connection)
            for record in records:
                connection.execute(insert, record)
            connection.execute(remove_stale_chunks, (document_id, [chunk.id for chunk in chunks]))
            connection.execute(remove_old_documents, (document_id,))

        return len(records)
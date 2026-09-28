from collections.abc import Callable, Sequence
from typing import Any

from langchain_postgres import PGVector
from pydantic import ValidationError
from sqlalchemy import delete

from ..config import Settings
from ..models import UserProfile
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
        embeddings: Any | None = None,
        vector_store_factory: Callable[..., PGVector] = PGVector,
    ) -> None:
        if not settings.pgvector_connection_string:
            raise CvVectorConfigurationError("PGVECTOR_CONNECTION_STRING is not configured")

        self.connection_string = settings.pgvector_connection_string.replace(
            "postgresql://", "postgresql+psycopg://", 1
        )
        self.collection_name = settings.pgvector_collection_name
        self.embedding_dimension = settings.pgvector_embedding_dimension
        self.embeddings = embeddings
        self._vector_store_factory = vector_store_factory
        self._vector_store: PGVector | None = None

    @property
    def vector_store(self) -> PGVector:
        if self._vector_store is None:
            self._vector_store = self._vector_store_factory(
                embeddings=self.embeddings,
                connection=self.connection_string,
                collection_name=self.collection_name,
                embedding_length=self.embedding_dimension,
            )
        return self._vector_store

    def setup(self) -> None:
        self.vector_store

    def get_active_cv_chunks(self) -> list[CvChunk]:
        vector_store = self.vector_store
        embedding_store = getattr(vector_store, "EmbeddingStore")
        with vector_store.session_maker() as session:
            collection = vector_store.get_collection(session)
            if collection is None:
                return []
            rows = (
                session.query(embedding_store)
                .filter(embedding_store.collection_id == collection.uuid)
                .all()
            )

        rows.sort(
            key=lambda row: (
                (row.cmetadata or {}).get("page_number", 0),
                (row.cmetadata or {}).get("chunk_index", 0),
                row.id,
            )
        )
        return [
            CvChunk(
                id=row.id,
                content=row.document or "",
                metadata=dict(row.cmetadata or {}),
            )
            for row in rows
        ]

    def get_cached_user_profile(self) -> UserProfile | None:
        vector_store = self.vector_store
        with vector_store.session_maker() as session:
            collection = vector_store.get_collection(session)
            profile_data = (collection.cmetadata or {}).get("user_profile") if collection else None

        if not isinstance(profile_data, dict):
            return None
        try:
            return UserProfile.model_validate(profile_data)
        except ValidationError:
            return None

    def save_user_profile(self, profile: UserProfile) -> None:
        vector_store = self.vector_store
        with vector_store.session_maker() as session:
            with session.begin():
                collection = vector_store.get_collection(session)
                if collection is None:
                    raise CvVectorSchemaError(
                        f"Collection '{self.collection_name}' was not initialized"
                    )
                collection_metadata = dict(collection.cmetadata or {})
                collection_metadata["user_profile"] = profile.model_dump(mode="json")
                collection.cmetadata = collection_metadata

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

        for chunk, embedding in zip(chunks, embeddings):
            if len(embedding) != self.embedding_dimension:
                raise CvVectorDimensionError(
                    f"Embedding dimension {len(embedding)} does not match configured "
                    f"dimension {self.embedding_dimension}"
                )
        vector_store = self.vector_store
        embedding_store = getattr(vector_store, "EmbeddingStore")
        chunk_ids = [chunk.id for chunk in chunks]
        with vector_store.session_maker() as session:
            with session.begin():
                collection = vector_store.get_collection(session)
                if collection is None:
                    raise CvVectorSchemaError(
                        f"Collection '{self.collection_name}' was not initialized"
                    )
                collection_metadata = dict(collection.cmetadata or {})
                if collection_metadata.pop("user_profile", None) is not None:
                    collection.cmetadata = collection_metadata
                for chunk, embedding in zip(chunks, embeddings):
                    session.merge(
                        embedding_store(
                            id=chunk.id,
                            collection_id=collection.uuid,
                            embedding=list(embedding),
                            document=chunk.content,
                            cmetadata=dict(chunk.metadata),
                        )
                    )
                session.flush()
                session.execute(
                    delete(embedding_store).where(
                        embedding_store.collection_id == collection.uuid,
                        embedding_store.id.not_in(chunk_ids),
                    )
                )

        return len(chunks)
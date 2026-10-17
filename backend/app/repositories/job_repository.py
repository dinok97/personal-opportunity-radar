from collections.abc import Callable, Mapping
from typing import Any, Protocol

from langchain_core.documents import Document
from langchain_postgres import PGVectorStore

from ..services.embedding_service import HuggingFaceEmbeddingClient

from ..models.job import Job
from .database import Database
from ..helpers.constants import *


class JobRepository:
    table_name = JOBS_TABLE
    id_column_name = JOBS_TABLE_ID
    content_column = JOBS_TABLE_EMBEDDING_TEXT
    metadata_columns = [
        JOBS_TABLE_SOURCE,
        JOBS_TABLE_URL,
        JOBS_TABLE_TITLE,
        JOBS_TABLE_COMPANY,
        JOBS_TABLE_LOCATIONS,
        JOBS_TABLE_POSTED_AT,
        JOBS_TABLE_SPECIALIZATION,
        JOBS_TABLE_APPLICATION_DEADLINE_AT,
        JOBS_TABLE_EMPLOYMENT_TYPE,
        JOBS_TABLE_SKILLS,
        JOBS_TABLE_EXEC_SUMMARY,
        JOBS_TABLE_IS_ACTIVE,
        JOBS_TABLE_IS_DELETED,
        AUDIT_COLUMN_CREATED_AT,
        AUDIT_COLUMN_UPDATED_AT,
    ]

    def __init__(
        self,
        db: Database,
        embedding_service: HuggingFaceEmbeddingClient,
        *,
        vector_store_factory: Callable[..., PGVectorStore] = PGVectorStore.create_sync,
    ) -> None:
        self.db = db
        self.embedding_service = embedding_service
        self._vector_store_factory = vector_store_factory
        self._store: PGVectorStore | None = None

    @property
    def store(self) -> PGVectorStore:
        if self._store is None:
            self._store = self._vector_store_factory(
                engine=self.db.engine,
                table_name=self.table_name,
                embedding_service=self.embedding_service.model,
                id_column=self.id_column_name,
                content_column=self.content_column,
                embedding_column="embedding",
                metadata_columns=self.metadata_columns,
            )
        return self._store

    def get_job_by_id(self, job_id: str) -> Job | None:
        if not job_id:
            return None

        row = self.db.fetch_one(
            f"SELECT * FROM {self.table_name} WHERE {self.id_column_name} = %s",
            (job_id,),
        )
        if row is None:
            return None

        job_data = dict(row)
        job_data["external_id"] = job_data.pop(self.id_column_name)
        return Job.model_validate(job_data)

    def get_jobs_by_query(
        self,
        query: str,
        k: int,
    ) -> list[tuple[Document, float]]:
        filters = {
            "$and": [
                {"is_active": {"$eq": True}},
                {"is_deleted": {"$eq": False}},
            ]
        }
        return self.store.similarity_search_with_score(query=query, k=k, filter=filters)
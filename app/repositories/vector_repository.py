import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))

from repositories.base_repository import BaseRepository
from helpers.constants import (
    EMBEDDING_DIMENSION, 
    AUDIT_COLUMNS, 
    AUDIT_COLUMN_CREATED_AT, 
    AUDIT_COLUMN_UPDATED_AT)
from helpers.utils import get_datetime_utc
from repositories.database import Database
from services.embedding_service import EmbeddingService
from models.vector_record import VectorRecord

from typing import List
from langchain_postgres import PGVectorStore
from langchain_postgres.v2.engine import Column


class VectorRepository(BaseRepository):
    table_name: str
    id_column_name: str
    id_column_def: Column
    content_column: str
    metadata_columns: list[Column]


    def __init__(self, db: Database, embedding_service: EmbeddingService):
        super().__init__(db)
        self.embedding_service = embedding_service
        self.engine = db.engine
        self._store: PGVectorStore | None = None

    def setup(self, overwrite_existing: bool = False):
        self._execute(
            "CREATE EXTENSION IF NOT EXISTS vector;"
        )

        if self._table_exists() and not overwrite_existing:
            print(f"Table '{self.table_name}' already exists - skipping creation.")
            return

        self.engine.init_vectorstore_table(
            table_name=self.table_name,
            vector_size=EMBEDDING_DIMENSION,
            id_column=self.id_column_def,
            content_column=self.content_column,
            embedding_column="embedding",
            metadata_columns=self.all_metadata_columns,
            overwrite_existing=overwrite_existing,
        )
        print(f"Table '{self.table_name}' ready.")

    def _table_exists(self) -> bool:
            row = self._fetch_one(
                "SELECT to_regclass(%s) AS table_name;", 
                (self.table_name,)
            )
            return row is not None and row["table_name"] is not None

    def _drop_existing_table(self) -> bool:
        existed = self._table_exists()
        if existed:
            self._execute(f"DROP TABLE IF EXISTS {self.table_name};")
        return existed

    @property
    def all_metadata_columns(self) -> list[Column]:
        return [
            *self.metadata_columns,
            *AUDIT_COLUMNS
        ]


    @property
    def store(self) -> PGVectorStore:
        if self._store is None:
            self._store = PGVectorStore.create_sync(
                engine=self.engine,
                table_name=self.table_name,
                embedding_service=self.embedding_service.model,
                id_column=self.id_column_name,
                content_column=self.content_column,
                embedding_column="embedding",
                metadata_columns=[
                    c.name for c in self.all_metadata_columns
                ],
            )
        return self._store


    def upsert(self, items: List[VectorRecord]) -> List[str]:
        if not items:
            return []

        ids = [item.id for item in items]
        contents = [item.content for item in items]

        placeholders = ", ".join(["%s"] * len(ids))

        query = f"""SELECT {self.id_column_name}, 
                           {AUDIT_COLUMN_CREATED_AT} 
                    FROM {self.table_name} 
                    WHERE {self.id_column_name} IN ({placeholders});"""

        rows = self._fetch_all(query, tuple(ids))

        existing_created_at_map = {
            row[0]: row[1]
            for row in rows
        }

        now = get_datetime_utc()
        batch_metadatas = []

        for item in items:
            item_id = item.id

            if item_id in existing_created_at_map:
                audit = {
                    AUDIT_COLUMN_CREATED_AT: existing_created_at_map[item_id], 
                    AUDIT_COLUMN_UPDATED_AT: now
                }
            else:
                audit = {
                    AUDIT_COLUMN_CREATED_AT: now, 
                    AUDIT_COLUMN_UPDATED_AT: None
                }
            
            batch_metadatas.append({**item.metadata, **audit})

        result = self.store.add_texts(texts=contents, metadatas=batch_metadatas, ids=ids)
        return result


    def update_fields(self, row_id: str, fields: dict):
        if not fields:
            return

        fields["updated_at"] = get_datetime_utc()

        set_clause = ", ".join(f"{k} = %s" for k in fields)
        res = self._execute(
            f"""UPDATE {self.table_name} 
                SET {set_clause} 
                WHERE {self.id_column_name} = %s;""",
            (*fields.values(), row_id),
        )

        return res


    def get_all(self) -> list[dict]:
        cols = [
            self.id_column_name,
            self.content_column,
            *[c.name for c in self.metadata_columns],
        ]

        rows = self._fetch_all(f"""SELECT {', '.join(cols)} 
                                   FROM {self.table_name};""")
        
        return [dict(row) for row in rows]
    
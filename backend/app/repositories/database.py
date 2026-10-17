from functools import lru_cache
from typing import Any

from langchain_postgres.v2.engine import PGEngine
from sqlalchemy import create_engine

from ..config import get_settings


class Database:
    def __init__(self, connection_string: str) -> None:
        sqlalchemy_url = connection_string.replace(
            "postgresql://",
            "postgresql+psycopg://",
            1,
        )
        self.engine = PGEngine.from_connection_string(url=sqlalchemy_url)
        self._sql_engine = create_engine(sqlalchemy_url, pool_pre_ping=True)

    def execute(self, sql: str, params: tuple[Any, ...] = ()) -> int:
        with self._sql_engine.begin() as connection:
            result = connection.exec_driver_sql(sql, params)
            return result.rowcount

    def fetch_one(
        self,
        sql: str,
        params: tuple[Any, ...] = (),
    ) -> dict[str, Any] | None:
        with self._sql_engine.connect() as connection:
            row = connection.exec_driver_sql(sql, params).mappings().first()
            return dict(row) if row is not None else None

    def fetch_all(
        self,
        sql: str,
        params: tuple[Any, ...] = (),
    ) -> list[dict[str, Any]]:
        with self._sql_engine.connect() as connection:
            rows = connection.exec_driver_sql(sql, params).mappings().all()
            return [dict(row) for row in rows]

    def close(self) -> None:
        self._sql_engine.dispose()


@lru_cache(maxsize=1) # singleton, return same instance every call
def get_database() -> Database:
    connection_string = get_settings().pgvector_connection_string
    if not connection_string:
        raise ValueError("PGVECTOR_CONNECTION_STRING is not configured")
    return Database(connection_string)
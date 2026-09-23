from psycopg_pool import ConnectionPool
from langchain_postgres.v2.engine import PGEngine
from psycopg.rows import dict_row

class Database:
    def __init__(self, connection_string: str):
        self.pool = ConnectionPool(
            conninfo=connection_string,
            min_size=1,
            max_size=10,
        )

        lc_url = connection_string.replace(
            "postgresql://",
            "postgresql+psycopg://",
            1,
        )

        self.engine = PGEngine.from_connection_string(
            url=lc_url
        )

    def execute(self, sql: str, params: tuple = ()):
        with self.pool.connection() as conn:
            return conn.execute(sql, params)

    def fetch_one(self, sql: str, params: tuple = ()):
        with self.pool.connection() as conn:
            with conn.cursor(row_factory=dict_row) as cur:
                cur.execute(sql, params)
                return cur.fetchone()

    def fetch_all(self, sql: str, params: tuple = ()):
        with self.pool.connection() as conn:
            with conn.cursor(row_factory=dict_row) as cur:
                cur.execute(sql, params)
                return cur.fetchall()

    def close(self):
        self.pool.close()
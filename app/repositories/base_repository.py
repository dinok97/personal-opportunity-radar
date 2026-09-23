import sys
from dotenv import load_dotenv
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))

from repositories.database import Database

import asyncio
from typing import Optional

load_dotenv()

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

class BaseRepository:
    def __init__(self, db: Database):
        self.db = db
 
    def _execute(self, sql: str, params: tuple = ()):
        return self.db.execute(sql=sql, params=params)

    def _fetch_one(self, sql: str, params: tuple = ()) -> Optional[dict]:
        return self.db.fetch_one(sql=sql, params=params)
 
    def _fetch_all(self, sql: str, params: tuple = ()) -> list[dict]:
        return self.db.fetch_all(sql=sql, params=params)
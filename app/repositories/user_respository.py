import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))

from repositories.vector_repository import VectorRepository
from dto.vector_record import VectorRecord

from langchain_postgres.v2.engine import Column

from dto.user_job_pref import UserRolePreference
from helpers.constants import (
    USERS_TABLE,
    USERS_TABLE_ID
)


class UserRepository(VectorRepository):
    table_name = USERS_TABLE

    def get_active_profile(self) -> UserRolePreference | None:
        query = f"""SELECT *
                    FROM {USERS_TABLE}
                    ORDER BY {USERS_TABLE_ID}
                    LIMIT 1
                """
        
        row = self.db.fetch_one(query, ())

        if row:
            return UserRolePreference(target_roles=row['profile']['target_roles'])

        return None

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))

from repositories.vector_repository import VectorRepository
from dto.vector_record import VectorRecord

from langchain_postgres.v2.engine import Column

from models.user import Profile
from dto.user_job_pref import UserJobPreference
from helpers.constants import (
    USERS_TABLE,
    USERS_TABLE_ID,
    USERS_TABLE_FULLNAME,
    USERS_TABLE_TARGET_ROLES,
    USERS_TABLE_TECHNICAL_SKILLS,
    USERS_TABLE_EMPLOYMENT_TYPES,
    USERS_TABLE_CV,
    USERS_TABLE_IS_DELETED,
    AUDIT_COLUMN_CREATED_AT
)


class UserRepository(VectorRepository):
    table_name = USERS_TABLE
    id_column_name = USERS_TABLE_ID
    content_column = USERS_TABLE_CV
    id_column_def = Column(USERS_TABLE_ID, "TEXT")

    metadata_columns = [
        Column(name=USERS_TABLE_FULLNAME, data_type="TEXT"),
        Column(name=USERS_TABLE_TARGET_ROLES, data_type="TEXT"),
        Column(name=USERS_TABLE_TECHNICAL_SKILLS, data_type="TEXT"),
        Column(name=USERS_TABLE_EMPLOYMENT_TYPES, data_type="TEXT"),
        Column(name=USERS_TABLE_IS_DELETED, data_type="BOOLEAN")
    ]

    def save_profiles(self, profiles: list[Profile]) -> list[str]:
        batch_items: list[VectorRecord] = []
        
        for profile in profiles:
            vec_rec = VectorRecord(
                id=profile.id,
                content=profile.cv_text,
                metadata={
                    USERS_TABLE_FULLNAME: profile.full_name,
                    USERS_TABLE_TARGET_ROLES: profile.target_roles,
                    USERS_TABLE_TECHNICAL_SKILLS: profile.technical_skills,
                    USERS_TABLE_EMPLOYMENT_TYPES: profile.preferred_employment_types,
                    USERS_TABLE_IS_DELETED: profile.is_deleted
                }
            )
                
            batch_items.append(vec_rec)

        return self.upsert(batch_items)

    def get_job_search_parameters(self) ->UserJobPreference | None:
        query = f"""SELECT {USERS_TABLE_ID},
                           {USERS_TABLE_TARGET_ROLES},
                           {USERS_TABLE_EMPLOYMENT_TYPES}
                    FROM {USERS_TABLE}
                    WHERE {USERS_TABLE_IS_DELETED} = %s
                    ORDER BY {AUDIT_COLUMN_CREATED_AT} DESC
                    LIMIT 1
                """

        row = self.db.fetch_one(query, (False,))

        if row:
            user_job_pref = UserJobPreference(
                target_roles=row[USERS_TABLE_TARGET_ROLES],
                preferred_employment_types=row[USERS_TABLE_EMPLOYMENT_TYPES]
            )

            return user_job_pref

        return None



    def get_active_profile_ids(self) -> list[str]:
        query = f"""SELECT *
                    FROM {self.table_name} 
                    WHERE {USERS_TABLE_IS_DELETED} = %s"""
        
        rows = self.db.fetch_all(query, (False,))
        
        existing_ids = {row[self.id_column_name] for row in rows}

        return list(existing_ids)


    def deactivate_exiting_profiles(self, ids: list[str]):
        for id in ids:
            res = self.update_fields(id, {USERS_TABLE_IS_DELETED: True})
            print(res)

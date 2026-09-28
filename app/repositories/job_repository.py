import sys
from dotenv import load_dotenv
from pathlib import Path
from typing import List, Optional

sys.path.append(str(Path(__file__).resolve().parent.parent))

from repositories.vector_repository import VectorRepository
from models.vector_record import VectorRecord

from langchain_postgres.v2.engine import Column

from models.job import Job
from helpers.constants import (
    JOBS_TABLE,
    JOBS_TABLE_ID,
    JOBS_TABLE_SOURCE,
    JOBS_TABLE_URL,
    JOBS_TABLE_POSTED_AT,
    JOBS_TABLE_TITLE,
    JOBS_TABLE_COMPANY,
    JOBS_TABLE_LOCATIONS,
    JOBS_TABLE_SPECIALIZATION,
    JOBS_TABLE_EMPLOYMENT_TYPE,
    JOBS_TABLE_SENIORITY,
    JOBS_TABLE_WORK_MODE,
    JOBS_TABLE_INDUSTRY_DOMAIN,
    JOBS_TABLE_SKILLS,
    JOBS_TABLE_EDUCATION,
    JOBS_TABLE_EXPERIENCE,
    JOBS_TABLE_EXEC_SUMMARY,
    JOBS_TABLE_EMBEDDING_TEXT,
    JOBS_TABLE_IS_ACTIVE,
    JOBS_TABLE_IS_DELETED
)


class JobRepository(VectorRepository):
    table_name = JOBS_TABLE
    id_column_name = JOBS_TABLE_ID
    id_column_def = Column(JOBS_TABLE_ID, "TEXT")
    content_column = JOBS_TABLE_EMBEDDING_TEXT

    metadata_columns = [
        Column(name=JOBS_TABLE_SOURCE, data_type="TEXT"),
        Column(name=JOBS_TABLE_URL, data_type="TEXT"),
        Column(name=JOBS_TABLE_TITLE, data_type="TEXT"),
        Column(name=JOBS_TABLE_COMPANY, data_type="TEXT"),
        Column(name=JOBS_TABLE_LOCATIONS, data_type="TEXT"),
        Column(name=JOBS_TABLE_POSTED_AT, data_type="TIMESTAMPTZ"),
        Column(name=JOBS_TABLE_SPECIALIZATION, data_type="TEXT"),
        Column(name=JOBS_TABLE_EMPLOYMENT_TYPE, data_type="TEXT"),
        Column(name=JOBS_TABLE_SENIORITY, data_type="TEXT"),
        Column(name=JOBS_TABLE_WORK_MODE, data_type="TEXT"),
        Column(name=JOBS_TABLE_INDUSTRY_DOMAIN, data_type="TEXT"),
        Column(name=JOBS_TABLE_SKILLS, data_type="TEXT"),
        Column(name=JOBS_TABLE_EDUCATION, data_type="TEXT"),
        Column(name=JOBS_TABLE_EXPERIENCE, data_type="TEXT"),
        Column(name=JOBS_TABLE_EXEC_SUMMARY, data_type="TEXT"),
        Column(name=JOBS_TABLE_IS_ACTIVE, data_type="BOOLEAN"),
        Column(name=JOBS_TABLE_IS_DELETED, data_type="BOOLEAN"),
    ]


    def get_existing_ids(self, ids: list[str]) -> list[str]:
        if not ids:
            return []

        placeholders = ", ".join(["%s"] * len(ids))
        
        query = f"""SELECT {self.id_column_name} 
                    FROM {self.table_name} 
                    WHERE {self.id_column_name} IN ({placeholders})"""
        
        rows = self._fetch_all(query, tuple(ids))
        
        existing_ids = {row[self.id_column_name] for row in rows}

        return list(existing_ids)


    def save_jobs(self, jobs: list[Job]) -> list[str]:
        batch_items: List[VectorRecord] = []
        
        for job in jobs:
            vec_rec = VectorRecord(
                 id=job.external_id,
                 content=job.embedding_text,
                 metadata={
                    JOBS_TABLE_SOURCE: job.source,
                    JOBS_TABLE_URL: job.url,
                    JOBS_TABLE_POSTED_AT: job.posted_at,
                    JOBS_TABLE_TITLE: job.title,
                    JOBS_TABLE_COMPANY: job.company,
                    JOBS_TABLE_LOCATIONS: job.locations,
                    JOBS_TABLE_SPECIALIZATION: job.specialization,
                    JOBS_TABLE_EMPLOYMENT_TYPE: job.employment_type,
                    JOBS_TABLE_SENIORITY: job.seniority,
                    JOBS_TABLE_WORK_MODE: job.work_mode,
                    JOBS_TABLE_INDUSTRY_DOMAIN: job.industry_domain,
                    JOBS_TABLE_SKILLS: job.skills,
                    JOBS_TABLE_EDUCATION: job.education,
                    JOBS_TABLE_EXPERIENCE: job.experience,
                    JOBS_TABLE_EXEC_SUMMARY: job.executive_summary,
                    JOBS_TABLE_IS_ACTIVE: job.is_active,
                    JOBS_TABLE_IS_DELETED: job.is_deleted,
                }
            )
              
            batch_items.append(vec_rec)

        return self.upsert(batch_items)


    def get_job_by_id(self, id: str) -> Optional[Job]:
        if not len(id) > 0:
            return None
        
        query = f"""SELECT *
                    FROM {self.table_name} 
                    WHERE {self.id_column_name} = %s"""

        row = self._fetch_one(query, (id,))

        if row:        
            job = Job(
                source = row[JOBS_TABLE_SOURCE],
                external_id = row[JOBS_TABLE_ID],
                url = row[JOBS_TABLE_URL],
                title = row[JOBS_TABLE_TITLE],
                company = row[JOBS_TABLE_COMPANY],
                locations = row[JOBS_TABLE_LOCATIONS],
                posted_at = row[JOBS_TABLE_POSTED_AT],
                executive_summary = row[JOBS_TABLE_EXEC_SUMMARY],
                employment_type = row[JOBS_TABLE_EMPLOYMENT_TYPE],
                specialization = row[JOBS_TABLE_SPECIALIZATION],
                seniority = row [JOBS_TABLE_SENIORITY],
                work_mode = row[JOBS_TABLE_WORK_MODE],
                industry_domain = row[JOBS_TABLE_INDUSTRY_DOMAIN], 
                skills = row[JOBS_TABLE_SKILLS],
                education = row[JOBS_TABLE_EDUCATION],
                experience = row[JOBS_TABLE_EXPERIENCE],
                is_active = row[JOBS_TABLE_IS_ACTIVE],
                is_deleted = row[JOBS_TABLE_IS_DELETED],
            )

        return job or None


    def get_jobs_by_query(self, query: str, k: int):
        res = self.search_by_query(query, k)

        return res
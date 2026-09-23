from typing import Optional
from datetime import datetime

import sys
from dotenv import load_dotenv
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))

from repositories.structured_repository import StructuredRepository
from helpers.constants import (
    SEARCH_SCHEDULE_TABLE,
    SEARCH_SCHEDULE_TABLE_ID,
    SEARCH_SCHEDULE_TABLE_LAST_RUN_ON,
    SEARCH_SCHEDULE_TABLE_TOTAL_FOUND_JOBS,
    SEARCH_SCHEDULE_TABLE_TOTAL_UNSEEEN_JOBS,
    SEARCH_SCHEDULE_TABLE_TOTAL_SAVED_JOBS,
    SEARCH_SCHEDULE_TABLE_SAVED_JOBS_IDS
)
from models.search_schedule import SearchSchedule

class SearchScheduleRepository(StructuredRepository):
    table_name = SEARCH_SCHEDULE_TABLE
    id_column = SEARCH_SCHEDULE_TABLE_ID
    schema_sql = f"""
        {SEARCH_SCHEDULE_TABLE_ID} INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
        {SEARCH_SCHEDULE_TABLE_LAST_RUN_ON} TIMESTAMPTZ,
        {SEARCH_SCHEDULE_TABLE_TOTAL_FOUND_JOBS} INTEGER DEFAULT 0,
        {SEARCH_SCHEDULE_TABLE_TOTAL_UNSEEEN_JOBS} INTEGER DEFAULT 0,
        {SEARCH_SCHEDULE_TABLE_TOTAL_SAVED_JOBS} INTEGER DEFAULT 0,
        {SEARCH_SCHEDULE_TABLE_SAVED_JOBS_IDS} TEXT
    """

    def save_search_schedule(self, search_schedule: SearchSchedule):
        res = self.insert({
            SEARCH_SCHEDULE_TABLE_LAST_RUN_ON: search_schedule.last_ran_on,
            SEARCH_SCHEDULE_TABLE_TOTAL_FOUND_JOBS: search_schedule.total_found,
            SEARCH_SCHEDULE_TABLE_TOTAL_UNSEEEN_JOBS: search_schedule.total_unseen,
            SEARCH_SCHEDULE_TABLE_TOTAL_SAVED_JOBS: search_schedule.total_saved,
            SEARCH_SCHEDULE_TABLE_SAVED_JOBS_IDS: ", ".join(search_schedule.saved_job_ids)
        })

        return res

    def get_last_run_date(self) -> Optional[datetime]:
        res = self.get_latest_data()

        if res and res[SEARCH_SCHEDULE_TABLE_LAST_RUN_ON]:
            return res[SEARCH_SCHEDULE_TABLE_LAST_RUN_ON]

        return None
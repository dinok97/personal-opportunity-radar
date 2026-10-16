from datetime import datetime, timedelta

import sys 
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent.parent))

from configs.app_container import Container
from models.search_schedule import SearchScheduleRequest
from helpers.utils import format_datetime, get_datetime_local
from helpers.constants import MAX_LOOKBACK_DAYS, CHUNK_DAYS_DEFAULT
from configs.app_container import Container
from models.search_schedule import SearchSchedule


def chunk_windows_backward(start: datetime, end: datetime, chunk_days: int):
    windows = []
    window_end = end
    while window_end > start:
        chunk_start = max(window_end - timedelta(days=chunk_days), start)
        windows.append((format_datetime(chunk_start), format_datetime(window_end)))
        window_end = chunk_start

    windows.reverse()
    return windows


def get_schedule_timeline(chunk_days = CHUNK_DAYS_DEFAULT, 
                          max_lookback_days=MAX_LOOKBACK_DAYS) -> SearchScheduleRequest:

    last_run = Container.searchschedule_repository.get_last_run_date()
    now = get_datetime_local()

    earliest = now - timedelta(days=max_lookback_days)

    if last_run is None:
        start = earliest          
    else:
        start = max(earliest, last_run - timedelta(1))

    windows = chunk_windows_backward(start, now, chunk_days=chunk_days)
    return SearchScheduleRequest(date_windows=windows)


def save_search_schedule(total_found: int,
                         total_unseen: int,
                         total_saved: int,
                         saved_job_ids: list[str],
                         last_run: datetime = get_datetime_local()):

    Container.searchschedule_repository.save_search_schedule(
        SearchSchedule(
            last_ran_on=last_run,
            total_found=total_found,
            total_unseen=total_unseen,
            total_saved=total_saved,
            saved_job_ids=saved_job_ids)
    )
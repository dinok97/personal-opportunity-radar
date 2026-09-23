from datetime import datetime, timedelta
from typing import List

import sys 
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))

from configs.app_container import Container
from models.search_schedule import SearchScheduleRequest
from helpers.utils import get_datetime_utc, get_formatted_datetime
from helpers.constants import MAX_LOOKBACK_DAYS, CHUNK_DAYS_DEFAULT
from configs.app_container import Container
from models.search_schedule import SearchSchedule


def chunk_windows_backward(start: datetime, end: datetime, chunk_days: int):
    windows = []
    window_end  = end
    while window_end  > start:
        chunk_start = max(window_end - timedelta(days=chunk_days), start)
        windows.append((get_formatted_datetime(chunk_start), get_formatted_datetime(window_end)))
        window_end = chunk_start

    windows.reverse()
    return windows


def get_schedule_timeline(chunk_days = CHUNK_DAYS_DEFAULT, 
                          max_lookback_days=MAX_LOOKBACK_DAYS) -> SearchScheduleRequest:

    last_run = Container.searchschedule_repository.get_last_run_date()
    now = get_datetime_utc()

    if last_run is None:
        start = now - timedelta(days=max_lookback_days)
        windows = chunk_windows_backward(start, now, chunk_days=chunk_days)

        return SearchScheduleRequest(date_windows=windows)
        
    else:
        gap = now - last_run

        if gap <= timedelta(days=1):
            return SearchScheduleRequest(time_range="d")

        elif gap <= timedelta(days=7):
            padded_start = last_run - timedelta(days=1)
            windows = [(get_formatted_datetime(padded_start), get_formatted_datetime(now))]
            return SearchScheduleRequest(date_windows=windows)  

        else:
            windows = chunk_windows_backward(last_run, now, chunk_days=chunk_days)

            return SearchScheduleRequest(date_windows=windows)


def save_search_schedule(total_found: int,
                         total_unseen: int,
                         total_saved: int,
                         saved_job_ids: List[str],
                         last_run: datetime = get_datetime_utc()):

    Container.searchschedule_repository.save_search_schedule(
        SearchSchedule(
            last_ran_on=last_run,
            total_found=total_found,
            total_unseen=total_unseen,
            total_saved=total_saved,
            saved_job_ids=saved_job_ids)
    )
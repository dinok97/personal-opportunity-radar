
from datetime import date, timedelta, datetime
from zoneinfo import ZoneInfo

LOCAL_TZ = ZoneInfo("Europe/Stockholm")

def on_or_after(key: str, day: date) -> dict:
    return {key: {"$gte": day.isoformat()}}


def on_or_before(key: str, day: date) -> dict:
    return {key: {"$lt": (day + timedelta(days=1)).isoformat()}}


def date_conditions(key: str, direction: int, before, after, on) -> list[dict]:
    """direction -1: counted in days ago (posted). direction +1: counted in days from today (deadline)."""
    today = datetime.now(LOCAL_TZ).date()
    day = lambda n: today + timedelta(days=direction * abs(n))
    
    if on is not None:
        return [on_or_after(key, day(on)), on_or_before(key, day(on))]
    
    conditions = []
    if after is not None:
        conditions.append(on_or_after(key, day(after)))
    if before is not None:
        conditions.append(on_or_before(key, day(before)))
    return conditions
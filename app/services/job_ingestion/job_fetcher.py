import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent.parent))

from helpers.constants import (
    JOBTECH_SEARCH_URL,
    JOBTECH_SEARCH_AD,
    JOBTECH_REQUEST_HEADER,
    JOBTECH_REQUEST_TIMEOUT
)

import requests

def get_jobs(params: dict) -> list[dict]:
    try:
        response = requests.get(
            JOBTECH_SEARCH_URL,
            params=params,
            headers=JOBTECH_REQUEST_HEADER,
            timeout=JOBTECH_REQUEST_TIMEOUT,
        )
        response.raise_for_status()
        return response.json().get("hits", [])

    except Exception as e:
        print(f"Request failed: {e}")
        return []


def get_job(id: str) -> dict | None:
    try:
        response = requests.get(
            JOBTECH_SEARCH_URL,
            params={"q": f"{JOBTECH_SEARCH_AD}/{id}"},
            headers=JOBTECH_REQUEST_HEADER,
            timeout=JOBTECH_REQUEST_TIMEOUT,
        )
        response.raise_for_status()
        return response.json()

    except Exception as e:
        print(f"Request failed: {e}")
        return None
from urllib.parse import urlparse, urlunparse
import tldextract
import hashlib
from datetime import datetime, timezone
from typing import Optional
from zoneinfo import ZoneInfo
from helpers.constants import (
    JOBTECH_DATETIME_FORMAT, 
    IMAGE_MD_PATTERN, 
    LINK_MD_PATTERN, 
    BARE_URL_PATTERN
)
import uuid
import re

SWEDEN_TZ = ZoneInfo("Europe/Stockholm")

def get_datetime_local() -> datetime:
    return datetime.now(SWEDEN_TZ)

def format_datetime(dt, format=JOBTECH_DATETIME_FORMAT) -> str:
    if dt is None:
        return ""
    
    return dt.strftime(format)

def to_swedish_time(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        return dt.replace(tzinfo=SWEDEN_TZ)
    return dt.astimezone(SWEDEN_TZ)

def parse_datetime_isoformat(date_str: str) -> datetime:
    dt = datetime.fromisoformat(date_str.strip().replace("Z", "+00:00"))
    return to_swedish_time(dt)


def clean_text(text: str) -> str:
    for ch in ("\xa0", "\u202f"):                
        text = text.replace(ch, " ")
    for ch in ("\ufeff", "\u200b", "\xad"):       
        text = text.replace(ch, "")
    text = re.sub(r"[ \t]+", " ", text)           
    text = re.sub(r" *\n *", "\n", text)       
    text = re.sub(r"\n{3,}", "\n\n", text)      
    return text.strip()


def clean_content_links(text):
    text = IMAGE_MD_PATTERN.sub("", text)
    text = LINK_MD_PATTERN.sub("", text)  
    text = BARE_URL_PATTERN.sub("", text)

    return text


def get_hashed_id(canonical_id: str):
    return hashlib.sha256(canonical_id.encode()).hexdigest()[:16]


def get_uuid() -> str:
    return str(uuid.uuid4())
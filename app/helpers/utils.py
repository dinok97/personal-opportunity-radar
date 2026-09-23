from urllib.parse import urlparse, urlunparse
import tldextract
import hashlib
from datetime import datetime, timezone
from typing import Optional
from helpers.constants import IMAGE_MD_PATTERN, LINK_MD_PATTERN, BARE_URL_PATTERN, DATE_FORMAT_DEFAULT

def get_base_domain(url: str) -> str:
    extracted = tldextract.extract(url)
    return f"{extracted.domain}.{extracted.suffix}"

def normalize_url(url: str) -> str:
    parsed = urlparse(url)
    clean = parsed._replace(
        netloc=parsed.netloc.lower(),
        path=parsed.path.rstrip("/") or "/",
        params="",
        query="",
        fragment="",
    )
    return urlunparse(clean)

def get_hashed_id(canonical_id: str):
    return hashlib.sha256(canonical_id.encode()).hexdigest()[:16]


def get_datetime_utc():
    return datetime.now(timezone.utc)


def get_formatted_datetime(date: datetime, format=DATE_FORMAT_DEFAULT):
    if date is None:
        return ""
    
    return date.strftime(format)


def get_datetime_from_str_utc(date: str, format=DATE_FORMAT_DEFAULT) -> Optional[datetime]:
    if date is None:
        return None

    parsed = datetime.strptime(date, format)
    return parsed.replace(tzinfo=timezone.utc)

def clean_content_links(text):
    text = IMAGE_MD_PATTERN.sub("", text)
    text = LINK_MD_PATTERN.sub("", text)  
    text = BARE_URL_PATTERN.sub("", text)

    return text
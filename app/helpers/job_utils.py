import sys 
from pathlib import Path
import re

from typing import Optional

from models.job import Job
from dto.job_enrichment import JobDetails
from dto.job_ad import JobAd
from helpers.utils import parse_datetime_isoformat

sys.path.append(str(Path(__file__).resolve().parent.parent))

def clean_text(text: str) -> str:
    for ch in ("\xa0", "\u202f"):                
        text = text.replace(ch, " ")
    for ch in ("\ufeff", "\u200b", "\xad"):       
        text = text.replace(ch, "")
    text = re.sub(r"[ \t]+", " ", text)           
    text = re.sub(r" *\n *", "\n", text)       
    text = re.sub(r"\n{3,}", "\n\n", text)      
    return text.strip()

def format_role(name: str, abbreviation: Optional[str]) -> str:
    abbr = (abbreviation or "").strip()
    name_words = {w.lower() for w in name.split()}
    if abbr and abbr.lower() != name.lower() and abbr.lower() not in name_words:
        return f"{name} ({abbr})"
    return name


def isknown(value):
    return value if value and value != "Not specified" else None


MAX_DESC_CHARS = 8000

def build_embedding_text(job: Job) -> str:

    desc = (job.executive_summary or "").strip()[:MAX_DESC_CHARS]

    lines = [
        f"Title: {job.title}",
        f"Company: {job.company}",
        f"Specialization/Target Role: {job.specialization}" if isknown(job.specialization) else None,
        f"Employment type: {job.employment_type}" if isknown(job.employment_type) else None,
        f"Locations: {job.locations}" if isknown(job.locations) else None,
        f"Required Skills: {job.skills}" if isknown(job.skills) else None,
        f"Summary: {desc}" if isknown(desc) else None,
    ]

    return "\n".join(line for line in lines if line)


def to_job(ex_detail: JobDetails, job_ad: JobAd) -> Job | None:
    job = Job(
        title=ex_detail.title,
        company=job_ad.employer,
        source="JobTech",
        external_id=job_ad.id,
        url=job_ad.url,
        posted_at=parse_datetime_isoformat(job_ad.publication_date),
        application_deadline_at=parse_datetime_isoformat(job_ad.application_deadline),
        employment_type=ex_detail.employment_type,
        locations="; ".join(job_ad.cities) or "Sweden",
        specialization="; ".join(format_role(r.name, r.abbreviation) for r in ex_detail.job_fields),
        skills="; ".join(ex_detail.skills),
        executive_summary=job_ad.description
    )

    job.embedding_text = build_embedding_text(job)

    return job


def _rx(*terms: str) -> re.Pattern:
    return re.compile(r"\b(?:" + "|".join(terms) + r")\b", re.IGNORECASE)


TITLE_RULES = [
    ("PhD",        _rx(r"ph\.?d", r"doctoral", r"doktorand\w*", r"industridoktorand\w*")),
    ("Thesis",     _rx(r"thesis", r"examensarbete\w*", r"exjobb\w*", r"degree\s+project", r"masteruppsats\w*")),
    ("Internship", _rx(r"intern(?:ship)?s?", r"praktik\w*", r"trainee\w*")),
    ("Part-time",  _rx(r"part[\s-]?time", r"deltid\w*")),
    ("Contract",   _rx(r"postdoc\w*", r"fixed[\s-]term", r"visstid\w*", r"konsultuppdrag", r"contract(?:or)?")),
    ("Full-time",  _rx(r"full[\s-]?time", r"heltid\w*")),
]

DESC_SPECIFIC = [
    ("PhD",        _rx(r"ph\.?d\s+(?:student|position|candidate)", r"doctoral\s+(?:student|position)",
                       r"doktorand\w*", r"industridoktorand\w*")),
    ("Thesis",     _rx(r"master(?:['’]s)?\s+thesis", r"degree\s+project", r"examensarbete\w*", r"exjobb\w*")),
    ("Internship", _rx(r"internship", r"praktik(?:plats\w*|ant\w*)?", r"trainee\s+program(?:me)?")),
]

DESC_GENERIC = [
    ("Contract",   _rx(r"fixed[\s-]term", r"visstidsanställning\w*", r"tidsbegränsad\w*", r"konsultuppdrag")),
    ("Part-time",  _rx(r"part[\s-]?time", r"deltid\w*")),
    ("Full-time",  _rx(r"full[\s-]?time", r"heltid\w*", r"tillsvidareanställning\w*", r"permanent\s+position")),
]
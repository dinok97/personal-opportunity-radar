from pydantic import BaseModel, Field
from typing import Literal, Optional

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))

from helpers.constants import EMP_TYPES

EmploymentType = Literal[*EMP_TYPES]


class Term(BaseModel):
    name: str = Field(
        description="Full canonical field name in title case, e.g. 'Machine Learning'. "
                    "Never include the abbreviation here.")
    abbreviation: Optional[str] = Field(
        default=None,
        description='Standard abbreviation of the WHOLE name as job postings write it, e.g. '
                    '"ML" for Machine Learning, "NLP", "LLMs", "AI" for Artificial Intelligence. '
                    'Use null if the field has no standard abbreviation, if the name is already an '
                    'acronym, or if the abbreviation is one of the words in the name '
                    '(e.g. "Data Engineering", "MLOps", "Agentic AI" all get null). '
                    'Never give a part of the name as its abbreviation. Never invent one.'
    )


class JobDetails(BaseModel):
    title: str = Field(
        description="The job title in English, translated when the posting is in another language."
    )
    job_fields: list[Term] = Field(
        description=(
            'Up to 6 broad fields of work, one per item, most relevant first, in common '
            'job-board terms, e.g. "Machine Learning", "Large Language Models", '
            '"Data Engineering". When the main work is machine learning, large language '
            'models or agentic AI, include "Artificial Intelligence" (abbreviation "AI") '
            'as its own entry, first in the list.'
        )
    )
    employment_type: EmploymentType = Field(
        description=(
            "PhD for PhD student, doktorand, doktorandtjänst or industrial PhD (industridoktorand)"
            "Thesis for master thesis, examensarbete, exjobb or degree projects; "
            "Internship for internships, intern, praktik and trainee roles; "
            "Part-time for deltid or part-time; "
            "Contract for visstidsanställning or konsultuppdrag; "
            "Full-time when nothing else is stated."
        )
    )
    skills: list[str] = Field(
        description=(
            "Up to 10 concrete technical skills, tools and technologies a candidate would list "
            'on a CV, one per item, most relevant first, in English, e.g. "PyTorch", "Python", '
            '"reinforcement learning". More specific than the job fields.'
        )
    )


class JobEnrichment(BaseModel):
    is_relevant: bool = Field(
        description=(
            "True when the main work of the job fits one of the target roles. "
            "True as well when the posting is borderline or unclear."
        )
    )
    details: JobDetails | None = Field(
        description="The job details when is_relevant is true; null when is_relevant is false."
    )
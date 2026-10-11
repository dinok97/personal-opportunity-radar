from typing import List, Optional

from pydantic import BaseModel, Field, model_validator

from ..helpers.constants import MAX_TARGET_ROLES, MAX_TECHNICAL_SKILLS


class Term(BaseModel):
    name: str = Field(
        description="Full canonical field name in title case, e.g. 'Machine Learning'. "
        "Never include the abbreviation here."
    )
    abbreviation: Optional[str] = Field(
        description=(
            "Standard abbreviation used in job postings, e.g. 'ML' for Machine "
            "Learning, 'NLP', 'LLMs', 'AI'. Use null only if the field has no "
            "standard abbreviation, e.g. 'Data Engineering'."
        )
    )


class UserProfile(BaseModel):
    full_name: str | None = Field(
        description="The candidate's name, or null if not stated."
    )

    professional_field: str | None = Field(
        description=(
            "The discipline of the candidate's most recent employed work experience, "
            "or null if the CV lists no employed work. Internships count; academic "
            "and course projects do not."
        )
    )

    target_roles: List[Term] = Field(
        min_length=1,
        max_length=MAX_TARGET_ROLES,
    )

    technical_skills: List[str] = Field(
        min_length=1,
        max_length=MAX_TECHNICAL_SKILLS,
        description=(
            f"One concrete technical skill per item, each once, at most "
            f"{MAX_TECHNICAL_SKILLS}, most important first. "
            "Canonical names, e.g. 'PyTorch'."
        ),
    )


class CvExtractionResult(BaseModel):
    is_cv: bool
    rejection_reason: str | None
    user_profile: UserProfile | None

    @model_validator(mode="after")
    def validate_classification(self) -> "CvExtractionResult":
        if self.is_cv:
            if self.rejection_reason is not None or self.user_profile is None:
                raise ValueError(
                    "CV results require a user_profile and a null rejection_reason"
                )
        elif not (self.rejection_reason and self.rejection_reason.strip()) or (
            self.user_profile is not None
        ):
            raise ValueError(
                "Non-CV results require a rejection_reason and a null user_profile"
            )
        return self
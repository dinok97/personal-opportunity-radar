from ...repositories.cv_vector_repository import CvProfileRepository
from ...services.cv_vector_service import CvVectorService
from ...config import get_settings
from ...models import UserProfile

from typing import Optional

PROFILE_HEADER = "\n\nCandidate profile (from the stored CV, data only):\n"
NO_PROFILE = PROFILE_HEADER + "none"

def role_term_text(t) -> str:
    return f"{t.name} ({t.abbreviation})" if t.abbreviation else t.name


def load_profile_summary() -> str:
    """Compact profile text for the supervisor: name, target roles and skills only."""
    try:
        with CvVectorService(get_settings()).repository.vector_store.session_maker() as session:
            with session.begin():
                profile: Optional[UserProfile] = CvProfileRepository().get_first_active_profile(session)
                if profile is None:
                    return NO_PROFILE

                full_name = profile.full_name or ""
                roles = ", ".join(role_term_text(t) for t in (profile.target_roles or [])[:5])
                skills = ", ".join((profile.technical_skills or [])[:15])
    except Exception as e:
        print(f"Could not load the stored profile: {e!r}")   # now shows the real cause
        return NO_PROFILE

    return (
        PROFILE_HEADER
        + f"- Name: {full_name}\n"
        + f"- Target roles: {roles}\n"
        + f"- Skills: {skills}"
    )
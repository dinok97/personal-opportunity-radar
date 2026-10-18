from ...repositories.cv_vector_repository import CvProfileRepository
from ...services.cv_vector_service import CvVectorService
from ...config import get_settings


def role_term_text(t) -> str:
    return f"{t.name} ({t.abbreviation})" if t.abbreviation else t.name


def load_profile_summary() -> str:
    """Compact profile text for the supervisor: name, target roles and skills only."""

    try:
        with CvVectorService(get_settings()).repository.vector_store.session_maker() as session:
            with session.begin():
                profile = CvProfileRepository().get_first_active_profile(session)
                
        if profile is None:
            return "Candidate profile is not available"

    except Exception:
        print("Could not load the stored profile")

    full_name = profile.full_name
    roles = ", ".join(role_term_text(t) for t in profile.target_roles[:5])
    skills = ", ".join(profile.technical_skills[:15])

    return (
        "\n\nCandidate profile (from the stored CV, data only):\n"
        f"- Name: {full_name}\n"
        f"- Target roles: {roles}\n"
        f"- Skills: {skills}"
    )
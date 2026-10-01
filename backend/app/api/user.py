import logging

from fastapi import APIRouter, HTTPException
from sqlalchemy.exc import SQLAlchemyError

from ..config import get_settings
from ..models import UserProfile
from ..repositories.cv_vector_repository import (
    CvVectorConfigurationError,
    CvVectorRepository,
    CvVectorSchemaError,
)
from ..services.user_profile_service import (
    UserProfileExtractionError,
    UserProfileProviderError,
    UserProfileService,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api")


@router.get(
    "/user",
    response_model=UserProfile,
    responses={
        404: {"description": "No CV has been uploaded"},
        502: {"description": "The AI provider returned an invalid profile"},
        503: {"description": "CV storage or profile extraction is unavailable"},
    },
)
async def get_user_profile() -> UserProfile:
    settings = get_settings()
    repository = None
    try:
        repository = CvVectorRepository(settings)
        chunks = repository.get_active_cv_chunks()
    except (CvVectorConfigurationError, CvVectorSchemaError, SQLAlchemyError) as exc:
        logger.exception("Could not read the active CV")
        raise HTTPException(status_code=503, detail="CV storage is unavailable") from exc

    if not chunks:
        raise HTTPException(status_code=404, detail="No CV has been uploaded")

    try:
        profile = await UserProfileService(settings).extract_profile(chunks)
    except UserProfileProviderError as exc:
        logger.warning("Profile extraction provider failed: %s", exc.__cause__)
        raise HTTPException(
            status_code=503,
            detail="Profile extraction is unavailable",
        ) from exc
    except UserProfileExtractionError as exc:
        logger.warning("Profile extraction returned invalid data: %s", exc.__cause__)
        raise HTTPException(
            status_code=502,
            detail="The AI provider returned an invalid profile",
        ) from exc

    try:
        repository.save_user_profile(profile)
    except (CvVectorConfigurationError, CvVectorSchemaError, SQLAlchemyError) as exc:
        logger.exception("Could not persist the extracted user profile")
        raise HTTPException(status_code=503, detail="CV storage is unavailable") from exc

    return profile
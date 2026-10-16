import logging

from fastapi import APIRouter, HTTPException
from sqlalchemy.exc import SQLAlchemyError

from ..config import get_settings
from ..models import UserProfile
from ..repositories.cv_profile_repository import CvProfileRepository
from ..repositories.cv_vector_repository import CvVectorConfigurationError
from ..services.cv_vector_service import CvVectorService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api")


@router.get("/profile/{document_id}", response_model=UserProfile)
def get_profile(document_id: str) -> UserProfile:
    try:
        cv_service = CvVectorService(get_settings())
        with cv_service.repository.vector_store.session_maker() as session:
            profile = CvProfileRepository().get_active_profile(session, document_id)
    except (CvVectorConfigurationError, SQLAlchemyError) as exc:
        logger.exception("CV profile could not be retrieved")
        raise HTTPException(status_code=503, detail="CV storage is unavailable") from exc

    if profile is None:
        raise HTTPException(status_code=404, detail="Profile not found")
    return profile
from sqlalchemy import JSON, Column, MetaData, String, Table, delete, insert, select
from sqlalchemy.orm import Session
from sqlalchemy.schema import CreateTable

from ..models import UserProfile

_metadata = MetaData()
CV_PROFILE_TABLE = Table(
    "cv_profiles",
    _metadata,
    Column("document_id", String, primary_key=True),
    Column("profile", JSON, nullable=False),
)


class CvProfileRepository:
    def replace_active_profile(self, session, document_id: str, profile: UserProfile) -> None:
        session.execute(CreateTable(CV_PROFILE_TABLE, if_not_exists=True))
        session.execute(delete(CV_PROFILE_TABLE))
        session.execute(
            insert(CV_PROFILE_TABLE).values(
                document_id=document_id,
                profile=profile.model_dump(mode="json"),
            )
        )

    def get_active_profile(self, session: Session, document_id: str) -> UserProfile | None:
        session.execute(CreateTable(CV_PROFILE_TABLE, if_not_exists=True))
        profile_data = session.execute(
            select(CV_PROFILE_TABLE.c.profile).where(
                CV_PROFILE_TABLE.c.document_id == document_id
            )
        ).scalar_one_or_none()
        if profile_data is None:
            return None
        return UserProfile.model_validate(profile_data)
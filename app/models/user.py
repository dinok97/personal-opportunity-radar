from pydantic import BaseModel

class Profile(BaseModel):
    id: str
    full_name: str
    target_roles: str
    technical_skills: str
    preferred_employment_types: str 
    is_deleted: bool = False
    cv_text: str
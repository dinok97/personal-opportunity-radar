from pydantic import BaseModel

class UserJobPreference(BaseModel):
    target_roles: str
    preferred_employment_types: str
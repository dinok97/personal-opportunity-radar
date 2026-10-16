from pydantic import BaseModel


class Role(BaseModel):
    name: str
    abbreviation: str | None


class UserRolePreference(BaseModel):
    target_roles: list[Role] = []


class UserJobPreference(BaseModel):
    target_roles: list[str]
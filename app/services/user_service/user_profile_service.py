import os 
from pathlib import Path
import sys

sys.path.append(str(Path(__file__).resolve().parent.parent.parent))

from dto.user_job_pref import UserJobPreference, UserRolePreference
from configs.app_container import Container

def to_role(role_pref: UserRolePreference):

    roles: list[str] = []
    
    for target_role in role_pref.target_roles:
        
        desc = target_role.name

        if target_role.abbreviation and target_role.abbreviation not in (None, "null", ""):
            desc += f"({target_role.abbreviation})"

        roles.append(desc)

    return roles
        

def get_user_job_preference() -> UserJobPreference | None:
    user_role_pref = Container.user_repository.get_active_profile()

    if user_role_pref:
        return UserJobPreference(
            target_roles = to_role(user_role_pref)
        )

    return None


    

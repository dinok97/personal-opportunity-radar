import os 
from pathlib import Path
import sys

sys.path.append(str(Path(__file__).resolve().parent.parent.parent))

from dto.user_job_pref import UserJobPreference
from configs.app_container import Container

def get_user_job_preference() -> UserJobPreference | None:
    job_search_params = Container.user_repository.get_job_search_parameters()

    if not job_search_params:
        print("Job search params does not exist for profile")
        return None

    return job_search_params

    

import sys 
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))


from services.job_source_service import JobSourceService
from services.linkedin_job_source_service import LinkedInJobService
from helpers.utils import get_base_domain
from helpers.constants import LINKEDIN_DOMAIN

class JobSourceFactory:

    @staticmethod
    def create(url: str) -> JobSourceService:
        domain =  get_base_domain(url)

        if domain == LINKEDIN_DOMAIN:
            return LinkedInJobService()


        raise ValueError("Unsupported job source")

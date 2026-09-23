import re
from urllib.parse import urlparse

import sys 
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))

from services.job_source_service import JobSourceService
from helpers.constants import LINKEDIN_DOMAIN

class LinkedInJobService(JobSourceService):

    def __init__(self) -> None:
        super().__init__()

        self.footer_markers = re.compile(
            r"^[ \t]*(?:"
            r"Referenser fördubblar"                 # referral CTA (sv)
            r"|Få aviseringar om nya jobb"           # job alert prompt (sv)
            r"|##\s+Liknande jobb"                   # similar jobs (sv)
            r"|##\s+Andra har även besökt"           # people also viewed (sv)
            r"|Referrals increase your chances"      # en, verify on a real page
            r"|Get notified about new"               # en, verify
            r"|##\s+Similar jobs"                    # en
            r"|##\s+People also viewed"              # en
            r"|\*\s+LinkedIn©"                       # footer links
            r")",
            re.I | re.M,
        )

        self.des_end_marker = re.compile(r"\s*Show more\s+Show less\s*", re.I)

        self.id_marker = re.compile(r"(\d{6,})/?$")
    
    def clean_job_content(self, raw_content: str) -> str:
        text = raw_content or ""

        output: str = ""

        if (end_marker := self.des_end_marker.search(text)):
            output = text[:end_marker.start()].rstrip()

        elif (end_marker := self.footer_markers.search(text)):
            output = text[:end_marker.start()].rstrip()

        else:
            output = text.rstrip()

        return output


    def get_job_post_path(self) -> str:
        return "jobs/view"
    

    def get_source(self) -> str:
        return LINKEDIN_DOMAIN
    

    def get_canonical_id(self, url: str) -> str:
        match = self.id_marker.search(urlparse(url).path)     
        if not match:
            raise ValueError(f"No LinkedIn job ID in URL: {url}")

        job_id = match.group(1)
        canonical: str = f"linkedin.com/jobs/view/{job_id}"
        
        return canonical
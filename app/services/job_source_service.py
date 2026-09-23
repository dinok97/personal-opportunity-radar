from abc import ABC, abstractmethod


class JobSourceService(ABC):

    @abstractmethod
    def clean_job_content(self, raw_text: str) -> str:
        pass

    @abstractmethod
    def get_job_post_path(self) -> str:
        pass

    @abstractmethod
    def get_source(self) -> str:
        pass

    @abstractmethod
    def get_canonical_id(self, url: str) -> str:
        pass
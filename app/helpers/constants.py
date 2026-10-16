from langchain_postgres.v2.engine import Column
import re

EMP_TYPES = (
    "PhD",
    "Full-time",
    "Part-time",
    "Internship",
    "Thesis",
    "Contract",
)

JOBTECH_SEARCH_URL = "https://jobsearch.api.jobtechdev.se/search"
JOBTECH_SEARCH_AD = "https://jobsearch.api.jobtechdev.se/ad/"
JOBTECH_REQUEST_LIMIT=10
JOBTECH_REQUEST_TIMEOUT=20
JOBTECH_REQUEST_HEADER = { "accept": "application/json" }
JOBTECH_REQUEST_SORTING = "relevance"
JOBTECH_DATETIME_FORMAT = "%Y-%m-%dT%H:%M:%S"

EMPLOYMENT_TYPE_QUERIES = {
    "Thesis": ["master thesis", "exjobb", "examensarbete"],
    "Internship": ["intern", "praktik"],
    "PhD": ["phd", "doktorand"],
    "Part-time":  ["part time", "deltid"],
    "Contract":   ["contract", "fixed-term", "visstidsanställning"],
    "Full-time": []
}

MAX_TARGET_ROLES_ALLOWED=5

DATE_FORMAT_DEFAULT = "%Y-%m-%d"
MAX_LOOKBACK_DAYS = 14
CHUNK_DAYS_DEFAULT = 7

GROQ_WAIT_SECONDS = [15, 30, 60]
MAX_WAIT_SECONDS = 60
MAX_NUM_RETRIES=3
MAX_OUTPUT_TOKENS_JOB_SUMMARY=400

ALL_EMPLOYMENT_TYPES = ["Full-time"]

IMAGE_MD_PATTERN = re.compile(r"!\[[^\]]*\]\([^)]*\)")
LINK_MD_PATTERN = re.compile(r"\[[^\]]*\]\([^)]*\)")
BARE_URL_PATTERN = re.compile(r"https?://\S+")

QWEN_MODEL="qwen/qwen3.8-27b"
OLLAMA_MODEL="qwen3.5:4b"
QWEN_SKIP_REASONING="none"

EMBEDDING_MODEL="jinaai/jina-embeddings-v5-text-nano"
EMBEDDING_DIMENSION=768
EMBEDDING_MODEL_REVISION="8a7f00a"

MAX_RESULTS_RETRIVAL=20
MAX_RESULTS_RERANKED=10
RERANKING_MODEL="rerank-v3.5"

MAX_RAG_DECOMPOSED_SUB_QUERIES=3

SUPPORTED_EXTENSIONS = [".pdf"]
MAX_ACCEPTED_PAGES_FOR_CV = 5
RATE_LIMIT_WAIT_SECONDS = 60


AUDIT_COLUMN_CREATED_AT="created_at"
AUDIT_COLUMN_UPDATED_AT="updated_at"


AUDIT_COLUMNS = [
    Column(AUDIT_COLUMN_CREATED_AT, "TIMESTAMPTZ", nullable=False),
    Column(AUDIT_COLUMN_UPDATED_AT, "TIMESTAMPTZ", nullable=True),
]


AUDIT_COLUMNS_SQL = f"""created_at TIMESTAMPTZ NOT NULL, 
                        updated_at TIMESTAMPTZ"""



JOBS_TABLE="jobs"
JOBS_TABLE_ID = "jobs_id"
JOBS_TABLE_SOURCE = "source"
JOBS_TABLE_URL = "url"
JOBS_TABLE_POSTED_AT = "posted_at"
JOBS_TABLE_APPLICATION_DEADLINE_AT = "application_deadline_at"
JOBS_TABLE_TITLE = "title"
JOBS_TABLE_COMPANY = "company"
JOBS_TABLE_LOCATIONS = "locations"
JOBS_TABLE_SPECIALIZATION = "specialization"
JOBS_TABLE_EMPLOYMENT_TYPE = "employment_type"
JOBS_TABLE_SKILLS = "skills"
JOBS_TABLE_EXEC_SUMMARY = "executive_summary"
JOBS_TABLE_EMBEDDING_TEXT = "embedding_text"
JOBS_TABLE_IS_ACTIVE="is_active"
JOBS_TABLE_IS_DELETED="is_deleted"


SEARCH_SCHEDULE_TABLE="search_schedules"
SEARCH_SCHEDULE_TABLE_ID="search_schedules_id"
SEARCH_SCHEDULE_TABLE_LAST_RUN_ON="last_run_on"
SEARCH_SCHEDULE_TABLE_TOTAL_FOUND_JOBS="total_found_jobs"
SEARCH_SCHEDULE_TABLE_TOTAL_UNSEEEN_JOBS="total_unseen_jobs"
SEARCH_SCHEDULE_TABLE_TOTAL_SAVED_JOBS="total_saved_jobs"
SEARCH_SCHEDULE_TABLE_SAVED_JOBS_IDS="saved_jobs_ids"


USERS_TABLE="cv_profiles"
USERS_TABLE_PROFILE="profile"
USERS_TABLE_ID = "document_id"
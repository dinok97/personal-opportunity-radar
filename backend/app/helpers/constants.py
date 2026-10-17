MAX_TARGET_ROLES = 5
MAX_TECHNICAL_SKILLS = 30
JOB_RERANKER_MODEL = "cross-encoder/ms-marco-MiniLM-L6-v2"
CV_RERANKER_MODEL = JOB_RERANKER_MODEL

EMP_TYPES = (
    "PhD",
    "Full-time",
    "Part-time",
    "Internship",
    "Thesis",
    "Contract",
)

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

AUDIT_COLUMN_CREATED_AT="created_at"
AUDIT_COLUMN_UPDATED_AT="updated_at"
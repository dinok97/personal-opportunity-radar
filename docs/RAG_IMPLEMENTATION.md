# RAG / CV Retrieval Implementation -- Team Notes

## Overview

This document summarizes the changes made for the CV Retrieval / RAG
part of the project on the `retrieval/cv-retrieval` branch.

The main goal was to enable the backend to:

1.  Accept a user's CV as a PDF.
2.  Extract and chunk the CV text.
3.  Generate embeddings for the CV chunks.
4.  Store the embeddings in PGVector.
5.  Retrieve the most relevant CV chunks for a user's question using
    semantic search.
6.  Pass the retrieved CV context to the LLM together with the existing
    job-opportunity context.
7.  Keep the existing job retrieval flow unchanged.

The existing job/opportunity retrieval functionality was not newly
implemented in this work; the changes here mainly add CV semantic
retrieval and connect it to the existing chat flow.

------------------------------------------------------------------------

## Files Changed

### 1. `backend/app/repositories/cv_vector_repository.py`

### What was added

Added a `search()` method to the CV vector repository.

``` python
def search(
    self,
    query: str,
    *,
    k: int = 5,
):
    if not query.strip():
        raise ValueError("Query must not be empty")

    return self.vector_store.similarity_search(
        query,
        k=k,
    )
```

### Purpose

-   Accepts the user's query.
-   Validates that the query is not empty.
-   Uses the configured LangChain vector store to perform semantic
    similarity search.
-   Returns the top `k` relevant CV chunks.
-   Default retrieval size is `k=5`.

This is the main repository-level CV retrieval functionality.

------------------------------------------------------------------------

### 2. `backend/app/services/cv_vector_service.py`

### What was added

Added a service-level `search()` method:

``` python
def search(self, query: str, *, k: int = 5):
    if not query.strip():
        raise ValueError("Query must not be empty")
    return self.repository.search(query, k=k)
```

### Purpose

The service layer exposes CV semantic retrieval to the API layer while
keeping the repository interaction behind the service.

Flow:

``` text
Chat/API
   ↓
CvVectorService.search()
   ↓
CvVectorRepository.search()
   ↓
PGVector similarity search
```

------------------------------------------------------------------------

### 3. `backend/app/api/chat.py`

This is the main integration point.

### What was added

#### A. CV context formatter

Added `_cv_context()` to convert retrieved CV documents into text that
can be passed to the LLM.

``` python
def _cv_context(documents: list) -> str:
    return "\n".join(
        f"- {document.page_content}"
        for document in documents
    )
```

#### B. CV retrieval during chat

The chat endpoint now:

-   Creates/uses the CV vector service.
-   Stores the newly uploaded CV chunks.
-   Performs semantic search against the CV when there is a user query.
-   Retrieves the top 5 relevant CV chunks.

Conceptually:

``` text
User question
     ↓
CV semantic search
     ↓
Top 5 CV chunks
     ↓
CV context
```

#### C. Existing CV can be retrieved

The integration also supports retrieving from an already stored CV when
PGVector is configured, rather than requiring the CV to be uploaded
again for every chat request.

#### D. CV context is passed to the LLM

The LLM prompt/context now contains both:

``` text
CV CONTEXT:
<retrieved CV chunks>

OPPORTUNITY CONTEXT:
<existing job opportunities>
```

This allows the LLM to answer career questions using retrieved
information from the user's CV while still having access to the existing
opportunity information.

------------------------------------------------------------------------

### 4. `backend/app/ollama.py`

### What was changed

The Ollama client was updated during integration/debugging so that
Ollama request failures expose more useful error information.

The request payload also supports the Ollama request configuration used
during testing.

The important point for the team is that the Ollama client continues to
be the LLM-generation layer after CV retrieval.

The successful local end-to-end test used:

``` text
LLM provider: Ollama
Model: llama3.2
```

The exact model remains configurable through `.env` rather than being
hard-coded into the RAG retrieval code.

------------------------------------------------------------------------

## Test Files Changed

### 5. `backend/tests/test_cv_vector_repository.py`

### What was added

Updated the fake vector store used by the repository tests to support:

``` python
similarity_search()
```

Added tests covering:

-   Successful semantic CV search.
-   Empty-query validation.

This verifies that the repository correctly delegates retrieval to the
vector store.

------------------------------------------------------------------------

### 6. `backend/tests/test_cv_vector_service.py`

### What was added

Added service-level tests for `CvVectorService.search()`.

The tests verify:

-   A valid query is passed to the repository.
-   The requested `k` value is forwarded.
-   Empty queries are rejected.

------------------------------------------------------------------------

### 7. `backend/tests/test_chat.py`

### What was changed

Updated the chat test fixtures/mocks so the fake CV ingestion service
supports both:

``` text
replace_active_cv()
search()
```

Added coverage for the CV retrieval flow, including:

-   Uploading a CV and retrieving relevant CV documents.
-   Retrieving from an already stored CV without uploading the CV again.

This ensures the new retrieval functionality is integrated into the chat
endpoint without breaking the existing chat behavior.

------------------------------------------------------------------------

# End-to-End RAG Flow

The implemented flow is:

``` text
                    USER
                     │
                     │ CV + question
                     ▼
              `/api/chat`
                     │
                     ▼
              PDF extraction
                     │
                     ▼
                 Chunking
                     │
                     ▼
              Embedding model
                     │
                     ▼
                  PGVector
                     │
                     │ user query
                     ▼
          Semantic similarity search
                     │
                     ▼
              Top 5 CV chunks
                     │
                     ├─────────────────────┐
                     │                     │
                     ▼                     ▼
                CV Context          Job Context
                                      (existing)
                     │                     │
                     └──────────┬──────────┘
                                ▼
                              Ollama
                                │
                                ▼
                         Final chat response
```

------------------------------------------------------------------------

# Job Retrieval vs CV Retrieval

These are two separate parts of the project.

## Existing job retrieval

The chat flow already uses:

``` python
find_opportunities(clean_prompt or "all")
```

The returned opportunities are converted into job context and included
in the LLM flow.

Examples returned by the current API test included:

-   AI Research Intern
-   Machine Learning Engineer
-   Applied AI Engineer

This job retrieval functionality was already present in the project and
was not the main implementation added here.

## New CV retrieval

The new work adds:

``` text
CV → embeddings → PGVector → semantic search → retrieved CV context
```

Therefore, the main contribution of this branch is the CV semantic
retrieval/RAG layer and its integration into the existing chat flow.

------------------------------------------------------------------------

# Embedding vs LLM

These are separate models/components.

### CV embeddings

The project uses the configured Hugging Face embedding model:

``` text
jinaai/jina-embeddings-v5-text-nano
```

with the configured 768-dimensional vector space.

Its job is to convert CV text and queries into vectors for semantic
retrieval.

### LLM

Ollama is used for generating the final natural-language response.

The local successful test used:

``` text
llama3.2
```

The LLM model is controlled through the local `.env` configuration.

------------------------------------------------------------------------

# Database / PGVector Setup

The CV retrieval uses the configured PostgreSQL/PGVector connection.

The setup was tested successfully with:

``` text
PGVector setup OK
```

The local configuration detected a valid PGVector connection.

The CV ingestion test generated:

``` text
Generated 6 embeddings for 6 CV chunks.
```

------------------------------------------------------------------------

# End-to-End Test Result

A real `/api/chat` request was tested with a CV PDF and the question:

``` text
What experience do I have in NLP and machine learning?
```

The request returned:

``` text
HTTP 200 OK
```

The response included:

``` json
{
  "source": "ollama",
  "file_name": "CV_Stockholm_Part-times.pdf",
  "cv_uploaded": true
}
```

and also returned job opportunities.

This confirms that the CV ingestion, vector retrieval, LLM generation,
and existing job retrieval can work together through the chat endpoint.

------------------------------------------------------------------------

# Tests

The backend test suite was run after the retrieval implementation.

Result:

``` text
62 passed, 1 skipped
```

There was also a pytest-asyncio deprecation warning, but it did not
cause test failure.

------------------------------------------------------------------------

# Configuration Notes

The LLM configuration is local/environment-based.

Example:

``` env
LLM_PROVIDER=ollama
OLLAMA_MODEL=llama3.2
OLLAMA_BASE_URL=http://localhost:11434/v1
LLM_TIMEOUT_SECONDS=120
```

Do **not** commit the real `.env` file if it contains API keys or
database credentials.

For team sharing, use `.env.example` with placeholder values.

------------------------------------------------------------------------

# Summary of Contribution

### Added

-   CV semantic search at repository level.
-   CV semantic search at service level.
-   CV retrieval integration in `/api/chat`.
-   Retrieved CV context for the LLM.
-   Support for retrieval from an already stored CV.
-   Repository retrieval tests.
-   Service retrieval tests.
-   Chat integration tests.
-   Ollama debugging/error visibility needed during local integration
    testing.

### Kept Existing

-   PDF extraction/chunking pipeline.
-   CV embedding model.
-   Job/opportunity retrieval.
-   Existing job context generation.
-   Existing chat response structure.

------------------------------------------------------------------------

# Suggested Team Review Checklist

Before merging this branch:

-   [ ] Run backend tests.
-   [ ] Verify PGVector connection/configuration.
-   [ ] Verify Ollama/local LLM configuration.
-   [ ] Test `/api/chat` with a real CV.
-   [ ] Confirm CV chunks are retrieved for a relevant query.
-   [ ] Review the final `git diff`.
-   [ ] Make sure `.env` and secrets are not committed.
-   [ ] Merge `retrieval/cv-retrieval` into the team's target branch
    after review.

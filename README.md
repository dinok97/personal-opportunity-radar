# Personal Opportunity Radar

> An agentic AI system for personalized career opportunity discovery.

**Personal Opportunity Radar** is an AI-powered job-search application that helps users discover relevant internships, thesis projects, and job opportunities without manually checking multiple career websites every day.

Instead of searching for opportunities repeatedly, the system continuously monitors selected career sources, detects new job postings, and uses an LLM-based agent to evaluate their relevance to the user's background and interests.

---

## Prerequisites

Before running the project, create a `.env` file in the project root and add the following environment variables:

- TAVILY_API_KEY=your_tavily_api_key
- GROQ_API_KEY=your_groq_api_key
- DB_CONNECTION_STR=your_render_external_database_connection_string
- HF_TOKEN=your_huggingface_token


## Installation

**Step 1: Clone This Repository**

```bash
git clone git@github.com:dinok97/personal-opportunity-radar.git .
```

**Step 2: Create a Virtual Environment**

```bash
# Create a new virtual environment
python -m venv venv

# Activate virtual environment

# On macOS/Linux:
source venv/bin/activate

# On Windows:
venv\Scripts\activate
```

**Step 3: Install Dependencies**
```bash
uv add -r requirements.txt
```

### Run the Ingestion Pipeline

1. Open the notebook:
   `app/tests/test_job_ingestion.ipynb`

2. Select the Python kernel:
   - Click **Detect Kernel**
   - Select **Python Environments**
   - Choose the environment named **`career-lens (Python 3.12...)`** (If the kernel does not appear the first time, close and reopen Visual Studio Code and try again)


## Goals

The project focuses on three main capabilities:

1. **Personalized matching**
   Compare job requirements with the user's skills, experience, projects, and interests.

2. **Conversational job search**
   Allow users to search and explore opportunities through an AI assistant instead of traditional keyword-based search.

3. [OPTIONAL] **Continuous job discovery**
   Automatically collect and update job opportunities from selected career sources.

---

## Key Features

### CV-based User Profile

Users can upload their CV. An LLM extracts structured information such as:

* Skills
* Work experience
* Projects
* Interests
* Education
* Etc

The extracted profile can then be reviewed and corrected by the user.

### Agentic Job Search

The AI agent interprets the user's request and decides which tools and information are required.

Example:

```text
User
 │
 ↓
Agent
 │
 ├── search_jobs()
 │
 ├── get_user_profile()
 │
 └── get_job_details()
 │
 ↓
LLM
 │
 ↓
Personalized Results
```

### Retrieval-Augmented Generation

RAG is used to retrieve relevant information from both job descriptions and the user's background before generating a response.

The system can retrieve:

**Job knowledge**

* Job descriptions
* Requirements
* Skills
* Location
* Company information

**User knowledge**

* Work experience
* Projects
* Skills
* Education
* Interests

This allows the LLM to evaluate opportunities using relevant context rather than relying only on keyword matching.

### [OPTIONAL] Continuous Job Monitoring

A background scheduler periodically checks configured career sources and:

* Detects new jobs
* Detects changed jobs
* Marks unavailable jobs
* Updates the database
* Updates embeddings when necessary

### [OPTIONAL] Notifications

When a new opportunity matches the user's profile, the system can send a notification through a configured channel such as Telegram.

---

## 📚 Course Project

This project is developed as part of the **LLM Course — Group 26**.

The project demonstrates the integration of:

**LLM + RAG + Agentic AI + Tool Calling + Vector Search + Automated Data Pipelines**

---

## License

This project is developed for educational and research purposes.

from .models import JobMatch


PROFILE_SKILLS = ["Python", "Machine Learning", "NLP", "SQL", "LLMs", "Research"]

OPPORTUNITIES = [
    JobMatch(
        id="job-1",
        title="AI Research Intern",
        company="Northstar Labs",
        location="Berlin, Germany",
        salary="€1,800 / month",
        type="Internship",
        matchScore=94,
        description="Build evaluation pipelines for LLM and retrieval-augmented systems with researchers and product teams.",
        tags=["LLM", "Research", "Python", "NLP"],
        reasons=[
            "Strong overlap with your LLM and NLP background",
            "Your project work matches evaluation and experimentation",
            "Research-oriented role fits your interests",
        ],
        missingSkills=["MLOps deployment", "Federated learning"],
        source="LinkedIn",
    ),
    JobMatch(
        id="job-2",
        title="Machine Learning Engineer",
        company="Aster Data",
        location="Remote",
        salary="€78k - €96k",
        type="Full-time",
        matchScore=89,
        description="Design and ship production ML systems for recommendation and forecasting products.",
        tags=["ML", "Python", "SQL", "Analytics"],
        reasons=[
            "Strong technical match in Python and ML workflows",
            "Your experience aligns with product-relevant ML systems",
            "SQL and experimentation skills are a clear fit",
        ],
        missingSkills=["Distributed training", "Spark"],
        source="Wellfound",
    ),
    JobMatch(
        id="job-3",
        title="Applied AI Engineer",
        company="VentureDock",
        location="Hamburg, Germany",
        salary="€70k - €85k",
        type="Full-time",
        matchScore=84,
        description="Work on AI-powered workflows by integrating LLMs and internal data tools into product experiences.",
        tags=["AI", "LLM", "Product", "Backend"],
        reasons=[
            "Strong alignment with AI product and LLM work",
            "Your background matches applied AI problem solving",
            "Good fit for product-driven AI roles",
        ],
        missingSkills=["FastAPI experience", "Cloud deployment"],
        source="Job Board",
    ),
    JobMatch(
        id="job-4",
        title="Data Scientist - NLP",
        company="TextHorizon",
        location="Munich, Germany",
        salary="€68k - €82k",
        type="Full-time",
        matchScore=81,
        description="Develop NLP models for customer support workflows and partner with engineering to deploy capabilities.",
        tags=["NLP", "Python", "Modeling", "Research"],
        reasons=[
            "NLP focus is highly relevant to your profile",
            "Model evaluation work is a good fit",
            "Your interests align with applied language AI",
        ],
        missingSkills=["Computer vision", "A/B test design"],
        source="Greenhouse",
    ),
]


def find_opportunities(prompt: str) -> list[JobMatch]:
    query = prompt.lower().strip()
    if not query or query == "all":
        return OPPORTUNITIES[:3]

    def matches(job: JobMatch) -> bool:
        haystack = " ".join(
            [job.title, job.company, job.location, job.description, *job.tags]
        ).lower()
        if "intern" in query:
            return "intern" in job.type.lower()
        if "remote" in query:
            return "remote" in job.location.lower()
        if "llm" in query or "ai" in query:
            return "llm" in haystack or "ai" in haystack or "nlp" in haystack
        if "python" in query:
            return "python" in haystack
        if "ml" in query:
            return "ml" in haystack or "machine learning" in haystack
        return query in haystack or any(query in tag.lower() for tag in job.tags)

    selected = [job for job in OPPORTUNITIES if matches(job)]
    return (selected or OPPORTUNITIES)[:3]

export type JobMatch = {
  id: string;
  title: string;
  company: string;
  location: string;
  salary: string;
  type: string;
  matchScore: number;
  description: string;
  tags: string[];
  reasons: string[];
  missingSkills: string[];
  source: string;
};

export const userProfile = {
  name: "Alicia Morgan",
  role: "ML Engineer",
  email: "alicia@careerflow.ai",
  location: "Berlin, Germany",
  availability: "Open to internships and full-time",
  topSkills: ["Python", "Machine Learning", "NLP", "SQL", "LLMs", "Research"],
  interests: ["AI products", "LLM systems", "Data science", "Career growth"],
  profileSummary:
    "ML engineer with experience in NLP, experimentation, and applied AI systems. Looking for roles that combine research, product thinking, and strong engineering execution.",
};

export const jobMatches: JobMatch[] = [
  {
    id: "job-1",
    title: "AI Research Intern",
    company: "Northstar Labs",
    location: "Berlin, Germany",
    salary: "€1,800 / month",
    type: "Internship",
    matchScore: 94,
    description:
      "Build evaluation pipelines for LLM and retrieval-augmented systems. Work with researchers and product teams to improve the quality of AI experiences.",
    tags: ["LLM", "Research", "Python", "NLP"],
    reasons: [
      "Strong overlap with your LLM and NLP background",
      "Your project work matches evaluation and experimentation",
      "Research-oriented role fits your interests",
    ],
    missingSkills: ["MLOps deployment", "Federated learning"],
    source: "LinkedIn",
  },
  {
    id: "job-2",
    title: "Machine Learning Engineer",
    company: "Aster Data",
    location: "Remote",
    salary: "€78k - €96k",
    type: "Full-time",
    matchScore: 89,
    description:
      "Design and ship production ML systems for recommendation and forecasting products. Partner with product and backend engineers on real-world ML features.",
    tags: ["ML", "Python", "SQL", "Analytics"],
    reasons: [
      "Strong technical match in Python and ML workflows",
      "Your experience aligns with product-relevant ML systems",
      "SQL and experimentation skills are a clear fit",
    ],
    missingSkills: ["Distributed training", "Spark"],
    source: "Wellfound",
  },
  {
    id: "job-3",
    title: "Applied AI Engineer",
    company: "VentureDock",
    location: "Hamburg, Germany",
    salary: "€70k - €85k",
    type: "Full-time",
    matchScore: 84,
    description:
      "Work on AI-powered workflows for enterprise clients, integrating LLMs and internal data tools into product experiences.",
    tags: ["AI", "LLM", "Product", "Backend"],
    reasons: [
      "Strong alignment with AI product and LLM work",
      "Your background matches applied AI problem solving",
      "Good fit for product-driven AI roles",
    ],
    missingSkills: ["FastAPI experience", "Cloud deployment"],
    source: "Job Board",
  },
  {
    id: "job-4",
    title: "Data Scientist - NLP",
    company: "TextHorizon",
    location: "Munich, Germany",
    salary: "€68k - €82k",
    type: "Full-time",
    matchScore: 81,
    description:
      "Develop NLP models for customer support workflows, analyze performance, and partner with engineering to deploy new capabilities.",
    tags: ["NLP", "Python", "Modeling", "Research"],
    reasons: [
      "NLP focus is highly relevant to your profile",
      "Model evaluation work is a good fit",
      "Your interests align with applied language AI",
    ],
    missingSkills: ["Computer vision", "A/B test design"],
    source: "Greenhouse",
  },
];

export function createMockResponse(prompt: string) {
  const query = prompt.toLowerCase();

  const filteredJobs = jobMatches.filter((job) => {
    const haystack = `${job.title} ${job.company} ${job.description} ${job.tags.join(" ")}`.toLowerCase();
    if (!query || query === "all") return true;

    if (query.includes("intern")) return job.type.toLowerCase().includes("intern");
    if (query.includes("remote")) return job.location.toLowerCase().includes("remote");
    if (query.includes("llm") || query.includes("ai")) {
      return haystack.includes("llm") || haystack.includes("ai") || haystack.includes("nlp");
    }
    if (query.includes("python")) return haystack.includes("python");
    if (query.includes("ml")) return haystack.includes("ml") || haystack.includes("machine learning");

    return haystack.includes(query) || job.tags.some((tag) => tag.toLowerCase().includes(query));
  });

  const selectedJobs = filteredJobs.length > 0 ? filteredJobs : jobMatches;

  return {
    message:
      `I checked your profile and the latest opportunities. I found ${selectedJobs.length} promising matches that align with your background in ${userProfile.topSkills.slice(0, 3).join(", ")}.`,
    jobs: selectedJobs.slice(0, 3),
  };
}

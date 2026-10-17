"use client";

import { useEffect, useRef, useState, useSyncExternalStore } from "react";
import type { JobMatch } from "@/lib/mock-data";

type UserProfile = {
  full_name: string | null;
  email: string | null;
  location: string | null;
  professional_field: string | null;
  target_roles: { name: string; abbreviation: string | null }[];
  technical_skills: string[];
};

type BackendJobSearchResult = {
  job: {
    external_id: string;
    title: string;
    company: string;
    source: string;
    locations: string;
    employment_type: string | null;
    skills: string;
    executive_summary: string;
    embedding_text: string;
  };
  score: number;
};

type DashboardJob = {
  id: string;
  title: string;
  company: string;
  location: string | null;
  type: string | null;
  salary: string | null;
  matchScore: number | null;
  relevanceScore: number | null;
  description: string;
  tags: string[];
  reasons: string[];
  missingSkills: string[];
  source: string;
};

type ChatMessage = {
  id: string;
  role: "user" | "assistant";
  content: string;
  jobs?: DashboardJob[];
};

type ChatApiResponse = {
  message?: string;
  jobs?: Array<BackendJobSearchResult | JobMatch>;
  detail?: string;
  cv_uploaded?: boolean;
  document_id?: string | null;
};

const PROFILE_DOCUMENT_KEY = "opportunity-radar-profile-document-id";
const PROFILE_DOCUMENT_EVENT = "profile-document-updated";

function toDashboardJob(result: BackendJobSearchResult | JobMatch): DashboardJob {
  if ("job" in result) {
    const job = result.job;
    return {
      id: job.external_id,
      title: job.title,
      company: job.company,
      location: job.locations || null,
      type: job.employment_type,
      salary: null,
      matchScore: null,
      relevanceScore: result.score,
      description: job.executive_summary || job.embedding_text,
      tags: job.skills.split(/[,;\n]/).map((skill) => skill.trim()).filter(Boolean),
      reasons: [],
      missingSkills: [],
      source: job.source,
    };
  }

  return {
    id: result.id,
    title: result.title,
    company: result.company,
    location: result.location,
    type: result.type,
    salary: result.salary,
    matchScore: result.matchScore,
    relevanceScore: null,
    description: result.description,
    tags: result.tags,
    reasons: result.reasons,
    missingSkills: result.missingSkills,
    source: result.source,
  };
}

function subscribeToProfileDocument(onChange: () => void) {
  window.addEventListener("storage", onChange);
  window.addEventListener(PROFILE_DOCUMENT_EVENT, onChange);
  return () => {
    window.removeEventListener("storage", onChange);
    window.removeEventListener(PROFILE_DOCUMENT_EVENT, onChange);
  };
}

function getProfileDocumentId() {
  return window.localStorage.getItem(PROFILE_DOCUMENT_KEY);
}

export function AICareerDashboard() {
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      id: "welcome",
      role: "assistant",
      content:
        "Hi! Upload your CV to build your profile and find relevant opportunities, or ask me about roles you have in mind.",
    },
  ]);
  const [draft, setDraft] = useState("");
  const [selectedJob, setSelectedJob] = useState<DashboardJob | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [isUploadingCv, setIsUploadingCv] = useState(false);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [fileError, setFileError] = useState("");
  const [activeTab, setActiveTab] = useState<"dashboard" | "profile">("dashboard");
  const profileDocumentId = useSyncExternalStore(
    subscribeToProfileDocument,
    getProfileDocumentId,
    () => null,
  );
  const [profile, setProfile] = useState<{ documentId: string; data: UserProfile } | null>(null);
  const [profileLoad, setProfileLoad] = useState<{
    documentId: string;
    status: "ready" | "error";
  } | null>(null);
  const fileInputRef = useRef<HTMLInputElement | null>(null);
  const chatContainerRef = useRef<HTMLDivElement | null>(null);
  const messageIdRef = useRef(0);

  const nextMessageId = (role: ChatMessage["role"]) => {
    messageIdRef.current += 1;
    return `${role}-${messageIdRef.current}`;
  };

  useEffect(() => {
    if (chatContainerRef.current) {
      chatContainerRef.current.scrollTop = chatContainerRef.current.scrollHeight;
    }
  }, [messages, isLoading]);

  useEffect(() => {
    if (!profileDocumentId) return;

    let isCurrentRequest = true;

    fetch(`/api/profile/${encodeURIComponent(profileDocumentId)}`, { cache: "no-store" })
      .then(async (response) => {
        if (response.status === 404) {
          window.localStorage.removeItem(PROFILE_DOCUMENT_KEY);
          if (isCurrentRequest) {
            setProfile(null);
            window.dispatchEvent(new Event(PROFILE_DOCUMENT_EVENT));
          }
          return;
        }
        if (!response.ok) throw new Error("Profile service is unavailable.");
        return (await response.json()) as UserProfile;
      })
      .then((data) => {
        if (isCurrentRequest && data) {
          setProfile({ documentId: profileDocumentId, data });
          setProfileLoad({ documentId: profileDocumentId, status: "ready" });
        }
      })
      .catch(() => {
        if (isCurrentRequest) setProfileLoad({ documentId: profileDocumentId, status: "error" });
      });

    return () => {
      isCurrentRequest = false;
    };
  }, [profileDocumentId]);

  const profileStatus = !profileDocumentId
    ? "empty"
    : profileLoad?.documentId === profileDocumentId
      ? profileLoad.status
      : "loading";
  const currentProfile = profile?.documentId === profileDocumentId ? profile.data : null;

  const validatePdfFile = (file: File | null) => {
    if (!file) return true;

    const isPdf = file.type === "application/pdf" || file.name.toLowerCase().endsWith(".pdf");
    if (!isPdf) {
      setFileError("Only PDF files are supported for upload.");
      return false;
    }

    setFileError("");
    return true;
  };

  const handleFileChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0] ?? null;
    if (!validatePdfFile(file)) {
      event.target.value = "";
      return;
    }

    setSelectedFile(file);
  };

  async function sendPrompt(promptOverride?: string) {
    const cleanPrompt = (promptOverride ?? draft).trim();
    const fileToSend = selectedFile;
    if (!cleanPrompt && !fileToSend) return;

    if (fileToSend && !validatePdfFile(fileToSend)) {
      return;
    }

    const userMessage: ChatMessage = {
      id: nextMessageId("user"),
      role: "user",
      content: fileToSend ? `Attached PDF: ${fileToSend.name}${cleanPrompt ? `\n\n${cleanPrompt}` : ""}` : cleanPrompt,
    };
    const requestMessages = [...messages, userMessage];

    setMessages((prev) => [...prev, userMessage]);
    setDraft("");
    setSelectedFile(null);
    setFileError("");
    if (fileInputRef.current) {
      fileInputRef.current.value = "";
    }
    setIsUploadingCv(Boolean(fileToSend));
    setIsLoading(true);

    try {
      let response;

      if (fileToSend) {
        const formData = new FormData();
        formData.append("prompt", cleanPrompt || "Review my uploaded CV and suggest relevant opportunities.");
        formData.append("messages", JSON.stringify(requestMessages));
        formData.append("file", fileToSend);

        response = await fetch("/api/chat", {
          method: "POST",
          body: formData,
        });
      } else {
        response = await fetch("/api/chat", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            prompt: cleanPrompt,
            messages: requestMessages,
          }),
        });
      }

      const data = (await response.json()) as ChatApiResponse;
      if (!response.ok) {
        throw new Error(data.detail || data.message || "The chat service is unavailable.");
      }
      if (fileToSend && (data.cv_uploaded !== true || !data.document_id)) {
        throw new Error("The backend did not confirm that this CV was stored. Please try again.");
      }
      if (fileToSend && data.document_id) {
        window.localStorage.setItem(PROFILE_DOCUMENT_KEY, data.document_id);
        setProfile(null);
        setProfileLoad(null);
        window.dispatchEvent(new Event(PROFILE_DOCUMENT_EVENT));
      }

      const assistantMessage: ChatMessage = {
        id: nextMessageId("assistant"),
        role: "assistant",
        content:
          data.message ||
          "I found a few great opportunities for you. I can narrow them by remote, type, or required skills.",
        jobs: data.jobs?.map(toDashboardJob) ?? [],
      };

      setMessages((prev) => [...prev, assistantMessage]);
      if (data.jobs?.length) {
        setSelectedJob(toDashboardJob(data.jobs[0]));
      }
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : "The chat service is unavailable.";
      if (fileToSend) {
        setSelectedFile(fileToSend);
      }
      setMessages((prev) => [
        ...prev,
        {
          id: nextMessageId("assistant"),
          role: "assistant",
          content: errorMessage,
        },
      ]);
    } finally {
      setIsUploadingCv(false);
      setIsLoading(false);
    }
  }

  const quickPrompts = [
    "Find me remote ML jobs",
    "Show AI internships in Berlin",
    "Compare me with LLM roles",
  ];

  return (
    <div className="min-h-screen bg-[#f5f5f7] text-[#111827]">
      <div className="mx-auto flex h-screen max-w-[1600px] gap-4 p-4">
        <aside className="hidden w-[220px] shrink-0 rounded-[28px] border border-[#e5e7eb] bg-white/90 p-4 shadow-[0_1px_2px_rgba(17,24,39,0.04)] backdrop-blur-sm lg:block">
          <div className="mb-8 flex items-center gap-3">
            <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-[#111827] text-sm font-semibold text-white">
              P
            </div>
            <div>
              <p className="text-[10px] font-semibold uppercase tracking-[0.22em] text-slate-400">Radar</p>
              <h1 className="text-base font-semibold text-slate-900">Opportunity</h1>
            </div>
          </div>

          <nav className="space-y-1.5">
            {[
              { label: "Dashboard", tab: "dashboard" as const },
              { label: "My profile", tab: "profile" as const },
              { label: "Matches" },
              { label: "Saved jobs" },
            ].map((item) => (
              <button
                key={item.label}
                onClick={() => item.tab && setActiveTab(item.tab)}
                className={`flex w-full items-center justify-between rounded-xl px-3 py-2 text-left text-sm transition ${
                  item.tab === activeTab ? "bg-[#f3f4f6] font-medium text-slate-900" : "text-slate-600 hover:bg-slate-50"
                }`}
              >
                <span>{item.label}</span>
                {item.tab === activeTab && <span className="rounded-full bg-[#ecfdf5] px-2 py-0.5 text-[10px] text-[#166534]">Live</span>}
              </button>
            ))}
          </nav>

          <div className="mt-8 rounded-2xl border border-[#e5e7eb] bg-[#f8fafc] p-4">
            <p className="text-[10px] font-semibold uppercase tracking-[0.2em] text-slate-400">Profile</p>
            <div className="mt-4 flex items-center gap-3">
              <div className="flex h-10 w-10 items-center justify-center rounded-full bg-[#e5e7eb] text-xs font-semibold text-slate-700">
                {currentProfile?.full_name?.split(/\s+/).map((part) => part[0]).join("").slice(0, 2).toUpperCase() || "CV"}
              </div>
              <div>
                <p className="text-sm font-medium text-slate-900">
                  {currentProfile?.full_name || "No CV uploaded"}
                </p>
                <p className="text-xs text-slate-500">{currentProfile?.professional_field || "No user profile"}</p>
              </div>
            </div>
            <div className="mt-4 flex flex-wrap gap-2">
              {currentProfile?.technical_skills.slice(0, 4).map((skill) => (
                <span key={skill} className="rounded-full border border-[#e5e7eb] bg-white px-2 py-1 text-[10px] text-slate-600">
                  {skill}
                </span>
              ))}
            </div>
          </div>
        </aside>

        <main className="flex flex-1 flex-col overflow-hidden rounded-[28px] border border-[#e5e7eb] bg-white shadow-[0_1px_2px_rgba(17,24,39,0.04)]">
          <header className="flex items-center justify-between border-b border-[#f1f5f9] px-5 py-4 md:px-7">
            <div>
              <p className="text-[10px] font-semibold uppercase tracking-[0.2em] text-slate-400">Career Copilot</p>
              <h2 className="mt-1 text-lg font-semibold text-slate-900 md:text-xl">
                {activeTab === "profile" ? "My profile" : "AI job discovery"}
              </h2>
            </div>
            <div className="flex rounded-lg border border-[#e5e7eb] bg-[#f8fafc] p-1" role="tablist" aria-label="Dashboard view">
              {(["dashboard", "profile"] as const).map((tab) => (
                <button
                  key={tab}
                  type="button"
                  role="tab"
                  aria-selected={activeTab === tab}
                  onClick={() => setActiveTab(tab)}
                  className={`rounded-md px-3 py-1.5 text-xs font-medium capitalize transition ${
                    activeTab === tab ? "bg-white text-slate-900 shadow-sm" : "text-slate-500 hover:text-slate-800"
                  }`}
                >
                  {tab === "dashboard" ? "Discover" : "Profile"}
                </button>
              ))}
            </div>
          </header>

          <section className={`${activeTab === "profile" ? "flex" : "hidden"} flex-1 overflow-y-auto px-5 py-6 md:px-8 md:py-8`}>
            <div className="mx-auto w-full max-w-3xl">
              {profileStatus === "loading" && (
                <p className="text-sm text-slate-500">Loading your profile...</p>
              )}
                  {profileStatus === "empty" && (
                <div className="border-l-4 border-[#d97706] bg-[#fffbeb] px-5 py-4">
                  <h3 className="text-base font-semibold text-slate-900">No user profile</h3>
                  <p className="mt-1 text-sm text-slate-600">Your CV hasn&apos;t been uploaded yet. Upload a CV in the dashboard to build your profile.</p>
                </div>
              )}
              {profileStatus === "error" && (
                <p role="alert" className="text-sm text-red-700">Your profile couldn&apos;t be loaded. Check that the backend is available, then try again.</p>
              )}
              {profileStatus === "ready" && currentProfile && (
                <div className="space-y-8">
                  <div className="border-b border-[#e5e7eb] pb-5">
                    <p className="text-xs font-semibold uppercase tracking-[0.16em] text-slate-500">CV profile</p>
                    <h3 className="mt-2 text-2xl font-semibold text-slate-900">{currentProfile.full_name || "Name not listed"}</h3>
                    <p className="mt-1 text-sm text-slate-600">{currentProfile.professional_field || "Professional field not listed"}</p>
                  </div>
                  <dl className="grid gap-x-8 gap-y-5 sm:grid-cols-2">
                    <div>
                      <dt className="text-xs font-medium uppercase tracking-wide text-slate-500">Email</dt>
                      <dd className="mt-1 break-words text-sm text-slate-900">{currentProfile.email || "Not listed in CV"}</dd>
                    </div>
                    <div>
                      <dt className="text-xs font-medium uppercase tracking-wide text-slate-500">Location</dt>
                      <dd className="mt-1 text-sm text-slate-900">{currentProfile.location || "Not listed in CV"}</dd>
                    </div>
                  </dl>
                  <div>
                    <h4 className="text-xs font-medium uppercase tracking-wide text-slate-500">Target roles</h4>
                    <div className="mt-3 flex flex-wrap gap-2">
                      {currentProfile.target_roles.map((role) => (
                        <span key={role.name} className="rounded-md border border-[#e5e7eb] bg-white px-3 py-1.5 text-sm text-slate-700">
                          {role.name}{role.abbreviation ? ` (${role.abbreviation})` : ""}
                        </span>
                      ))}
                    </div>
                  </div>
                  <div>
                    <h4 className="text-xs font-medium uppercase tracking-wide text-slate-500">Technical skills</h4>
                    <div className="mt-3 flex flex-wrap gap-2">
                      {currentProfile.technical_skills.map((skill) => (
                        <span key={skill} className="rounded-md bg-[#eef2f4] px-3 py-1.5 text-sm text-slate-700">{skill}</span>
                      ))}
                    </div>
                  </div>
                </div>
              )}
            </div>
          </section>

          <div ref={chatContainerRef} className={`${activeTab === "dashboard" ? "flex" : "hidden"} flex-1 overflow-y-auto px-4 py-4 md:px-6 md:py-6`}>
            <div className="mx-auto max-w-3xl space-y-5">
              <div className="flex items-center gap-3 py-2 text-[10px] font-semibold uppercase tracking-[0.2em] text-slate-400">
                <span className="h-px flex-1 bg-[#f1f5f9]" />
                <span>Today · September 19, 2026</span>
                <span className="h-px flex-1 bg-[#f1f5f9]" />
              </div>

              {messages.map((message) => (
                <div key={message.id} className={`flex ${message.role === "user" ? "justify-end" : "justify-start"}`}>
                  <div className={`w-full max-w-3xl ${message.role === "user" ? "text-right" : "text-left"}`}>
                    <div
                      className={`inline-block max-w-full rounded-2xl px-4 py-3 text-left text-sm leading-7 ${
                        message.role === "user"
                          ? "bg-[#f3f4f6] text-slate-900"
                          : "bg-transparent text-slate-700"
                      }`}
                    >
                      <p className="whitespace-pre-wrap">{message.content}</p>
                    </div>

                    {message.jobs && message.jobs.length > 0 && (
                      <div className="mt-4 grid gap-3 md:grid-cols-2">
                        {message.jobs.map((job) => (
                          <button
                            key={job.id}
                            onClick={() => setSelectedJob(job)}
                            className={`rounded-2xl border p-4 text-left transition ${
                              selectedJob?.id === job.id
                                ? "border-[#111827] bg-[#f8fafc] shadow-[0_1px_2px_rgba(17,24,39,0.04)]"
                                : "border-[#e5e7eb] bg-white hover:border-[#d1d5db] hover:bg-[#f8fafc]"
                            }`}
                          >
                            <div className="flex items-start justify-between gap-3">
                              <div>
                                <p className="text-base font-semibold text-slate-900">{job.title}</p>
                                <p className="mt-1 text-sm text-slate-500">{job.company}</p>
                              </div>
                              {job.relevanceScore !== null ? (
                                <span className="rounded-full bg-[#ecfdf5] px-2 py-1 text-[11px] font-medium text-[#166534]">
                                  Score {job.relevanceScore.toFixed(2)}
                                </span>
                              ) : job.matchScore !== null ? (
                                <span className="rounded-full bg-[#ecfdf5] px-2 py-1 text-[11px] font-medium text-[#166534]">
                                  {job.matchScore}%
                                </span>
                              ) : null}
                            </div>

                            <div className="mt-3 flex flex-wrap gap-2 text-[11px] text-slate-500">
                              {job.location && <span className="rounded-full border border-[#e5e7eb] px-2 py-1">{job.location}</span>}
                              {job.type && <span className="rounded-full border border-[#e5e7eb] px-2 py-1">{job.type}</span>}
                              {job.salary && <span className="rounded-full border border-[#e5e7eb] px-2 py-1">{job.salary}</span>}
                            </div>
                          </button>
                        ))}
                      </div>
                    )}
                  </div>
                </div>
              ))}

              {isLoading && (
                <div className="flex justify-start">
                  <div className="rounded-2xl border border-[#e5e7eb] bg-[#f8fafc] px-4 py-3 text-sm text-slate-500">
                    {isUploadingCv
                      ? "Uploading your CV and searching opportunities..."
                      : "Searching opportunities and comparing them with your profile..."}
                  </div>
                </div>
              )}
            </div>
          </div>

          <div className={`${activeTab === "dashboard" ? "" : "hidden"} border-t border-[#f1f5f9] bg-white px-4 py-4 md:px-6`}>
            <div className="mx-auto max-w-3xl">
              <div className="mb-3 flex flex-wrap gap-2">
                {quickPrompts.map((prompt) => (
                  <button
                    key={prompt}
                    onClick={() => sendPrompt(prompt)}
                    className="rounded-full border border-[#e5e7eb] bg-[#f8fafc] px-3 py-1.5 text-xs text-slate-600 transition hover:border-[#d1d5db] hover:bg-[#f3f4f6]"
                  >
                    {prompt}
                  </button>
                ))}
              </div>

              {selectedFile && (
                <div className="mb-2 flex items-center justify-between rounded-xl border border-[#e5e7eb] bg-[#f8fafc] px-3 py-2 text-xs text-slate-600">
                  <span className="truncate">{selectedFile.name}</span>
                  <button
                    type="button"
                    onClick={() => {
                      setSelectedFile(null);
                      setFileError("");
                      if (fileInputRef.current) {
                        fileInputRef.current.value = "";
                      }
                    }}
                    className="ml-2 text-slate-500 hover:text-slate-700"
                  >
                    Remove
                  </button>
                </div>
              )}

              {fileError && <p className="mb-2 text-xs text-red-600">{fileError}</p>}

              <div className="flex items-end gap-3 rounded-2xl border border-[#e5e7eb] bg-[#f8fafc] p-3 shadow-[inset_0_1px_0_rgba(255,255,255,0.7)]">
                <input
                  ref={fileInputRef}
                  type="file"
                  accept=".pdf,application/pdf"
                  className="hidden"
                  onChange={handleFileChange}
                />

                <button
                  type="button"
                  onClick={() => fileInputRef.current?.click()}
                  className="flex h-11 w-11 items-center justify-center rounded-xl border border-[#e5e7eb] bg-white text-slate-600 transition hover:border-[#d1d5db] hover:text-slate-800"
                  aria-label="Upload PDF"
                >
                  <svg viewBox="0 0 24 24" fill="none" className="h-5 w-5" stroke="currentColor" strokeWidth="1.9">
                    <path d="M15 10.5V16.5C15 17.8807 13.8807 19 12.5 19H9.5C8.11929 19 7 17.8807 7 16.5V9.5C7 8.11929 8.11929 7 9.5 7H13.5C14.8807 7 16 8.11929 16 9.5V12.5" strokeLinecap="round" strokeLinejoin="round" />
                    <path d="M11 7V4.5C11 4.22386 11.2239 4 11.5 4H15.5C15.7761 4 16 4.22386 16 4.5V7" strokeLinecap="round" />
                    <path d="M16 9.5H13.5C12.1193 9.5 11 8.38071 11 7V4.5" strokeLinecap="round" />
                  </svg>
                </button>

                <textarea
                  value={draft}
                  onChange={(event) => setDraft(event.target.value)}
                  rows={1}
                  placeholder="Ask for jobs, internships, or fit analysis..."
                  className="max-h-36 min-h-[48px] flex-1 resize-none border-0 bg-transparent px-2 py-2 text-sm text-slate-800 outline-none placeholder:text-slate-400"
                  onKeyDown={(event) => {
                    if (event.key === "Enter" && !event.shiftKey) {
                      event.preventDefault();
                      void sendPrompt();
                    }
                  }}
                />
                <button
                  type="button"
                  onClick={() => void sendPrompt()}
                  className="flex h-11 w-11 items-center justify-center rounded-xl bg-[#111827] text-white transition hover:bg-[#1f2937]"
                  aria-label="Send message"
                >
                  <svg viewBox="0 0 24 24" fill="none" className="h-4 w-4" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                    <path d="M5 12L19 5L14 19L11 13L5 12Z" />
                  </svg>
                </button>
              </div>
            </div>
          </div>
        </main>

        <aside className={`${activeTab === "dashboard" ? "hidden xl:block" : "hidden"} w-[320px] shrink-0 rounded-[28px] border border-[#e5e7eb] bg-white p-5 shadow-[0_1px_2px_rgba(17,24,39,0.04)]`}>
          {selectedJob ? (
            <div>
              <p className="text-[10px] font-semibold uppercase tracking-[0.22em] text-slate-400">Selected role</p>
              <h3 className="mt-3 text-xl font-semibold text-slate-900">{selectedJob.title}</h3>
              <p className="mt-1 text-sm text-slate-500">{selectedJob.company}</p>

              <div className="mt-5 flex flex-wrap gap-2">
                {selectedJob.relevanceScore !== null && (
                  <span className="rounded-full bg-[#ecfdf5] px-2.5 py-1 text-[11px] font-medium text-[#166534]">
                    Relevance score {selectedJob.relevanceScore.toFixed(2)}
                  </span>
                )}
                {selectedJob.matchScore !== null && (
                  <span className="rounded-full bg-[#ecfdf5] px-2.5 py-1 text-[11px] font-medium text-[#166534]">
                    {selectedJob.matchScore}% match
                  </span>
                )}
                {selectedJob.location && (
                  <span className="rounded-full border border-[#e5e7eb] px-2.5 py-1 text-[11px] text-slate-600">
                    {selectedJob.location}
                  </span>
                )}
                {selectedJob.type && (
                  <span className="rounded-full border border-[#e5e7eb] px-2.5 py-1 text-[11px] text-slate-600">
                    {selectedJob.type}
                  </span>
                )}
              </div>

              {selectedJob.reasons.length > 0 ? (
                <div className="mt-6 rounded-2xl border border-[#e5e7eb] bg-[#f8fafc] p-4">
                  <p className="text-[10px] font-semibold uppercase tracking-[0.2em] text-slate-400">Why it matches</p>
                  <ul className="mt-3 space-y-3 text-sm text-slate-600">
                    {selectedJob.reasons.map((reason) => (
                      <li key={reason} className="flex gap-2">
                        <span className="mt-2 h-2 w-2 rounded-full bg-slate-900" />
                        <span>{reason}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              ) : selectedJob.description ? (
                <div className="mt-6 rounded-2xl border border-[#e5e7eb] bg-[#f8fafc] p-4">
                  <p className="text-[10px] font-semibold uppercase tracking-[0.2em] text-slate-400">Role summary</p>
                  <p className="mt-3 text-sm leading-6 text-slate-600">{selectedJob.description}</p>
                </div>
              ) : null}

              {selectedJob.tags.length > 0 && <div className="mt-6">
                <p className="text-[10px] font-semibold uppercase tracking-[0.2em] text-slate-400">Skills</p>
                <div className="mt-3 flex flex-wrap gap-2">
                  {selectedJob.tags.map((tag) => (
                    <span key={tag} className="rounded-full border border-[#e5e7eb] bg-white px-2.5 py-1 text-[11px] text-slate-600">
                      {tag}
                    </span>
                  ))}
                </div>
              </div>}

              {selectedJob.missingSkills.length > 0 && <div className="mt-6 rounded-2xl border border-[#fef3c7] bg-[#fffbeb] p-4">
                <p className="text-[10px] font-semibold uppercase tracking-[0.2em] text-[#a16207]">Needs attention</p>
                <ul className="mt-3 space-y-2 text-sm text-[#7c5a00]">
                  {selectedJob.missingSkills.map((skill) => (
                    <li key={skill}>• {skill}</li>
                  ))}
                </ul>
              </div>}

              <div className="mt-6 space-y-3">
                <button className="w-full rounded-xl bg-slate-900 px-4 py-2.5 text-sm font-medium text-white hover:bg-slate-700">
                  Save job
                </button>
                <button className="w-full rounded-xl border border-[#e5e7eb] bg-white px-4 py-2.5 text-sm font-medium text-slate-700 hover:bg-slate-50">
                  Compare with profile
                </button>
              </div>
            </div>
          ) : (
            <div className="flex h-full items-center justify-center text-sm text-slate-400">
              Select a job match to inspect it.
            </div>
          )}
        </aside>
      </div>
    </div>
  );
}

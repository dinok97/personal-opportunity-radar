"use client";

import { useEffect, useRef, useState } from "react";
import { jobMatches, type JobMatch, userProfile } from "@/lib/mock-data";

type ChatMessage = {
  id: string;
  role: "user" | "assistant";
  content: string;
  jobs?: JobMatch[];
};

const defaultJobs = jobMatches.slice(0, 3);

export function AICareerDashboard() {
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      id: "welcome",
      role: "assistant",
      content:
        "Hi Alicia — I reviewed your profile and can help you find internship and full-time roles that match your ML and LLM background.",
      jobs: defaultJobs,
    },
  ]);
  const [draft, setDraft] = useState("");
  const [selectedJob, setSelectedJob] = useState<JobMatch | null>(defaultJobs[0]);
  const [isLoading, setIsLoading] = useState(false);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [fileError, setFileError] = useState("");
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
      content: fileToSend ? `Uploaded PDF: ${fileToSend.name}${cleanPrompt ? `\n\n${cleanPrompt}` : ""}` : cleanPrompt,
    };
    const requestMessages = [...messages, userMessage];

    setMessages((prev) => [...prev, userMessage]);
    setDraft("");
    setSelectedFile(null);
    setFileError("");
    if (fileInputRef.current) {
      fileInputRef.current.value = "";
    }
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

      const data = await response.json();
      if (!response.ok) {
        throw new Error(data.detail || data.message || "The chat service is unavailable.");
      }

      const assistantMessage: ChatMessage = {
        id: nextMessageId("assistant"),
        role: "assistant",
        content:
          data.message ||
          "I found a few great opportunities for you. I can narrow them by remote, type, or required skills.",
        jobs: data.jobs || defaultJobs,
      };

      setMessages((prev) => [...prev, assistantMessage]);
      if (data.jobs?.length) {
        setSelectedJob(data.jobs[0]);
      }
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : "The chat service is unavailable.";
      setMessages((prev) => [
        ...prev,
        {
          id: nextMessageId("assistant"),
          role: "assistant",
          content: errorMessage,
          jobs: defaultJobs,
        },
      ]);
    } finally {
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
              { label: "Dashboard", active: true },
              { label: "My profile" },
              { label: "Matches" },
              { label: "Saved jobs" },
            ].map((item) => (
              <button
                key={item.label}
                className={`flex w-full items-center justify-between rounded-xl px-3 py-2 text-left text-sm transition ${
                  item.active ? "bg-[#f3f4f6] font-medium text-slate-900" : "text-slate-600 hover:bg-slate-50"
                }`}
              >
                <span>{item.label}</span>
                {item.active && <span className="rounded-full bg-[#ecfdf5] px-2 py-0.5 text-[10px] text-[#166534]">Live</span>}
              </button>
            ))}
          </nav>

          <div className="mt-8 rounded-2xl border border-[#e5e7eb] bg-[#f8fafc] p-4">
            <p className="text-[10px] font-semibold uppercase tracking-[0.2em] text-slate-400">Profile</p>
            <div className="mt-4 flex items-center gap-3">
              <div className="flex h-10 w-10 items-center justify-center rounded-full bg-[#e5e7eb] text-xs font-semibold text-slate-700">
                AM
              </div>
              <div>
                <p className="text-sm font-medium text-slate-900">{userProfile.name}</p>
                <p className="text-xs text-slate-500">{userProfile.role}</p>
              </div>
            </div>
            <div className="mt-4 flex flex-wrap gap-2">
              {userProfile.topSkills.slice(0, 4).map((skill) => (
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
              <h2 className="mt-1 text-lg font-semibold text-slate-900 md:text-xl">AI job discovery</h2>
            </div>
            <div className="flex items-center gap-2 rounded-full border border-[#d1fae5] bg-[#ecfdf5] px-3 py-1.5 text-xs font-medium text-[#166534]">
              <span className="h-2 w-2 rounded-full bg-[#22c55e]" />
              3 new matches
            </div>
          </header>

          <div ref={chatContainerRef} className="flex-1 overflow-y-auto px-4 py-4 md:px-6 md:py-6">
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
                              <span className="rounded-full bg-[#ecfdf5] px-2 py-1 text-[11px] font-medium text-[#166534]">
                                {job.matchScore}%
                              </span>
                            </div>

                            <div className="mt-3 flex flex-wrap gap-2 text-[11px] text-slate-500">
                              <span className="rounded-full border border-[#e5e7eb] px-2 py-1">{job.location}</span>
                              <span className="rounded-full border border-[#e5e7eb] px-2 py-1">{job.type}</span>
                              <span className="rounded-full border border-[#e5e7eb] px-2 py-1">{job.salary}</span>
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
                    Searching opportunities and comparing them with your profile...
                  </div>
                </div>
              )}
            </div>
          </div>

          <div className="border-t border-[#f1f5f9] bg-white px-4 py-4 md:px-6">
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

        <aside className="hidden w-[320px] shrink-0 rounded-[28px] border border-[#e5e7eb] bg-white p-5 shadow-[0_1px_2px_rgba(17,24,39,0.04)] xl:block">
          {selectedJob ? (
            <div>
              <p className="text-[10px] font-semibold uppercase tracking-[0.22em] text-slate-400">Selected role</p>
              <h3 className="mt-3 text-xl font-semibold text-slate-900">{selectedJob.title}</h3>
              <p className="mt-1 text-sm text-slate-500">{selectedJob.company}</p>

              <div className="mt-5 flex flex-wrap gap-2">
                <span className="rounded-full bg-[#ecfdf5] px-2.5 py-1 text-[11px] font-medium text-[#166534]">
                  {selectedJob.matchScore}% match
                </span>
                <span className="rounded-full border border-[#e5e7eb] px-2.5 py-1 text-[11px] text-slate-600">
                  {selectedJob.location}
                </span>
              </div>

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

              <div className="mt-6">
                <p className="text-[10px] font-semibold uppercase tracking-[0.2em] text-slate-400">Skills</p>
                <div className="mt-3 flex flex-wrap gap-2">
                  {selectedJob.tags.map((tag) => (
                    <span key={tag} className="rounded-full border border-[#e5e7eb] bg-white px-2.5 py-1 text-[11px] text-slate-600">
                      {tag}
                    </span>
                  ))}
                </div>
              </div>

              <div className="mt-6 rounded-2xl border border-[#fef3c7] bg-[#fffbeb] p-4">
                <p className="text-[10px] font-semibold uppercase tracking-[0.2em] text-[#a16207]">Needs attention</p>
                <ul className="mt-3 space-y-2 text-sm text-[#7c5a00]">
                  {selectedJob.missingSkills.map((skill) => (
                    <li key={skill}>• {skill}</li>
                  ))}
                </ul>
              </div>

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

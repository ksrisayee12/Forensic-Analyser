import { useEffect, useMemo, useState } from "react";
import { useRouterState } from "@tanstack/react-router";
import { getCaseById } from "@/services/api";
import { Case } from "@/types";
import { MessageSquare, Sparkles, Send, X } from "lucide-react";

type Message = {
  role: "assistant" | "user";
  text: string;
  time: string;
};

const initialMessages: Message[] = [
  {
    role: "assistant",
    text: "Hi there! I’m AIVENTRA Assistant. Ask me about case findings, evidence status, or evidence correlations.",
    time: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
  },
];

const quickPrompts = [
  "Summarize the current case findings.",
  "What evidence modules should I review first?",
  "How strong is the evidence correlation?",
];

function formatTime(date = new Date()) {
  return date.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
}

function generateBotResponse(question: string, caseData?: Case) {
  const normalized = question.toLowerCase();

  const makeCaseIntro = () =>
    caseData
      ? `For case ${caseData.id}, ${caseData.summary} `
      : "This is a general AIVENTRA response. ";

  if (normalized.includes("summarize") || normalized.includes("summary")) {
    return caseData
      ? `For ${caseData.id}: ${caseData.summary} The case is currently ${caseData.status.toLowerCase()} and led by ${caseData.investigator} from ${caseData.unit}.`
      : "This case currently shows strong forensic indicators from autopsy and timeline evidence. The next step is reviewing suspect movement and CCTV anomalies to confirm the timeline.";
  }

  if (normalized.includes("modules") || normalized.includes("evidence modules")) {
    return caseData
      ? `${makeCaseIntro()}Key active modules are ${caseData.evidenceModules.join(", ")}. Focus on the highest-priority evidence streams for the current investigation.`
      : "Review the autopsy findings first, then compare them with timeline events and correlation links. The highest-priority evidence modules are Autopsy, Timeline, and Correlation.";
  }

  if (normalized.includes("status") || normalized.includes("priority") || normalized.includes("investigator")) {
    if (caseData) {
      return `${makeCaseIntro()}The current status is ${caseData.status}, priority is ${caseData.priority}, and the lead investigator is ${caseData.investigator}.`;
    }
  }

  if (normalized.includes("correlation")) {
    return caseData
      ? `${makeCaseIntro()}The correlation graph suggests strong relationships between ${caseData.evidenceModules.join(", ")} evidence streams. Check the correlation module for linked activity and anomalies.`
      : "The correlation graph suggests several strong relationships between mobile activity, witness accounts, and the autopsy window. Focus on the highest-confidence nodes first.";
  }

  return caseData
    ? `${makeCaseIntro()}I’m using the current case context to answer. In a live deployment, this assistant would query backend case details for accurate predictions.`
    : "I’m processing your request. In a real deployment, this assistant would connect to your AI backend for context-aware case analysis.";
}

export function ChatbotWidget() {
  const pathname = useRouterState({ select: (s) => s.location.pathname });
  const caseMatch = pathname.match(/^\/case\/([^/]+)/);
  const caseId = caseMatch?.[1];
  const [caseData, setCaseData] = useState<Case | null>(null);
  const currentCaseKey = caseId ?? "global";

  const [chatThreads, setChatThreads] = useState<Record<string, Message[]>>({
    global: initialMessages,
  });
  const messages = chatThreads[currentCaseKey] ?? initialMessages;
  const [draft, setDraft] = useState("");
  const [isTyping, setIsTyping] = useState(false);
  const [isOpen, setIsOpen] = useState(false);

  useEffect(() => {
    let active = true;
    if (!caseId) {
      setCaseData(null);
      return;
    }

    getCaseById(caseId).then((data) => {
      if (active) {
        setCaseData(data);
      }
    });

    return () => {
      active = false;
    };
  }, [caseId]);

  useEffect(() => {
    setChatThreads((prev) => {
      if (prev[currentCaseKey]) return prev;
      return { ...prev, [currentCaseKey]: initialMessages };
    });
  }, [currentCaseKey]);

  const handleSend = (text: string) => {
    const trimmed = text.trim();
    if (!trimmed) return;

    const userMessage: Message = {
      role: "user",
      text: trimmed,
      time: formatTime(),
    };

    setChatThreads((prev) => {
      const currentMessages = prev[currentCaseKey] ?? initialMessages;
      return { ...prev, [currentCaseKey]: [...currentMessages, userMessage] };
    });
    setDraft("");
    setIsTyping(true);

    window.setTimeout(() => {
      setChatThreads((prev) => {
        const currentMessages = prev[currentCaseKey] ?? initialMessages;
        return {
          ...prev,
          [currentCaseKey]: [
            ...currentMessages,
            {
              role: "assistant",
              text: generateBotResponse(trimmed, caseData),
              time: formatTime(),
            },
          ],
        };
      });
      setIsTyping(false);
    }, 700);
  };

  const handleQuickPrompt = (prompt: string) => {
    setDraft(prompt);
  };

  const lastMessage = useMemo(() => messages[messages.length - 1], [messages]);

  return (
    <>
      <button
        type="button"
        onClick={() => setIsOpen(true)}
        className="fixed right-6 bottom-6 z-50 inline-flex items-center gap-2 rounded-full bg-primary px-5 py-3 text-sm font-semibold text-primary-foreground shadow-2xl shadow-primary/20 transition hover:-translate-y-0.5 hover:bg-primary/90"
      >
        <MessageSquare className="h-4 w-4" />
        Chat with AIVENTRA
      </button>

      {isOpen && (
        <aside className="fixed right-6 top-6 bottom-6 z-50 w-[420px] rounded-[32px] border border-white/10 bg-slate-950/95 shadow-[0_40px_120px_rgba(15,23,42,0.65)] backdrop-blur-xl">
          <div className="flex h-full flex-col overflow-hidden rounded-[32px] bg-gradient-to-b from-slate-950 via-slate-900 to-slate-950 shadow-inner">
            <div className="flex items-center justify-between border-b border-white/10 px-6 py-4">
              <div>
                <p className="text-lg font-semibold">AIVENTRA Assistant</p>
                <p className="text-xs uppercase tracking-[0.24em] text-slate-500">
                  Work on the case while chatting in real time.
                </p>
              </div>
              <button
                type="button"
                onClick={() => setIsOpen(false)}
                className="inline-flex h-9 w-9 items-center justify-center rounded-full bg-white/5 text-slate-200 transition hover:bg-white/10"
              >
                <X className="h-4 w-4" />
              </button>
            </div>

            <div className="flex-1 overflow-y-auto px-6 py-4 space-y-4">
              {caseData ? (
                <div className="rounded-3xl border border-white/10 bg-slate-950/80 p-4 text-sm text-slate-200">
                  <p className="text-xs uppercase tracking-[0.24em] text-slate-500">Case context</p>
                  <div className="mt-3 space-y-2">
                    <div className="flex items-center justify-between gap-4 text-[13px]">
                      <span className="font-medium text-slate-100">Case</span>
                      <span className="text-slate-300">{caseData.id}</span>
                    </div>
                    <div className="flex items-center justify-between gap-4 text-[13px]">
                      <span className="font-medium text-slate-100">Victim</span>
                      <span className="text-slate-300">{caseData.victim}</span>
                    </div>
                    <div className="flex items-center justify-between gap-4 text-[13px]">
                      <span className="font-medium text-slate-100">Status</span>
                      <span className="text-slate-300">{caseData.status}</span>
                    </div>
                    <div className="flex items-center justify-between gap-4 text-[13px]">
                      <span className="font-medium text-slate-100">Priority</span>
                      <span className="text-slate-300">{caseData.priority}</span>
                    </div>
                    <div className="flex items-center justify-between gap-4 text-[13px]">
                      <span className="font-medium text-slate-100">Modules</span>
                      <span className="text-slate-300">{caseData.evidenceModules.join(", ")}</span>
                    </div>
                  </div>
                </div>
              ) : (
                <div className="rounded-3xl border border-white/10 bg-slate-950/80 p-4 text-sm text-slate-200">
                  <p className="text-xs uppercase tracking-[0.24em] text-slate-500">General AIVENTRA</p>
                  <p className="mt-2 text-sm text-slate-300">Open a case to read case-specific details and receive tailored answers.</p>
                </div>
              )}

              <div className="space-y-3 rounded-3xl border border-white/10 bg-slate-950/80 p-4">
                {messages.map((message, index) => (
                  <div
                    key={`${message.role}-${index}`}
                    className={`rounded-3xl p-4 ${
                      message.role === "assistant"
                        ? "border border-white/10 bg-slate-900 text-slate-100"
                        : "self-end bg-primary/10 text-white"
                    }`}
                  >
                    <div className="text-sm leading-6">{message.text}</div>
                    <div className="mt-3 text-[11px] uppercase tracking-[0.3em] text-slate-500">
                      {message.role === "assistant" ? "Assistant" : "You"} · {message.time}
                    </div>
                  </div>
                ))}

                {isTyping && (
                  <div className="rounded-3xl border border-white/10 bg-slate-900 p-4 text-sm text-slate-300">
                    AIVENTRA is preparing a smart response...
                  </div>
                )}
              </div>

              <div className="rounded-3xl border border-white/10 bg-slate-950/70 p-4">
                <p className="text-xs uppercase tracking-[0.24em] text-slate-500">Suggested prompts</p>
                <div className="mt-3 flex flex-wrap gap-2">
                  {quickPrompts.map((prompt) => (
                    <button
                      type="button"
                      key={prompt}
                      onClick={() => handleQuickPrompt(prompt)}
                      className="inline-flex items-center gap-2 rounded-full border border-white/10 bg-white/5 px-3 py-1.5 text-xs text-slate-200 transition hover:bg-white/10"
                    >
                      <Sparkles className="h-3.5 w-3.5" />
                      {prompt}
                    </button>
                  ))}
                </div>
              </div>
            </div>

            <form
              onSubmit={(event) => {
                event.preventDefault();
                handleSend(draft);
              }}
              className="border-t border-white/10 bg-slate-950/95 px-6 py-4"
            >
              <div className="flex items-center gap-3 rounded-3xl border border-white/10 bg-slate-900/90 px-4 py-3">
                <input
                  value={draft}
                  onChange={(event) => setDraft(event.target.value)}
                  placeholder="Ask a question or describe what you need…"
                  className="flex-1 bg-transparent text-sm text-slate-100 outline-none placeholder:text-slate-500"
                />
                <button
                  type="submit"
                  className="inline-flex items-center gap-2 rounded-full bg-primary px-4 py-2 text-sm font-semibold text-primary-foreground transition hover:bg-primary/90"
                >
                  <Send className="h-4 w-4" />
                  Send
                </button>
              </div>
            </form>
          </div>
        </aside>
      )}
    </>
  );
}

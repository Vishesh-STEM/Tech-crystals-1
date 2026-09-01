import { useEffect, useRef, useState } from "react";
import { Link } from "react-router-dom";
import { Bot, Loader2, MessageSquarePlus, Send, Sparkles, Trash2, User as UserIcon } from "lucide-react";
import Markdown from "../components/Markdown";
import { Card, EmptyState } from "../components/ui/Primitives";
import { useAuth } from "../context/AuthContext";
import { useToast } from "../context/ToastContext";
import { endpoints, errorMessage } from "../lib/api";
import { timeAgo } from "../lib/format";
import type { ChatMessage } from "../lib/types";

const STARTERS = [
  "Explain capacitors",
  "What should I study today?",
  "Give me 3 practice questions on Integration",
  "Why is Current Electricity weak for me?",
];

export default function Chat() {
  const { user } = useAuth();
  const toast = useToast();
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [sessions, setSessions] = useState<any[]>([]);
  const [sessionId, setSessionId] = useState<number | undefined>(undefined);
  const [input, setInput] = useState("");
  const [sending, setSending] = useState(false);
  const [status, setStatus] = useState<any>(null);
  const [sources, setSources] = useState<any[]>([]);
  const [suggestions, setSuggestions] = useState<string[]>([]);
  const endRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    endpoints.chatStatus().then(setStatus).catch(() => undefined);
    endpoints.chatSessions().then(setSessions).catch(() => undefined);
  }, []);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, sending]);

  async function openSession(id?: number) {
    setSessionId(id);
    setSources([]);
    if (!id) {
      setMessages([]);
      return;
    }
    try {
      setMessages(await endpoints.chatHistory(id));
    } catch (err) {
      toast.error(errorMessage(err));
    }
  }

  async function send(text?: string) {
    const question = (text ?? input).trim();
    if (!question || sending) return;
    setInput("");
    setSending(true);
    const optimistic: ChatMessage = {
      id: Date.now(),
      role: "user",
      content: question,
      created_at: new Date().toISOString(),
    };
    setMessages((current) => [...current, optimistic]);
    try {
      const response = await endpoints.chat({ message: question, session_id: sessionId });
      setSessionId(response.session_id);
      setMessages((current) => [...current, response.message]);
      setSources(response.sources || []);
      setSuggestions(response.suggestions || []);
      endpoints.chatSessions().then(setSessions).catch(() => undefined);
    } catch (err) {
      toast.error(errorMessage(err));
      setMessages((current) => current.filter((message) => message.id !== optimistic.id));
      setInput(question);
    } finally {
      setSending(false);
    }
  }

  async function removeSession(id: number) {
    try {
      await endpoints.deleteChatSession(id);
      setSessions((current) => current.filter((session) => session.id !== id));
      if (sessionId === id) openSession(undefined);
      toast.success("Conversation deleted.");
    } catch (err) {
      toast.error(errorMessage(err));
    }
  }

  return (
    <div className="grid gap-5 lg:grid-cols-[260px_1fr]">
      {/* sessions */}
      <div className="space-y-3">
        <button className="btn-primary w-full text-sm" onClick={() => openSession(undefined)}>
          <MessageSquarePlus size={16} /> New conversation
        </button>
        <Card className="p-3">
          <p className="mb-2 px-1 text-xs font-semibold uppercase tracking-wide text-ink-500 dark:text-ink-400">
            Recent
          </p>
          {sessions.length === 0 ? (
            <p className="px-1 py-2 text-sm text-ink-500 dark:text-ink-400">No conversations yet.</p>
          ) : (
            <ul className="space-y-1">
              {sessions.map((session) => (
                <li key={session.id} className="group flex items-center gap-1">
                  <button
                    onClick={() => openSession(session.id)}
                    className={`min-w-0 flex-1 rounded-lg px-2 py-2 text-left text-sm transition ${
                      sessionId === session.id
                        ? "bg-brand-50 text-brand-700 dark:bg-brand-500/15 dark:text-brand-200"
                        : "hover:bg-ink-100 dark:hover:bg-white/5"
                    }`}
                  >
                    <span className="block truncate">{session.title}</span>
                    <span className="block text-[11px] text-ink-400">{timeAgo(session.last_message_at)}</span>
                  </button>
                  <button
                    className="opacity-0 transition group-hover:opacity-100"
                    onClick={() => removeSession(session.id)}
                    aria-label="Delete conversation"
                  >
                    <Trash2 size={15} className="text-ink-400 hover:text-rose-500" />
                  </button>
                </li>
              ))}
            </ul>
          )}
        </Card>

        {status ? (
          <Card className="p-3">
            <p className="mb-1 flex items-center gap-1.5 text-xs font-semibold uppercase tracking-wide text-ink-500 dark:text-ink-400">
              <Sparkles size={13} /> Tutor status
            </p>
            <p className="text-sm font-medium text-ink-800 dark:text-ink-100">
              {status.mode === "ollama" ? `Local model: ${status.model}` : "Offline mode"}
            </p>
            <p className="mt-1 text-xs text-ink-500 dark:text-ink-400">{status.detail}</p>
            <p className="mt-2 text-[11px] text-ink-400">
              {status.indexed_documents} indexed passages · {status.vector_backend}
            </p>
          </Card>
        ) : null}
      </div>

      {/* conversation */}
      <Card className="flex h-[calc(100vh-11rem)] flex-col p-0">
        <div className="flex items-center gap-2 border-b border-ink-200/70 px-4 py-3 dark:border-white/10">
          <span className="grid h-9 w-9 place-items-center rounded-xl bg-gradient-to-br from-brand-500 to-violet-500 text-white">
            <Bot size={18} />
          </span>
          <div className="min-w-0">
            <p className="font-display text-sm font-semibold text-ink-900 dark:text-white">Vidyalaya AI tutor</p>
            <p className="truncate text-xs text-ink-500 dark:text-ink-400">
              Answers grounded in your syllabus and your own performance data
            </p>
          </div>
        </div>

        <div className="scrollbar-thin flex-1 space-y-4 overflow-y-auto p-4">
          {messages.length === 0 ? (
            <div className="flex h-full flex-col items-center justify-center text-center">
              <span className="mb-3 grid h-14 w-14 place-items-center rounded-2xl bg-brand-50 text-brand-600 dark:bg-brand-500/15 dark:text-brand-300">
                <Bot size={26} />
              </span>
              <p className="font-display text-lg font-semibold text-ink-900 dark:text-white">
                Hi {user?.full_name?.split(" ")[0] || "there"}, what shall we work on?
              </p>
              <p className="muted mt-1 max-w-md">
                Ask about any Class 12 topic. I look up your syllabus content first and use your own mastery data
                to personalise the answer.
              </p>
              <div className="mt-5 flex flex-wrap justify-center gap-2">
                {STARTERS.map((starter) => (
                  <button key={starter} className="btn-secondary text-xs" onClick={() => send(starter)}>
                    {starter}
                  </button>
                ))}
              </div>
            </div>
          ) : (
            messages.map((message) => (
              <div key={message.id} className={`flex gap-3 ${message.role === "user" ? "justify-end" : ""}`}>
                {message.role === "assistant" ? (
                  <span className="grid h-8 w-8 shrink-0 place-items-center rounded-lg bg-brand-100 text-brand-700 dark:bg-brand-500/20 dark:text-brand-200">
                    <Bot size={16} />
                  </span>
                ) : null}
                <div
                  className={`max-w-[80%] rounded-2xl px-4 py-3 ${
                    message.role === "user"
                      ? "bg-brand-600 text-white"
                      : "bg-ink-50 text-ink-800 dark:bg-white/5 dark:text-ink-100"
                  }`}
                >
                  {message.role === "user" ? (
                    <p className="text-sm">{message.content}</p>
                  ) : (
                    <Markdown content={message.content} />
                  )}
                  {message.role === "assistant" && message.mode ? (
                    <p className="mt-2 text-[11px] text-ink-400">
                      {message.mode === "ollama" ? `local model · ${message.model}` : "offline mode"}
                    </p>
                  ) : null}
                </div>
                {message.role === "user" ? (
                  <span className="grid h-8 w-8 shrink-0 place-items-center rounded-lg bg-ink-200 text-ink-600 dark:bg-white/10 dark:text-ink-200">
                    <UserIcon size={16} />
                  </span>
                ) : null}
              </div>
            ))
          )}
          {sending ? (
            <div className="flex items-center gap-2 text-sm text-ink-500 dark:text-ink-400">
              <Loader2 className="animate-spin" size={16} /> Looking through your syllabus...
            </div>
          ) : null}
          <div ref={endRef} />
        </div>

        {sources.length ? (
          <div className="border-t border-ink-200/70 px-4 py-2 dark:border-white/10">
            <p className="mb-1 text-[11px] font-semibold uppercase tracking-wide text-ink-500 dark:text-ink-400">
              Sources from your syllabus
            </p>
            <div className="flex flex-wrap gap-1.5">
              {sources.map((source, position) => (
                <Link
                  key={`${source.topic_id}-${position}`}
                  to={source.topic_id ? `/topics/${source.topic_id}` : "/subjects"}
                  className="chip bg-ink-100 text-ink-600 hover:bg-ink-200 dark:bg-white/10 dark:text-ink-300"
                  title={source.snippet}
                >
                  {source.subject} · {source.topic}
                </Link>
              ))}
            </div>
          </div>
        ) : null}

        {suggestions.length && messages.length ? (
          <div className="flex flex-wrap gap-1.5 px-4 pt-2">
            {suggestions.map((suggestion) => (
              <button key={suggestion} className="chip bg-brand-50 text-brand-700 hover:bg-brand-100 dark:bg-brand-500/15 dark:text-brand-200" onClick={() => send(suggestion)}>
                {suggestion}
              </button>
            ))}
          </div>
        ) : null}

        <form
          className="flex items-end gap-2 border-t border-ink-200/70 p-3 dark:border-white/10"
          onSubmit={(event) => {
            event.preventDefault();
            send();
          }}
        >
          <textarea
            className="input max-h-32 min-h-[46px] flex-1 resize-none"
            placeholder="Ask anything about your Class 12 syllabus..."
            value={input}
            rows={1}
            onChange={(event) => setInput(event.target.value)}
            onKeyDown={(event) => {
              if (event.key === "Enter" && !event.shiftKey) {
                event.preventDefault();
                send();
              }
            }}
          />
          <button type="submit" className="btn-primary h-[46px]" disabled={sending || !input.trim()}>
            {sending ? <Loader2 className="animate-spin" size={16} /> : <Send size={16} />}
          </button>
        </form>
      </Card>
    </div>
  );
}

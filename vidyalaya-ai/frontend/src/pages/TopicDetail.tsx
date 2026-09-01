import { useEffect, useRef, useState } from "react";
import { Link, useParams } from "react-router-dom";
import {
  AlertTriangle, ArrowLeft, Bot, CheckCircle2, ExternalLink, Eye, FileText, Headphones,
  Lightbulb, PencilRuler, Play, Timer,
} from "lucide-react";
import Markdown from "../components/Markdown";
import { Card, EmptyState, ErrorState, ProgressBar, SectionHeader, Skeleton } from "../components/ui/Primitives";
import { useToast } from "../context/ToastContext";
import { endpoints, errorMessage } from "../lib/api";
import { formatMinutes, masteryTone, toneClasses } from "../lib/format";

const formatMeta: Record<string, { icon: any; label: string; hint: string }> = {
  text: { icon: FileText, label: "Read", hint: "Concept summary" },
  visual: { icon: Eye, label: "Visualise", hint: "Diagram walkthrough" },
  audio: { icon: Headphones, label: "Listen", hint: "Revision script" },
  practice: { icon: PencilRuler, label: "Practise", hint: "Practice set" },
};

export default function TopicDetail() {
  const { topicId } = useParams();
  const toast = useToast();
  const [topic, setTopic] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [activeResource, setActiveResource] = useState<any>(null);
  const [practice, setPractice] = useState<any[]>([]);
  const [revealed, setRevealed] = useState<Record<number, boolean>>({});
  const openedAt = useRef<number>(Date.now());

  async function load() {
    setLoading(true);
    setError("");
    try {
      const data = await endpoints.topic(topicId!);
      setTopic(data);
      setActiveResource(data.resources?.[0] ?? null);
    } catch (err) {
      setError(errorMessage(err));
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    openedAt.current = Date.now();
    load();
    return () => {
      const seconds = Math.round((Date.now() - openedAt.current) / 1000);
      if (seconds > 5 && topicId) {
        endpoints
          .trackActivity({
            event_type: seconds < 30 ? "abandoned_topic" : "spent_time",
            topic_id: Number(topicId),
            duration_seconds: Math.min(seconds, 7200),
          })
          .catch(() => undefined);
      }
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [topicId]);

  async function openResource(resource: any) {
    setActiveResource(resource);
    try {
      await endpoints.resource(resource.id);
    } catch {
      /* tracking is best effort */
    }
  }

  async function completeResource(resource: any) {
    try {
      await endpoints.trackActivity({
        event_type: "completed_resource",
        resource_id: resource.id,
        topic_id: topic.id,
        duration_seconds: (resource.estimated_minutes || 10) * 60,
      });
      toast.success(`Marked "${resource.title}" as complete. This updates your learning profile.`);
    } catch (err) {
      toast.error(errorMessage(err));
    }
  }

  async function loadPractice() {
    try {
      setPractice(await endpoints.topicQuestions(topic.id, 5));
    } catch (err) {
      toast.error(errorMessage(err));
    }
  }

  if (loading) return <Skeleton className="h-96 w-full" />;
  if (error) return <ErrorState message={error} onRetry={load} />;
  if (!topic) return null;

  const progress = topic.progress || {};
  const tone = toneClasses[masteryTone(progress.mastery || 0)];

  return (
    <div className="space-y-5">
      <Link to={`/chapters/${topic.chapter.id}`} className="btn-ghost -ml-2 text-sm">
        <ArrowLeft size={15} /> {topic.chapter.name}
      </Link>

      <Card>
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div className="max-w-2xl">
            <p className="text-xs font-semibold uppercase tracking-wide text-brand-600 dark:text-brand-300">
              {topic.subject.name} · Chapter {topic.chapter.number}
            </p>
            <h1 className="mt-1 font-display text-2xl font-semibold text-ink-900 dark:text-white">{topic.name}</h1>
            <p className="mt-2 text-ink-700 dark:text-ink-200">{topic.summary}</p>
            <div className="mt-3 flex flex-wrap gap-2">
              <span className="chip bg-ink-100 text-ink-600 dark:bg-white/10 dark:text-ink-300">
                <Timer size={12} /> {topic.estimated_minutes} min
              </span>
              <span className="chip bg-ink-100 text-ink-600 dark:bg-white/10 dark:text-ink-300">{topic.difficulty}</span>
              {topic.ncert_url ? (
                <a href={topic.ncert_url} target="_blank" rel="noreferrer" className="chip bg-brand-50 text-brand-700 hover:bg-brand-100 dark:bg-brand-500/15 dark:text-brand-200">
                  <ExternalLink size={12} /> NCERT reference
                </a>
              ) : null}
            </div>
          </div>
          <div className="min-w-[180px] rounded-xl bg-ink-50 p-4 dark:bg-white/5">
            <p className="text-xs uppercase tracking-wide text-ink-500 dark:text-ink-400">Your mastery</p>
            <p className={`font-display text-3xl font-semibold ${tone.text}`}>{Math.round(progress.mastery || 0)}</p>
            <ProgressBar value={progress.mastery || 0} className="mt-1" />
            <p className="mt-2 text-xs text-ink-500 dark:text-ink-400">
              {progress.attempts || 0} attempts · {progress.questions_answered || 0} questions ·{" "}
              {formatMinutes(progress.study_minutes || 0)}
            </p>
          </div>
        </div>

        {progress.is_weak ? (
          <p className="mt-4 rounded-xl border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-800 dark:border-amber-500/20 dark:bg-amber-500/10 dark:text-amber-200">
            <AlertTriangle size={14} className="mr-1.5 inline" />
            <strong>{topic.name} needs attention.</strong> {progress.weakness_reason}
          </p>
        ) : null}
      </Card>

      <div className="grid gap-5 lg:grid-cols-3">
        <div className="space-y-5 lg:col-span-2">
          <Card>
            <SectionHeader
              title="Study this topic"
              subtitle="Pick a format - we measure which one works best for you."
            />
            <div className="mb-4 grid grid-cols-2 gap-2 sm:grid-cols-4">
              {topic.resources.map((resource: any) => {
                const meta = formatMeta[resource.type] ?? formatMeta.text;
                const Icon = meta.icon;
                const active = activeResource?.id === resource.id;
                return (
                  <button
                    key={resource.id}
                    onClick={() => openResource(resource)}
                    className={`rounded-xl border p-3 text-left transition ${
                      active
                        ? "border-brand-400 bg-brand-50 dark:border-brand-500/40 dark:bg-brand-500/10"
                        : "border-ink-200 hover:border-brand-300 dark:border-white/10"
                    }`}
                  >
                    <Icon size={17} className={active ? "text-brand-600 dark:text-brand-300" : "text-ink-500"} />
                    <p className="mt-1.5 text-sm font-semibold text-ink-900 dark:text-white">{meta.label}</p>
                    <p className="text-[11px] text-ink-500 dark:text-ink-400">{resource.estimated_minutes} min</p>
                  </button>
                );
              })}
            </div>

            {activeResource ? (
              <div className="rounded-xl border border-ink-200/70 p-4 dark:border-white/10">
                <div className="mb-2 flex flex-wrap items-center justify-between gap-2">
                  <h3 className="font-display font-semibold text-ink-900 dark:text-white">{activeResource.title}</h3>
                  <button className="btn-secondary text-xs" onClick={() => completeResource(activeResource)}>
                    <CheckCircle2 size={14} /> Mark as complete
                  </button>
                </div>
                <Markdown content={activeResource.body} />
              </div>
            ) : (
              <EmptyState title="No resources yet" description="A teacher can add study resources for this topic." />
            )}
          </Card>

          <Card>
            <SectionHeader
              title="Key concepts"
              subtitle="The points examiners keep coming back to."
              action={
                <Link to="/chat" className="btn-ghost text-sm">
                  <Bot size={15} /> Ask about this
                </Link>
              }
            />
            <ul className="space-y-2">
              {(topic.key_concepts || []).map((concept: string) => (
                <li key={concept} className="flex gap-2 rounded-lg bg-ink-50 px-3 py-2 text-sm text-ink-700 dark:bg-white/5 dark:text-ink-200">
                  <Lightbulb size={15} className="mt-0.5 shrink-0 text-amber-500" />
                  {concept}
                </li>
              ))}
            </ul>
            {topic.examples?.length ? (
              <>
                <h3 className="mb-2 mt-5 font-display text-sm font-semibold text-ink-900 dark:text-white">Worked examples</h3>
                <ul className="space-y-2">
                  {topic.examples.map((example: string) => (
                    <li key={example} className="rounded-lg border border-dashed border-ink-200 px-3 py-2 text-sm text-ink-700 dark:border-white/10 dark:text-ink-200">
                      {example}
                    </li>
                  ))}
                </ul>
              </>
            ) : null}
          </Card>

          <Card>
            <SectionHeader
              title="Quick practice"
              subtitle="Instant feedback - these attempts are not graded."
              action={
                <button className="btn-secondary text-sm" onClick={loadPractice}>
                  <PencilRuler size={14} /> {practice.length ? "Reload" : "Load questions"}
                </button>
              }
            />
            {practice.length === 0 ? (
              <EmptyState title="Practice on demand" description="Load a few questions with worked explanations before you attempt the graded quiz." />
            ) : (
              <ol className="space-y-4">
                {practice.map((question, index) => (
                  <li key={question.id} className="rounded-xl border border-ink-200/70 p-4 dark:border-white/10">
                    <p className="text-sm font-medium text-ink-900 dark:text-white">
                      {index + 1}. {question.text}
                    </p>
                    <ul className="mt-2 space-y-1">
                      {(question.options || []).map((option: string) => (
                        <li key={option} className="rounded-lg bg-ink-50 px-3 py-1.5 text-sm text-ink-700 dark:bg-white/5 dark:text-ink-200">
                          {option}
                        </li>
                      ))}
                    </ul>
                    <button
                      className="btn-ghost mt-2 text-xs"
                      onClick={() => setRevealed((current) => ({ ...current, [question.id]: !current[question.id] }))}
                    >
                      {revealed[question.id] ? "Hide answer" : "Show answer"}
                    </button>
                    {revealed[question.id] ? (
                      <div className="mt-2 rounded-lg bg-emerald-50 px-3 py-2 text-sm text-emerald-800 dark:bg-emerald-500/10 dark:text-emerald-200">
                        <p className="font-semibold">{question.correct_answer}</p>
                        <p className="mt-1 text-xs">{question.explanation}</p>
                      </div>
                    ) : null}
                  </li>
                ))}
              </ol>
            )}
          </Card>
        </div>

        <div className="space-y-5">
          <Card>
            <SectionHeader title="Graded quizzes" />
            {topic.quizzes?.length ? (
              <ul className="space-y-3">
                {topic.quizzes.map((quiz: any) => (
                  <li key={quiz.id} className="rounded-xl border border-ink-200/70 p-3.5 dark:border-white/10">
                    <p className="text-sm font-semibold text-ink-900 dark:text-white">{quiz.title}</p>
                    <p className="muted mt-0.5">
                      {quiz.question_count} questions · {quiz.time_limit_minutes} min
                    </p>
                    <Link to={`/quiz/${quiz.id}`} className="btn-primary mt-3 w-full text-sm">
                      <Play size={14} /> Attempt
                    </Link>
                  </li>
                ))}
              </ul>
            ) : (
              <EmptyState title="No quiz for this topic" />
            )}
          </Card>

          {topic.prerequisites?.length ? (
            <Card>
              <SectionHeader title="Prerequisites" subtitle="Make sure these are solid first." />
              <ul className="space-y-2">
                {topic.prerequisites.map((prerequisite: any) => (
                  <li key={prerequisite.id}>
                    <Link
                      to={`/topics/${prerequisite.id}`}
                      className="flex items-center justify-between rounded-lg border border-ink-200/70 px-3 py-2 text-sm hover:border-brand-300 dark:border-white/10"
                    >
                      <span className="truncate text-ink-800 dark:text-ink-100">{prerequisite.name}</span>
                      <span className={toneClasses[masteryTone(prerequisite.mastery)].text}>
                        {Math.round(prerequisite.mastery)}%
                      </span>
                    </Link>
                  </li>
                ))}
              </ul>
            </Card>
          ) : null}

          <Card>
            <SectionHeader title="Your record" />
            <dl className="space-y-2 text-sm">
              {[
                ["Mastery", `${Math.round(progress.mastery || 0)}/100`],
                ["Attempts", progress.attempts || 0],
                ["Average score", progress.average_score != null ? `${Math.round(progress.average_score)}%` : "-"],
                ["Last score", progress.last_score != null ? `${Math.round(progress.last_score)}%` : "-"],
                ["Trend", `${(progress.trend || 0) > 0 ? "+" : ""}${Math.round(progress.trend || 0)}`],
              ].map(([label, value]) => (
                <div key={String(label)} className="flex items-center justify-between">
                  <dt className="text-ink-500 dark:text-ink-400">{label}</dt>
                  <dd className="font-semibold text-ink-900 dark:text-white">{value}</dd>
                </div>
              ))}
            </dl>
          </Card>
        </div>
      </div>
    </div>
  );
}

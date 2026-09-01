import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import {
  AlertTriangle, ArrowRight, Bot, CheckCircle2, Clock, Flame, ListChecks, Play, RefreshCw, Target, TrendingUp,
} from "lucide-react";
import { Card, EmptyState, ErrorState, MasteryChip, ProgressBar, SectionHeader, Skeleton, StatTile } from "../components/ui/Primitives";
import { ProgressLineChart, SubjectMasteryChart } from "../components/charts/Charts";
import { useToast } from "../context/ToastContext";
import { endpoints, errorMessage } from "../lib/api";
import { formatMinutes, masteryTone, subjectAccent, timeAgo, toneClasses } from "../lib/format";
import type { Dashboard as DashboardData } from "../lib/types";

export default function Dashboard() {
  const [data, setData] = useState<DashboardData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const toast = useToast();

  async function load() {
    setLoading(true);
    setError("");
    try {
      setData(await endpoints.dashboard());
    } catch (err) {
      setError(errorMessage(err));
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load();
  }, []);

  async function completeRecommendation(id: number) {
    setBusy(true);
    try {
      await endpoints.recommendationAction(id, "complete");
      toast.success("Nice - marked as done.");
      await load();
    } catch (err) {
      toast.error(errorMessage(err));
    } finally {
      setBusy(false);
    }
  }

  if (loading) {
    return (
      <div className="space-y-6">
        <Skeleton className="h-28 w-full" />
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {[0, 1, 2, 3].map((key) => (
            <Skeleton key={key} className="h-20" />
          ))}
        </div>
        <Skeleton className="h-72 w-full" />
      </div>
    );
  }

  if (error) return <ErrorState message={error} onRetry={load} />;
  if (!data) return null;

  const firstName = (data.student_name || "there").split(" ")[0];
  const tone = toneClasses[masteryTone(data.overall_mastery)];

  return (
    <div className="space-y-6">
      {/* Hero */}
      <section className="relative overflow-hidden rounded-2xl bg-gradient-to-br from-brand-600 via-brand-600 to-violet-600 p-6 text-white shadow-lift sm:p-8">
        <div className="absolute -right-16 -top-16 h-56 w-56 rounded-full bg-white/10 blur-2xl" />
        <div className="relative flex flex-wrap items-start justify-between gap-6">
          <div>
            <h1 className="font-display text-2xl font-semibold sm:text-3xl">
              {data.greeting}, {firstName} 👋
            </h1>
            <p className="mt-1 text-white/80">Here's what you should focus on today.</p>
            <div className="mt-5 flex flex-wrap gap-2">
              <Link to="/recommendations" className="btn bg-white text-brand-700 hover:bg-white/90">
                <ListChecks size={16} /> Today's plan
              </Link>
              <Link to="/chat" className="btn border border-white/30 text-white hover:bg-white/10">
                <Bot size={16} /> Ask the AI tutor
              </Link>
            </div>
          </div>
          <div className="min-w-[190px]">
            <p className="text-xs uppercase tracking-wide text-white/70">Overall progress</p>
            <p className="font-display text-5xl font-semibold">{Math.round(data.overall_mastery)}%</p>
            <div className="mt-2 h-2 w-full overflow-hidden rounded-full bg-white/20">
              <div className="h-full rounded-full bg-white transition-all duration-700" style={{ width: `${data.overall_mastery}%` }} />
            </div>
            <p className="mt-2 text-xs text-white/70">Academic year {data.academic_year}</p>
          </div>
        </div>
      </section>

      {/* Stats */}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <StatTile label="Study streak" value={`${data.stats.streak_days ?? 0} days`} icon={<Flame size={18} />} hint={`Goal ${data.stats.daily_goal_minutes ?? 45} min/day`} />
        <StatTile label="This week" value={formatMinutes(data.stats.study_minutes_7d ?? 0)} icon={<Clock size={18} />} hint="Time on the platform" />
        <StatTile label="Quizzes taken" value={data.stats.quizzes_taken ?? 0} icon={<Target size={18} />} hint={`${data.stats.average_accuracy ?? 0}% average`} />
        <StatTile label="Questions answered" value={data.stats.questions_answered ?? 0} icon={<TrendingUp size={18} />} hint={`${data.stats.accuracy ?? 0}% correct`} />
      </div>

      <div className="grid gap-6 lg:grid-cols-3">
        {/* Subjects */}
        <div className="lg:col-span-2">
          <Card>
            <SectionHeader
              title="Subjects"
              subtitle="Mastery is computed from your own quiz attempts."
              action={
                <Link to="/subjects" className="btn-ghost text-sm">
                  All subjects <ArrowRight size={15} />
                </Link>
              }
            />
            <div className="grid gap-3 sm:grid-cols-2">
              {data.subjects.map((subject) => (
                <Link
                  key={subject.subject_id}
                  to={`/subjects/${subject.subject_id}`}
                  className="group rounded-xl border border-ink-200/70 p-4 transition hover:border-brand-300 hover:bg-brand-50/40 dark:border-white/10 dark:hover:border-brand-500/40 dark:hover:bg-brand-500/5"
                >
                  <div className="mb-2 flex items-center gap-2">
                    <span
                      className={`grid h-9 w-9 place-items-center rounded-lg bg-gradient-to-br text-white ${
                        subjectAccent[subject.color] ?? subjectAccent.indigo
                      }`}
                    >
                      <span className="text-base">{subject.icon}</span>
                    </span>
                    <span className="min-w-0 flex-1">
                      <span className="block truncate text-sm font-semibold text-ink-900 dark:text-white">
                        {subject.subject_name}
                      </span>
                      <span className="block text-xs text-ink-500 dark:text-ink-400">
                        {subject.topics_started}/{subject.topics_total} topics started
                      </span>
                    </span>
                    <span className={`font-display text-lg font-semibold ${toneClasses[masteryTone(subject.mastery)].text}`}>
                      {Math.round(subject.mastery)}%
                    </span>
                  </div>
                  <ProgressBar value={subject.mastery} />
                  {subject.weak_topics > 0 ? (
                    <p className="mt-2 text-xs text-amber-600 dark:text-amber-400">
                      {subject.weak_topics} topic{subject.weak_topics > 1 ? "s" : ""} need attention
                    </p>
                  ) : (
                    <p className="mt-2 text-xs text-ink-500 dark:text-ink-400">
                      {subject.topics_mastered} mastered · {formatMinutes(subject.study_minutes)} studied
                    </p>
                  )}
                </Link>
              ))}
            </div>
          </Card>
        </div>

        {/* Needs attention */}
        <Card>
          <SectionHeader title="Needs attention" subtitle="Flagged from multiple signals." />
          {data.needs_attention.length === 0 ? (
            <EmptyState
              icon={<CheckCircle2 size={26} className="text-emerald-500" />}
              title="Nothing flagged yet"
              description="Take a few quizzes and we'll tell you exactly which topics need work - and why."
              action={<Link to="/quizzes" className="btn-primary text-sm">Take a quiz</Link>}
            />
          ) : (
            <ul className="space-y-3">
              {data.needs_attention.map((topic) => (
                <li key={topic.topic_id} className="rounded-xl border border-amber-200/70 bg-amber-50/50 p-3 dark:border-amber-500/20 dark:bg-amber-500/5">
                  <Link to={`/topics/${topic.topic_id}`} className="block">
                    <div className="flex items-start justify-between gap-2">
                      <div className="min-w-0">
                        <p className="truncate text-sm font-semibold text-ink-900 dark:text-white">{topic.topic_name}</p>
                        <p className="truncate text-xs text-ink-500 dark:text-ink-400">{topic.subject_name}</p>
                      </div>
                      <MasteryChip value={topic.mastery} />
                    </div>
                    <p className="mt-2 text-xs leading-relaxed text-amber-800 dark:text-amber-200">
                      <AlertTriangle size={12} className="mr-1 inline" />
                      {topic.weakness_reason}
                    </p>
                  </Link>
                </li>
              ))}
            </ul>
          )}
        </Card>
      </div>

      {/* Recommended */}
      <Card>
        <SectionHeader
          title="Recommended today"
          subtitle="Ranked by weakness, recency and what works for you."
          action={
            <Link to="/recommendations" className="btn-ghost text-sm">
              See all <ArrowRight size={15} />
            </Link>
          }
        />
        {data.recommended_today.length === 0 ? (
          <EmptyState title="No recommendations yet" description="Study a topic or take a quiz and your plan will appear here." />
        ) : (
          <ol className="space-y-3">
            {data.recommended_today.map((item, index) => (
              <li key={item.id} className="flex flex-wrap items-start gap-3 rounded-xl border border-ink-200/70 p-3.5 dark:border-white/10">
                <span className="grid h-7 w-7 shrink-0 place-items-center rounded-full bg-brand-100 text-xs font-bold text-brand-700 dark:bg-brand-500/20 dark:text-brand-200">
                  {index + 1}
                </span>
                <div className="min-w-0 flex-1">
                  <p className="text-sm font-semibold text-ink-900 dark:text-white">{item.title}</p>
                  <p className="muted mt-0.5">{item.reason}</p>
                  <p className="mt-1 text-xs text-ink-400">~{item.estimated_minutes} min · {item.kind}</p>
                </div>
                <div className="flex gap-2">
                  <Link to={item.action_url || "/subjects"} className="btn-primary text-sm">
                    <Play size={14} /> {item.action_label}
                  </Link>
                  <button className="btn-secondary text-sm" disabled={busy} onClick={() => completeRecommendation(item.id)}>
                    <CheckCircle2 size={14} /> Done
                  </button>
                </div>
              </li>
            ))}
          </ol>
        )}
      </Card>

      <div className="grid gap-6 lg:grid-cols-2">
        <Card>
          <SectionHeader title="Subject mastery" subtitle="Where you stand right now." />
          <SubjectMasteryChart data={data.subjects.map((s) => ({ subject_name: s.subject_name, mastery: s.mastery }))} />
        </Card>
        <Card>
          <SectionHeader
            title="Monthly improvement"
            subtitle={
              data.monthly_progress.length >= 2
                ? `${data.monthly_progress[0].label} ${Math.round(data.monthly_progress[0].mastery)}% → ${
                    data.monthly_progress[data.monthly_progress.length - 1].label
                  } ${Math.round(data.monthly_progress[data.monthly_progress.length - 1].mastery)}%`
                : "Your monthly trend appears as you study."
            }
          />
          {data.monthly_progress.length ? (
            <ProgressLineChart data={data.monthly_progress} />
          ) : (
            <EmptyState title="No history yet" description="Complete a quiz to start your monthly progress chart." />
          )}
        </Card>
      </div>

      {/* Continue learning */}
      <Card>
        <SectionHeader title="Continue learning" subtitle="Pick up where you left off." action={
          <button className="btn-ghost text-sm" onClick={load}><RefreshCw size={14} /> Refresh</button>
        } />
        {data.continue_learning.length === 0 ? (
          <EmptyState
            title="Nothing opened yet"
            description="Open any topic and it will show up here for quick access."
            action={<Link to="/subjects" className="btn-primary text-sm">Browse subjects</Link>}
          />
        ) : (
          <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
            {data.continue_learning.map((item: any) => (
              <Link
                key={item.topic_id}
                to={`/topics/${item.topic_id}`}
                className="card card-hover p-4"
              >
                <span className="text-lg">{item.icon}</span>
                <p className="mt-1.5 line-clamp-2 text-sm font-semibold text-ink-900 dark:text-white">{item.topic_name}</p>
                <p className="muted mt-0.5 truncate">{item.subject_name}</p>
                <p className="mt-2 text-xs text-ink-400">{timeAgo(item.last_seen)} · {formatMinutes(item.minutes_spent)}</p>
              </Link>
            ))}
          </div>
        )}
      </Card>

      {data.ai_status?.mode === "offline" ? (
        <p className="rounded-xl border border-amber-200 bg-amber-50 px-4 py-3 text-xs text-amber-800 dark:border-amber-500/20 dark:bg-amber-500/10 dark:text-amber-200">
          <Bot size={14} className="mr-1 inline" />
          AI tutor is running in offline mode - answers come from your syllabus content and your own performance
          data. Start Ollama to enable the local language model.
        </p>
      ) : null}
    </div>
  );
}

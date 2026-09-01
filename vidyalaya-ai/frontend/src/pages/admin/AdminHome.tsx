import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import {
  Activity, AlertTriangle, BarChart3, BookOpen, Database, GraduationCap, RefreshCw, Users,
} from "lucide-react";
import { ActivityBarChart, SubjectMasteryChart } from "../../components/charts/Charts";
import { Card, EmptyState, ErrorState, SectionHeader, Skeleton, StatTile } from "../../components/ui/Primitives";
import { useToast } from "../../context/ToastContext";
import { endpoints, errorMessage } from "../../lib/api";
import { eventLabels, masteryTone, timeAgo, toneClasses } from "../../lib/format";

export default function AdminHome() {
  const toast = useToast();
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [reindexing, setReindexing] = useState(false);

  async function load() {
    setLoading(true);
    setError("");
    try {
      setData(await endpoints.adminAnalytics());
    } catch (err) {
      setError(errorMessage(err));
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load();
  }, []);

  async function reindex() {
    setReindexing(true);
    try {
      const result = await endpoints.reindex();
      toast.success(`Rebuilt the AI index: ${result.indexed} passages.`);
    } catch (err) {
      toast.error(errorMessage(err));
    } finally {
      setReindexing(false);
    }
  }

  if (loading) return <Skeleton className="h-96 w-full" />;
  if (error) return <ErrorState message={error} onRetry={load} />;
  if (!data) return null;

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <h1 className="font-display text-2xl font-semibold text-ink-900 dark:text-white">Teacher workspace</h1>
          <p className="muted mt-1">Class overview for academic year {data.academic_year}.</p>
        </div>
        <div className="flex gap-2">
          <button className="btn-secondary" onClick={reindex} disabled={reindexing}>
            <Database size={15} className={reindexing ? "animate-pulse" : ""} /> Rebuild AI index
          </button>
          <Link to="/admin/analytics" className="btn-primary">
            <BarChart3 size={15} /> Full analytics
          </Link>
        </div>
      </div>

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <StatTile label="Students" value={data.students} icon={<Users size={18} />} hint={`${data.teachers} staff accounts`} />
        <StatTile label="Class average" value={`${Math.round(data.class_average)}%`} icon={<GraduationCap size={18} />} hint="Mean subject mastery" />
        <StatTile label="Quiz attempts" value={data.quiz_stats.attempts} icon={<Activity size={18} />} hint={`${data.quiz_stats.average_accuracy}% average`} />
        <StatTile label="Content" value={`${data.catalog.topics} topics`} icon={<BookOpen size={18} />} hint={`${data.catalog.chapters} chapters · ${data.catalog.resources} resources`} />
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        <Card>
          <SectionHeader title="Subject performance" subtitle="Average mastery across all students." />
          <SubjectMasteryChart
            data={data.subject_performance.map((item: any) => ({
              subject_name: item.subject_name,
              mastery: item.average_mastery,
            }))}
          />
        </Card>
        <Card>
          <SectionHeader title="Most common weak topics" subtitle="Where the class needs teaching support." />
          {data.common_weak_topics.length === 0 ? (
            <EmptyState title="No weak topics detected yet" />
          ) : (
            <ul className="space-y-2">
              {data.common_weak_topics.map((topic: any) => (
                <li key={topic.topic_id} className="flex items-center justify-between gap-3 rounded-xl border border-ink-200/70 px-3 py-2.5 dark:border-white/10">
                  <div className="min-w-0">
                    <p className="truncate text-sm font-medium text-ink-900 dark:text-white">{topic.topic_name}</p>
                    <p className="muted">{topic.subject_name}</p>
                  </div>
                  <div className="shrink-0 text-right">
                    <p className="text-sm font-semibold text-amber-600 dark:text-amber-400">
                      {topic.students_affected} students
                    </p>
                    <p className="text-xs text-ink-400">avg {Math.round(topic.average_mastery)}/100</p>
                  </div>
                </li>
              ))}
            </ul>
          )}
        </Card>
      </div>

      <div className="grid gap-6 lg:grid-cols-3">
        <Card className="lg:col-span-2">
          <SectionHeader title="Recent activity" subtitle="Live feed from the platform." action={
            <button className="btn-ghost text-sm" onClick={load}><RefreshCw size={14} /> Refresh</button>
          } />
          {data.recent_activity.length === 0 ? (
            <EmptyState title="No activity yet" />
          ) : (
            <ul className="divide-y divide-ink-200/70 dark:divide-white/10">
              {data.recent_activity.map((event: any) => (
                <li key={event.id} className="flex items-center gap-3 py-2.5 text-sm">
                  <span className="min-w-0 flex-1 truncate">
                    <span className="font-medium text-ink-900 dark:text-white">{event.student_name}</span>
                    <span className="text-ink-500 dark:text-ink-400"> · {eventLabels[event.event_type] ?? event.event_type}</span>
                    {event.topic_name ? <span className="text-ink-400"> · {event.topic_name}</span> : null}
                  </span>
                  <span className="shrink-0 text-xs text-ink-400">{timeAgo(event.created_at)}</span>
                </li>
              ))}
            </ul>
          )}
        </Card>

        <Card>
          <SectionHeader title="Top performers" />
          <ul className="space-y-2">
            {data.leaderboard.map((student: any, index: number) => (
              <li key={student.student_id} className="flex items-center gap-3 rounded-lg bg-ink-50 px-3 py-2 dark:bg-white/5">
                <span className="grid h-7 w-7 place-items-center rounded-full bg-brand-100 text-xs font-bold text-brand-700 dark:bg-brand-500/20 dark:text-brand-200">
                  {index + 1}
                </span>
                <Link to="/admin/students" className="min-w-0 flex-1 truncate text-sm text-ink-800 hover:underline dark:text-ink-100">
                  {student.name}
                </Link>
                <span className={`text-sm font-semibold ${toneClasses[masteryTone(student.mastery)].text}`}>
                  {Math.round(student.mastery)}%
                </span>
              </li>
            ))}
          </ul>
        </Card>
      </div>

      <Card>
        <SectionHeader title="Platform activity (14 days)" />
        {data.activity_trend?.length ? (
          <ActivityBarChart data={data.activity_trend} />
        ) : (
          <EmptyState title="No activity recorded yet" />
        )}
      </Card>

      <Card>
        <SectionHeader title="Integrations" subtitle="Everything runs locally and free." />
        <div className="grid gap-3 sm:grid-cols-2">
          <div className="rounded-xl bg-ink-50 p-3 dark:bg-white/5">
            <p className="text-xs uppercase tracking-wide text-ink-500 dark:text-ink-400">ML models in use</p>
            <p className="mt-1 text-sm text-ink-800 dark:text-ink-100">
              {Object.entries(data.ml_models).map(([key, value]) => `${key}: ${value}`).join(" · ")}
            </p>
          </div>
          <div className="rounded-xl bg-ink-50 p-3 dark:bg-white/5">
            <p className="text-xs uppercase tracking-wide text-ink-500 dark:text-ink-400">Moodle</p>
            <p className="mt-1 text-sm text-ink-800 dark:text-ink-100">
              {data.moodle.enabled ? "Connected" : "Integration layer ready (disabled)"}
            </p>
            <p className="mt-1 text-xs text-ink-500 dark:text-ink-400">{data.moodle.note}</p>
          </div>
        </div>
      </Card>
    </div>
  );
}

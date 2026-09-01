import { useEffect, useState } from "react";
import { AlertTriangle, BarChart3, Percent, Target, Users } from "lucide-react";
import { ActivityBarChart, DifficultyBars, SubjectMasteryChart } from "../../components/charts/Charts";
import { Card, EmptyState, ErrorState, ProgressBar, SectionHeader, Skeleton, StatTile } from "../../components/ui/Primitives";
import { endpoints, errorMessage } from "../../lib/api";
import { masteryTone, toneClasses } from "../../lib/format";

export default function AdminAnalytics() {
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

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

  if (loading) return <Skeleton className="h-96 w-full" />;
  if (error) return <ErrorState message={error} onRetry={load} />;
  if (!data) return null;

  return (
    <div className="space-y-6">
      <div>
        <h1 className="font-display text-2xl font-semibold text-ink-900 dark:text-white">Class analytics</h1>
        <p className="muted mt-1">Academic year {data.academic_year} · every number is computed from stored attempts.</p>
      </div>

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <StatTile label="Students" value={data.students} icon={<Users size={18} />} />
        <StatTile label="Class average" value={`${Math.round(data.class_average)}%`} icon={<BarChart3 size={18} />} />
        <StatTile label="Quiz pass rate" value={`${data.quiz_stats.pass_rate}%`} icon={<Percent size={18} />} hint={`${data.quiz_stats.attempts} attempts`} />
        <StatTile label="Question bank" value={data.quiz_stats.questions} icon={<Target size={18} />} hint={`${data.quiz_stats.quizzes_published} quizzes published`} />
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        <Card>
          <SectionHeader title="Average mastery by subject" />
          <SubjectMasteryChart
            data={data.subject_performance.map((item: any) => ({
              subject_name: item.subject_name,
              mastery: item.average_mastery,
            }))}
          />
        </Card>
        <Card>
          <SectionHeader title="Platform activity (14 days)" />
          {data.activity_trend?.length ? <ActivityBarChart data={data.activity_trend} /> : <EmptyState title="No activity yet" />}
        </Card>
      </div>

      <Card>
        <SectionHeader title="Subject breakdown" subtitle="Students tracked per subject and their average mastery." />
        <ul className="space-y-3">
          {data.subject_performance.map((subject: any) => (
            <li key={subject.subject_id}>
              <div className="mb-1 flex items-center justify-between text-sm">
                <span className="text-ink-800 dark:text-ink-100">
                  {subject.icon} {subject.subject_name}
                  <span className="ml-2 text-xs text-ink-400">{subject.students_tracked} students</span>
                </span>
                <span className={`font-semibold ${toneClasses[masteryTone(subject.average_mastery)].text}`}>
                  {Math.round(subject.average_mastery)}%
                </span>
              </div>
              <ProgressBar value={subject.average_mastery} />
            </li>
          ))}
        </ul>
      </Card>

      <Card>
        <SectionHeader title="Topics the class struggles with" subtitle="Ranked by how many students are flagged." />
        {data.common_weak_topics.length === 0 ? (
          <EmptyState title="No weak topics detected" />
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full min-w-[520px] text-sm">
              <thead>
                <tr className="border-b border-ink-200/70 text-left text-xs uppercase tracking-wide text-ink-500 dark:border-white/10 dark:text-ink-400">
                  <th className="py-2 pr-3">Topic</th>
                  <th className="py-2 pr-3">Subject</th>
                  <th className="py-2 pr-3">Students affected</th>
                  <th className="py-2">Average mastery</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-ink-200/70 dark:divide-white/10">
                {data.common_weak_topics.map((topic: any) => (
                  <tr key={topic.topic_id}>
                    <td className="py-2.5 pr-3 font-medium text-ink-900 dark:text-white">
                      <AlertTriangle size={13} className="mr-1 inline text-amber-500" />
                      {topic.topic_name}
                    </td>
                    <td className="py-2.5 pr-3 text-ink-500 dark:text-ink-400">{topic.subject_name}</td>
                    <td className="py-2.5 pr-3 text-ink-700 dark:text-ink-200">{topic.students_affected}</td>
                    <td className={`py-2.5 font-semibold ${toneClasses[masteryTone(topic.average_mastery)].text}`}>
                      {Math.round(topic.average_mastery)}/100
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Card>
    </div>
  );
}

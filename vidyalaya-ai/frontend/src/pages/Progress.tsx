import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { AlertTriangle, Award, CalendarRange, TrendingUp } from "lucide-react";
import { ActivityBarChart, LearningProfileRadar, ProgressLineChart, SubjectMasteryChart } from "../components/charts/Charts";
import { Card, EmptyState, ErrorState, MasteryChip, ProgressBar, SectionHeader, Skeleton, StatTile } from "../components/ui/Primitives";
import { endpoints, errorMessage } from "../lib/api";
import { formatDate, formatMinutes, masteryTone, toneClasses } from "../lib/format";

export default function Progress() {
  const [data, setData] = useState<any>(null);
  const [years, setYears] = useState<any[]>([]);
  const [yearId, setYearId] = useState<number | undefined>(undefined);
  const [profile, setProfile] = useState<any>(null);
  const [heatmap, setHeatmap] = useState<any[]>([]);
  const [topicMastery, setTopicMastery] = useState<any[]>([]);
  const [masterySubject, setMasterySubject] = useState<string>("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  async function load(selectedYear?: number) {
    setLoading(true);
    setError("");
    try {
      const [progress, yearList, learningProfile, activity, topics] = await Promise.all([
        endpoints.progress(selectedYear),
        endpoints.years(),
        endpoints.learningProfile(),
        endpoints.heatmap(30),
        endpoints.mastery(),
      ]);
      setData(progress);
      setYears(yearList);
      setProfile(learningProfile);
      setHeatmap(activity);
      setTopicMastery(topics);
    } catch (err) {
      setError(errorMessage(err));
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load(yearId);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [yearId]);

  if (loading) return <Skeleton className="h-96 w-full" />;
  if (error) return <ErrorState message={error} onRetry={() => load(yearId)} />;
  if (!data) return null;

  const monthly = data.monthly_progress || [];
  const improvement =
    monthly.length >= 2 ? Math.round(monthly[monthly.length - 1].mastery - monthly[0].mastery) : 0;

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <h1 className="font-display text-2xl font-semibold text-ink-900 dark:text-white">Your progress</h1>
          <p className="muted mt-1">Academic year {data.academic_year} · history is never deleted.</p>
        </div>
        <label className="flex items-center gap-2">
          <CalendarRange size={16} className="text-ink-400" />
          <select
            className="input w-44"
            value={yearId ?? data.academic_year_id}
            onChange={(event) => setYearId(Number(event.target.value))}
            aria-label="Academic year"
          >
            {years.map((year) => (
              <option key={year.id} value={year.id}>
                {year.label} {year.is_current ? "(current)" : ""}
              </option>
            ))}
          </select>
        </label>
      </div>

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <StatTile label="Overall mastery" value={`${Math.round(data.overall_mastery)}%`} icon={<Award size={18} />} />
        <StatTile
          label="Improvement"
          value={`${improvement >= 0 ? "+" : ""}${improvement}%`}
          icon={<TrendingUp size={18} />}
          hint={monthly.length >= 2 ? `${monthly[0].label} → ${monthly[monthly.length - 1].label}` : "Needs more history"}
        />
        <StatTile label="Quizzes taken" value={data.quizzes_taken} hint={`${data.accuracy}% answer accuracy`} />
        <StatTile label="Study time (7d)" value={formatMinutes(data.study_minutes_7d)} hint={`${data.streak_days} day streak`} />
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        <Card>
          <SectionHeader title="Subject mastery" />
          <SubjectMasteryChart data={data.subjects.map((s: any) => ({ subject_name: s.subject_name, mastery: s.mastery }))} />
        </Card>
        <Card>
          <SectionHeader
            title="Monthly improvement"
            subtitle={
              improvement !== 0 && monthly.length >= 2
                ? `Your mastery ${improvement > 0 ? "improved" : "dropped"} by ${Math.abs(improvement)}% since ${monthly[0].label}.`
                : undefined
            }
          />
          {monthly.length ? <ProgressLineChart data={monthly} /> : <EmptyState title="No monthly history yet" />}
        </Card>
      </div>

      <div className="grid gap-6 lg:grid-cols-3">
        <Card className="lg:col-span-2">
          <SectionHeader title="Topics that need attention" subtitle="Each one comes with the reason it was flagged." />
          {data.weak_topics.length === 0 ? (
            <EmptyState title="No weak topics" description="Keep going - nothing is currently flagged." />
          ) : (
            <ul className="space-y-2">
              {data.weak_topics.map((topic: any) => (
                <li key={topic.topic_id} className="rounded-xl border border-ink-200/70 p-3.5 dark:border-white/10">
                  <div className="flex flex-wrap items-center justify-between gap-2">
                    <Link to={`/topics/${topic.topic_id}`} className="font-medium text-ink-900 hover:underline dark:text-white">
                      {topic.topic_name}
                    </Link>
                    <div className="flex items-center gap-2">
                      <span className="muted">{topic.subject_name}</span>
                      <MasteryChip value={topic.mastery} />
                    </div>
                  </div>
                  <ProgressBar value={topic.mastery} className="mt-2" />
                  <p className="mt-2 text-xs text-amber-700 dark:text-amber-300">
                    <AlertTriangle size={12} className="mr-1 inline" />
                    {topic.weakness_reason}
                  </p>
                </li>
              ))}
            </ul>
          )}
        </Card>

        <Card>
          <SectionHeader title="Strongest topics" />
          {data.strong_topics.length === 0 ? (
            <EmptyState title="Take a quiz to see your strengths" />
          ) : (
            <ul className="space-y-2">
              {data.strong_topics.map((topic: any) => (
                <li key={topic.topic_id} className="flex items-center justify-between gap-2 rounded-lg bg-ink-50 px-3 py-2 dark:bg-white/5">
                  <Link to={`/topics/${topic.topic_id}`} className="min-w-0 flex-1 truncate text-sm text-ink-800 hover:underline dark:text-ink-100">
                    {topic.topic_name}
                  </Link>
                  <span className={`text-sm font-semibold ${toneClasses[masteryTone(topic.mastery)].text}`}>
                    {Math.round(topic.mastery)}
                  </span>
                </li>
              ))}
            </ul>
          )}
        </Card>
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        <Card>
          <SectionHeader
            title="Resource effectiveness"
            subtitle="Which study format actually improves your scores."
          />
          {profile ? <LearningProfileRadar profile={profile} /> : null}
          <p className="muted mt-3 text-xs">{profile?.note}</p>
        </Card>
        <Card>
          <SectionHeader title="Study activity (30 days)" subtitle="Minutes tracked per day." />
          {heatmap.length ? <ActivityBarChart data={heatmap} /> : <EmptyState title="No activity recorded yet" />}
        </Card>
      </div>

      <Card>
        <SectionHeader
          title="Every topic you have been assessed on"
          subtitle={`${topicMastery.length} topics with a mastery score.`}
          action={
            <select
              className="input w-44"
              value={masterySubject}
              onChange={(event) => setMasterySubject(event.target.value)}
              aria-label="Filter topics by subject"
            >
              <option value="">All subjects</option>
              {data.subjects.map((subject: any) => (
                <option key={subject.subject_id} value={subject.subject_id}>
                  {subject.subject_name}
                </option>
              ))}
            </select>
          }
        />
        {topicMastery.length === 0 ? (
          <EmptyState title="No topic scores yet" description="Take a quiz to start building your topic map." />
        ) : (
          <div className="max-h-96 overflow-y-auto">
            <table className="w-full min-w-[560px] text-sm">
              <thead className="sticky top-0 bg-white dark:bg-ink-900">
                <tr className="border-b border-ink-200/70 text-left text-xs uppercase tracking-wide text-ink-500 dark:border-white/10 dark:text-ink-400">
                  <th className="py-2 pr-3">Topic</th>
                  <th className="py-2 pr-3">Subject</th>
                  <th className="py-2 pr-3">Attempts</th>
                  <th className="py-2 pr-3">Average</th>
                  <th className="py-2">Mastery</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-ink-200/70 dark:divide-white/10">
                {topicMastery
                  .filter((row: any) => !masterySubject || String(row.subject_id) === masterySubject)
                  .map((row: any) => (
                    <tr key={row.topic_id}>
                      <td className="py-2.5 pr-3">
                        <Link to={`/topics/${row.topic_id}`} className="font-medium text-ink-800 hover:underline dark:text-ink-100">
                          {row.topic_name}
                        </Link>
                        {row.is_weak ? (
                          <span className="chip ml-2 bg-amber-50 text-amber-700 dark:bg-amber-500/15 dark:text-amber-300">
                            needs work
                          </span>
                        ) : null}
                      </td>
                      <td className="py-2.5 pr-3 text-ink-500 dark:text-ink-400">{row.subject_name}</td>
                      <td className="py-2.5 pr-3 text-ink-600 dark:text-ink-300">{row.attempts}</td>
                      <td className="py-2.5 pr-3 text-ink-600 dark:text-ink-300">
                        {row.average_score != null ? `${Math.round(row.average_score)}%` : "-"}
                      </td>
                      <td className="w-40 py-2.5">
                        <div className="flex items-center gap-2">
                          <ProgressBar value={row.mastery} />
                          <span className={`w-9 text-right text-xs font-semibold ${toneClasses[masteryTone(row.mastery)].text}`}>
                            {Math.round(row.mastery)}
                          </span>
                        </div>
                      </td>
                    </tr>
                  ))}
              </tbody>
            </table>
          </div>
        )}
      </Card>

      <Card>
        <SectionHeader title="Quiz history" subtitle="Every attempt is stored." />
        {data.quiz_history.length === 0 ? (
          <EmptyState title="No attempts yet" action={<Link to="/quizzes" className="btn-primary text-sm">Take your first quiz</Link>} />
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full min-w-[560px] text-sm">
              <thead>
                <tr className="border-b border-ink-200/70 text-left text-xs uppercase tracking-wide text-ink-500 dark:border-white/10 dark:text-ink-400">
                  <th className="py-2 pr-3">Quiz</th>
                  <th className="py-2 pr-3">Subject</th>
                  <th className="py-2 pr-3">Score</th>
                  <th className="py-2">Date</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-ink-200/70 dark:divide-white/10">
                {[...data.quiz_history].reverse().map((attempt: any) => (
                  <tr key={attempt.attempt_id}>
                    <td className="py-2.5 pr-3 font-medium text-ink-800 dark:text-ink-100">{attempt.quiz_title}</td>
                    <td className="py-2.5 pr-3 text-ink-500 dark:text-ink-400">{attempt.subject_name}</td>
                    <td className={`py-2.5 pr-3 font-semibold ${toneClasses[masteryTone(attempt.accuracy)].text}`}>
                      {Math.round(attempt.accuracy)}%
                    </td>
                    <td className="py-2.5 text-ink-500 dark:text-ink-400">{formatDate(attempt.submitted_at)}</td>
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

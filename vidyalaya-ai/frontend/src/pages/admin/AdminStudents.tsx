import { useEffect, useState } from "react";
import { AlertTriangle, Search, Users, X } from "lucide-react";
import { Card, EmptyState, ErrorState, ProgressBar, SectionHeader, Skeleton } from "../../components/ui/Primitives";
import { endpoints, errorMessage } from "../../lib/api";
import { masteryTone, timeAgo, toneClasses } from "../../lib/format";

export default function AdminStudents() {
  const [students, setStudents] = useState<any[]>([]);
  const [selected, setSelected] = useState<any>(null);
  const [query, setQuery] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  async function load(search?: string) {
    setLoading(true);
    setError("");
    try {
      setStudents(await endpoints.adminStudents(search));
    } catch (err) {
      setError(errorMessage(err));
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load();
  }, []);

  async function open(id: number) {
    try {
      setSelected(await endpoints.adminStudent(id));
    } catch (err) {
      setError(errorMessage(err));
    }
  }

  return (
    <div className="space-y-5">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <h1 className="font-display text-2xl font-semibold text-ink-900 dark:text-white">Students</h1>
          <p className="muted mt-1">{students.length} students enrolled.</p>
        </div>
        <form
          className="relative w-full sm:w-72"
          onSubmit={(event) => {
            event.preventDefault();
            load(query);
          }}
        >
          <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-ink-400" />
          <input
            className="input pl-9"
            placeholder="Search by name or email"
            value={query}
            onChange={(event) => setQuery(event.target.value)}
            aria-label="Search students"
          />
        </form>
      </div>

      {loading ? (
        <Skeleton className="h-80 w-full" />
      ) : error ? (
        <ErrorState message={error} onRetry={() => load()} />
      ) : students.length === 0 ? (
        <EmptyState title="No students found" icon={<Users size={26} />} />
      ) : (
        <Card className="p-0">
          <div className="overflow-x-auto">
            <table className="w-full min-w-[720px] text-sm">
              <thead>
                <tr className="border-b border-ink-200/70 text-left text-xs uppercase tracking-wide text-ink-500 dark:border-white/10 dark:text-ink-400">
                  <th className="px-5 py-3">Student</th>
                  <th className="px-3 py-3">Mastery</th>
                  <th className="px-3 py-3">Weak topics</th>
                  <th className="px-3 py-3">Quizzes</th>
                  <th className="px-3 py-3">Last active</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-ink-200/70 dark:divide-white/10">
                {students.map((student) => (
                  <tr
                    key={student.id}
                    className="cursor-pointer transition hover:bg-ink-50 dark:hover:bg-white/5"
                    onClick={() => open(student.id)}
                  >
                    <td className="px-5 py-3">
                      <p className="font-medium text-ink-900 dark:text-white">{student.name}</p>
                      <p className="text-xs text-ink-500 dark:text-ink-400">{student.email}</p>
                    </td>
                    <td className="w-44 px-3 py-3">
                      <div className="flex items-center gap-2">
                        <ProgressBar value={student.overall_mastery} />
                        <span className={`w-10 text-right text-xs font-semibold ${toneClasses[masteryTone(student.overall_mastery)].text}`}>
                          {Math.round(student.overall_mastery)}%
                        </span>
                      </div>
                    </td>
                    <td className="px-3 py-3">
                      <span className={student.weak_topics > 0 ? "text-amber-600 dark:text-amber-400" : "text-ink-500"}>
                        {student.weak_topics}
                      </span>
                    </td>
                    <td className="px-3 py-3 text-ink-600 dark:text-ink-300">{student.quizzes_taken}</td>
                    <td className="px-3 py-3 text-ink-500 dark:text-ink-400">{timeAgo(student.last_active_at)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Card>
      )}

      {selected ? (
        <div className="fixed inset-0 z-50 flex items-end justify-center bg-ink-900/50 p-0 backdrop-blur-sm sm:items-center sm:p-6" onClick={() => setSelected(null)}>
          <div
            className="max-h-[90vh] w-full max-w-2xl overflow-y-auto rounded-t-2xl bg-white p-6 dark:bg-ink-900 sm:rounded-2xl"
            onClick={(event) => event.stopPropagation()}
          >
            <div className="mb-4 flex items-start justify-between gap-3">
              <div>
                <h2 className="font-display text-xl font-semibold text-ink-900 dark:text-white">{selected.name}</h2>
                <p className="muted">{selected.email} · Class {selected.class_level} · {selected.school}</p>
              </div>
              <button onClick={() => setSelected(null)} aria-label="Close"><X size={18} /></button>
            </div>

            <SectionHeader title="Subject mastery" />
            <ul className="mb-5 space-y-2">
              {selected.subjects.map((subject: any) => (
                <li key={subject.subject_id}>
                  <div className="mb-1 flex items-center justify-between text-sm">
                    <span className="text-ink-700 dark:text-ink-200">{subject.icon} {subject.subject_name}</span>
                    <span className="font-semibold text-ink-900 dark:text-white">{Math.round(subject.mastery)}%</span>
                  </div>
                  <ProgressBar value={subject.mastery} />
                </li>
              ))}
            </ul>

            <SectionHeader title="Weak topics" />
            {selected.weak_topics.length === 0 ? (
              <p className="muted mb-5">No weak topics detected.</p>
            ) : (
              <ul className="mb-5 space-y-2">
                {selected.weak_topics.map((topic: any) => (
                  <li key={topic.topic_id} className="rounded-xl border border-amber-200 bg-amber-50/60 p-3 text-sm dark:border-amber-500/20 dark:bg-amber-500/5">
                    <p className="font-medium text-ink-900 dark:text-white">
                      <AlertTriangle size={13} className="mr-1 inline text-amber-500" />
                      {topic.topic_name} · {Math.round(topic.mastery)}/100
                    </p>
                    <p className="mt-1 text-xs text-amber-800 dark:text-amber-200">{topic.weakness_reason}</p>
                  </li>
                ))}
              </ul>
            )}

            <SectionHeader title="Recent attempts" />
            <ul className="divide-y divide-ink-200/70 dark:divide-white/10">
              {selected.recent_attempts.map((attempt: any) => (
                <li key={attempt.attempt_id} className="flex items-center justify-between py-2 text-sm">
                  <span className="min-w-0 flex-1 truncate text-ink-700 dark:text-ink-200">{attempt.quiz_title}</span>
                  <span className={`font-semibold ${toneClasses[masteryTone(attempt.accuracy)].text}`}>
                    {Math.round(attempt.accuracy)}%
                  </span>
                </li>
              ))}
            </ul>
          </div>
        </div>
      ) : null}
    </div>
  );
}

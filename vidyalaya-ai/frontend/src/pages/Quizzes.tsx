import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { ClipboardList, Play, Search } from "lucide-react";
import { Card, EmptyState, ErrorState, Skeleton } from "../components/ui/Primitives";
import { endpoints, errorMessage } from "../lib/api";
import { masteryTone, toneClasses } from "../lib/format";

export default function Quizzes() {
  const [quizzes, setQuizzes] = useState<any[]>([]);
  const [subjects, setSubjects] = useState<any[]>([]);
  const [subjectId, setSubjectId] = useState<string>("");
  const [query, setQuery] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  async function load() {
    setLoading(true);
    setError("");
    try {
      const [quizList, subjectList] = await Promise.all([
        endpoints.quizzes({ limit: 200 }),
        endpoints.subjects(),
      ]);
      setQuizzes(quizList);
      setSubjects(subjectList);
    } catch (err) {
      setError(errorMessage(err));
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load();
  }, []);

  const filtered = useMemo(
    () =>
      quizzes.filter((quiz) => {
        const matchesSubject = !subjectId || String(quiz.subject_id) === subjectId;
        const matchesQuery = quiz.title.toLowerCase().includes(query.trim().toLowerCase());
        return matchesSubject && matchesQuery;
      }),
    [quizzes, subjectId, query],
  );

  return (
    <div className="space-y-5">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <h1 className="font-display text-2xl font-semibold text-ink-900 dark:text-white">Quizzes</h1>
          <p className="muted mt-1">Every attempt updates your mastery, weak topics and recommendations.</p>
        </div>
        <div className="flex w-full flex-wrap gap-2 sm:w-auto">
          <label className="relative flex-1 sm:w-60">
            <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-ink-400" />
            <input
              className="input pl-9"
              placeholder="Search quizzes"
              value={query}
              onChange={(event) => setQuery(event.target.value)}
              aria-label="Search quizzes"
            />
          </label>
          <select className="input sm:w-48" value={subjectId} onChange={(event) => setSubjectId(event.target.value)} aria-label="Filter by subject">
            <option value="">All subjects</option>
            {subjects.map((subject) => (
              <option key={subject.id} value={subject.id}>
                {subject.name}
              </option>
            ))}
          </select>
        </div>
      </div>

      {loading ? (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {[0, 1, 2, 3, 4, 5].map((key) => (
            <Skeleton key={key} className="h-40" />
          ))}
        </div>
      ) : error ? (
        <ErrorState message={error} onRetry={load} />
      ) : filtered.length === 0 ? (
        <EmptyState title="No quizzes found" description="Try another subject or search term." icon={<ClipboardList size={26} />} />
      ) : (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {filtered.map((quiz) => (
            <Card key={quiz.id} className="card-hover flex flex-col">
              <div className="flex items-start gap-2">
                <span className="text-xl">{quiz.icon}</span>
                <div className="min-w-0 flex-1">
                  <h2 className="line-clamp-2 font-semibold text-ink-900 dark:text-white">{quiz.title}</h2>
                  <p className="muted mt-0.5">{quiz.subject_name}</p>
                </div>
              </div>
              <p className="muted mt-3">
                {quiz.question_count} questions · {quiz.time_limit_minutes} min · {quiz.difficulty}
              </p>
              {quiz.attempts_count > 0 ? (
                <p className="mt-2 text-sm">
                  <span className="text-ink-500 dark:text-ink-400">Best score </span>
                  <span className={`font-semibold ${toneClasses[masteryTone(quiz.best_score || 0)].text}`}>
                    {Math.round(quiz.best_score || 0)}%
                  </span>
                  <span className="text-ink-400"> · {quiz.attempts_count} attempts</span>
                </p>
              ) : (
                <p className="mt-2 text-sm text-ink-400">Not attempted yet</p>
              )}
              <Link to={`/quiz/${quiz.id}`} className="btn-primary mt-4 text-sm">
                <Play size={14} /> {quiz.attempts_count > 0 ? "Retake quiz" : "Start quiz"}
              </Link>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}

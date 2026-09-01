import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { BookOpen, ExternalLink, Search } from "lucide-react";
import { Card, EmptyState, ErrorState, ProgressBar, Skeleton } from "../components/ui/Primitives";
import { endpoints, errorMessage } from "../lib/api";
import { formatMinutes, masteryTone, subjectAccent, toneClasses } from "../lib/format";

export default function Subjects() {
  const [subjects, setSubjects] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [query, setQuery] = useState("");

  async function load() {
    setLoading(true);
    setError("");
    try {
      setSubjects(await endpoints.subjects());
    } catch (err) {
      setError(errorMessage(err));
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load();
  }, []);

  const filtered = subjects.filter((subject) =>
    subject.name.toLowerCase().includes(query.trim().toLowerCase()),
  );

  return (
    <div className="space-y-5">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <h1 className="font-display text-2xl font-semibold text-ink-900 dark:text-white">Your subjects</h1>
          <p className="muted mt-1">Class 12 · NCERT aligned chapters, topics and resources.</p>
        </div>
        <label className="relative w-full sm:w-72">
          <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-ink-400" />
          <input
            className="input pl-9"
            placeholder="Search subjects"
            value={query}
            onChange={(event) => setQuery(event.target.value)}
            aria-label="Search subjects"
          />
        </label>
      </div>

      {loading ? (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {[0, 1, 2, 3, 4, 5].map((key) => (
            <Skeleton key={key} className="h-48" />
          ))}
        </div>
      ) : error ? (
        <ErrorState message={error} onRetry={load} />
      ) : filtered.length === 0 ? (
        <EmptyState title="No subjects found" description="Try a different search term." icon={<BookOpen size={26} />} />
      ) : (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {filtered.map((subject) => (
            <Card key={subject.id} className="card-hover flex flex-col">
              <div className="flex items-start gap-3">
                <span
                  className={`grid h-12 w-12 place-items-center rounded-xl bg-gradient-to-br text-xl text-white ${
                    subjectAccent[subject.color] ?? subjectAccent.indigo
                  }`}
                >
                  {subject.icon}
                </span>
                <div className="min-w-0 flex-1">
                  <h2 className="font-display font-semibold text-ink-900 dark:text-white">{subject.name}</h2>
                  <p className="muted line-clamp-2 mt-0.5">{subject.description}</p>
                </div>
              </div>

              <dl className="mt-4 grid grid-cols-3 gap-2 text-center">
                <div className="rounded-lg bg-ink-50 py-2 dark:bg-white/5">
                  <dt className="text-[11px] uppercase tracking-wide text-ink-500 dark:text-ink-400">Chapters</dt>
                  <dd className="font-semibold text-ink-900 dark:text-white">{subject.chapter_count}</dd>
                </div>
                <div className="rounded-lg bg-ink-50 py-2 dark:bg-white/5">
                  <dt className="text-[11px] uppercase tracking-wide text-ink-500 dark:text-ink-400">Topics</dt>
                  <dd className="font-semibold text-ink-900 dark:text-white">{subject.topic_count}</dd>
                </div>
                <div className="rounded-lg bg-ink-50 py-2 dark:bg-white/5">
                  <dt className="text-[11px] uppercase tracking-wide text-ink-500 dark:text-ink-400">Weak</dt>
                  <dd className="font-semibold text-amber-600 dark:text-amber-400">{subject.weak_topics}</dd>
                </div>
              </dl>

              <div className="mt-4">
                <div className="mb-1 flex items-center justify-between text-xs">
                  <span className="text-ink-500 dark:text-ink-400">Mastery</span>
                  <span className={`font-semibold ${toneClasses[masteryTone(subject.mastery)].text}`}>
                    {Math.round(subject.mastery)}%
                  </span>
                </div>
                <ProgressBar value={subject.mastery} />
                <p className="mt-2 text-xs text-ink-500 dark:text-ink-400">
                  {subject.topics_started}/{subject.topic_count} topics started
                </p>
              </div>

              <div className="mt-4 flex items-center gap-2">
                <Link to={`/subjects/${subject.id}`} className="btn-primary flex-1 text-sm">
                  Open subject
                </Link>
                {subject.ncert_url ? (
                  <a
                    href={subject.ncert_url}
                    target="_blank"
                    rel="noreferrer"
                    className="btn-secondary px-3"
                    title="Official NCERT textbook"
                  >
                    <ExternalLink size={15} />
                  </a>
                ) : null}
              </div>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}

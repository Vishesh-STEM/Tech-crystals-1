import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { ArrowLeft, ChevronRight, ExternalLink } from "lucide-react";
import { Card, EmptyState, ErrorState, ProgressBar, SectionHeader, Skeleton } from "../components/ui/Primitives";
import { endpoints, errorMessage } from "../lib/api";
import { masteryTone, subjectAccent, toneClasses } from "../lib/format";

export default function SubjectDetail() {
  const { subjectId } = useParams();
  const [subject, setSubject] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  async function load() {
    setLoading(true);
    setError("");
    try {
      setSubject(await endpoints.subject(subjectId!));
    } catch (err) {
      setError(errorMessage(err));
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [subjectId]);

  if (loading) return <Skeleton className="h-96 w-full" />;
  if (error) return <ErrorState message={error} onRetry={load} />;
  if (!subject) return null;

  return (
    <div className="space-y-5">
      <Link to="/subjects" className="btn-ghost -ml-2 text-sm">
        <ArrowLeft size={15} /> All subjects
      </Link>

      <div
        className={`rounded-2xl bg-gradient-to-br p-6 text-white shadow-lift ${
          subjectAccent[subject.color] ?? subjectAccent.indigo
        }`}
      >
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div className="max-w-2xl">
            <p className="text-3xl">{subject.icon}</p>
            <h1 className="mt-2 font-display text-2xl font-semibold sm:text-3xl">{subject.name}</h1>
            <p className="mt-1 text-white/80">{subject.description}</p>
            {subject.ncert_url ? (
              <a
                href={subject.ncert_url}
                target="_blank"
                rel="noreferrer"
                className="mt-4 inline-flex items-center gap-1.5 rounded-lg bg-white/15 px-3 py-1.5 text-sm hover:bg-white/25"
              >
                <ExternalLink size={14} /> Official NCERT textbook
              </a>
            ) : null}
          </div>
          <div className="min-w-[160px]">
            <p className="text-xs uppercase tracking-wide text-white/70">Your mastery</p>
            <p className="font-display text-4xl font-semibold">{Math.round(subject.mastery)}%</p>
            <p className="mt-1 text-xs text-white/70">
              {subject.topics_mastered} mastered · {subject.weak_topics} need work
            </p>
          </div>
        </div>
      </div>

      <Card>
        <SectionHeader title="Chapters" subtitle={`${subject.chapters.length} chapters · ${subject.quiz_count} quizzes available`} />
        {subject.chapters.length === 0 ? (
          <EmptyState title="No chapters yet" description="A teacher can add chapters from the admin workspace." />
        ) : (
          <ul className="divide-y divide-ink-200/70 dark:divide-white/10">
            {subject.chapters.map((chapter: any) => (
              <li key={chapter.id}>
                <Link
                  to={`/chapters/${chapter.id}`}
                  className="flex items-center gap-4 py-3.5 transition hover:bg-ink-50 dark:hover:bg-white/5 sm:px-2"
                >
                  <span className="grid h-9 w-9 shrink-0 place-items-center rounded-lg bg-ink-100 text-sm font-semibold text-ink-600 dark:bg-white/10 dark:text-ink-200">
                    {chapter.number}
                  </span>
                  <span className="min-w-0 flex-1">
                    <span className="block truncate font-medium text-ink-900 dark:text-white">{chapter.name}</span>
                    <span className="muted line-clamp-1 block">{chapter.description}</span>
                    <span className="mt-1.5 block max-w-xs">
                      <ProgressBar value={chapter.mastery} />
                    </span>
                  </span>
                  <span className="hidden shrink-0 text-right sm:block">
                    <span className={`block font-display font-semibold ${toneClasses[masteryTone(chapter.mastery)].text}`}>
                      {Math.round(chapter.mastery)}%
                    </span>
                    <span className="block text-xs text-ink-500 dark:text-ink-400">{chapter.topic_count} topics</span>
                  </span>
                  <ChevronRight size={18} className="shrink-0 text-ink-400" />
                </Link>
              </li>
            ))}
          </ul>
        )}
      </Card>
    </div>
  );
}

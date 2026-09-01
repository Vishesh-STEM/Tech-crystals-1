import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { AlertTriangle, ArrowLeft, ChevronRight, ExternalLink, Play } from "lucide-react";
import { Card, EmptyState, ErrorState, MasteryChip, ProgressBar, SectionHeader, Skeleton } from "../components/ui/Primitives";
import { endpoints, errorMessage } from "../lib/api";

export default function ChapterDetail() {
  const { chapterId } = useParams();
  const [chapter, setChapter] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  async function load() {
    setLoading(true);
    setError("");
    try {
      setChapter(await endpoints.chapter(chapterId!));
    } catch (err) {
      setError(errorMessage(err));
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [chapterId]);

  if (loading) return <Skeleton className="h-96 w-full" />;
  if (error) return <ErrorState message={error} onRetry={load} />;
  if (!chapter) return null;

  return (
    <div className="space-y-5">
      <Link to={`/subjects/${chapter.subject.id}`} className="btn-ghost -ml-2 text-sm">
        <ArrowLeft size={15} /> {chapter.subject.name}
      </Link>

      <Card>
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div className="max-w-2xl">
            <p className="text-xs font-semibold uppercase tracking-wide text-brand-600 dark:text-brand-300">
              Chapter {chapter.number} · {chapter.subject.name}
            </p>
            <h1 className="mt-1 font-display text-2xl font-semibold text-ink-900 dark:text-white">{chapter.name}</h1>
            <p className="muted mt-1">{chapter.description}</p>
          </div>
          {chapter.ncert_url ? (
            <a href={chapter.ncert_url} target="_blank" rel="noreferrer" className="btn-secondary text-sm">
              <ExternalLink size={15} /> NCERT chapter PDF
            </a>
          ) : null}
        </div>
      </Card>

      <div className="grid gap-5 lg:grid-cols-3">
        <div className="lg:col-span-2">
          <Card>
            <SectionHeader title="Topics" subtitle={`${chapter.topics.length} topics in this chapter`} />
            {chapter.topics.length === 0 ? (
              <EmptyState title="No topics yet" />
            ) : (
              <ul className="divide-y divide-ink-200/70 dark:divide-white/10">
                {chapter.topics.map((topic: any) => (
                  <li key={topic.id}>
                    <Link
                      to={`/topics/${topic.id}`}
                      className="flex items-start gap-3 py-3.5 transition hover:bg-ink-50 dark:hover:bg-white/5 sm:px-2"
                    >
                      <div className="min-w-0 flex-1">
                        <div className="flex flex-wrap items-center gap-2">
                          <span className="font-medium text-ink-900 dark:text-white">{topic.name}</span>
                          {topic.is_weak ? (
                            <span className="chip bg-amber-50 text-amber-700 dark:bg-amber-500/15 dark:text-amber-300">
                              <AlertTriangle size={12} /> needs work
                            </span>
                          ) : null}
                          <span className="chip bg-ink-100 text-ink-600 dark:bg-white/10 dark:text-ink-300">
                            {topic.difficulty}
                          </span>
                        </div>
                        <p className="muted line-clamp-2 mt-1">{topic.summary}</p>
                        <div className="mt-2 max-w-xs">
                          <ProgressBar value={topic.mastery} showLabel />
                        </div>
                        <p className="mt-1.5 text-xs text-ink-400">
                          {topic.resource_count} resources · {topic.estimated_minutes} min · {topic.attempts} attempts
                        </p>
                      </div>
                      <ChevronRight size={18} className="mt-1 shrink-0 text-ink-400" />
                    </Link>
                  </li>
                ))}
              </ul>
            )}
          </Card>
        </div>

        <Card>
          <SectionHeader title="Quizzes" subtitle="Test yourself on this chapter." />
          {chapter.quizzes.length === 0 ? (
            <EmptyState title="No quiz yet" description="Ask your teacher to publish one." />
          ) : (
            <ul className="space-y-3">
              {chapter.quizzes.map((quiz: any) => (
                <li key={quiz.id} className="rounded-xl border border-ink-200/70 p-3.5 dark:border-white/10">
                  <p className="text-sm font-semibold text-ink-900 dark:text-white">{quiz.title}</p>
                  <p className="muted mt-0.5">
                    {quiz.question_count} questions · {quiz.time_limit_minutes} min · {quiz.difficulty}
                  </p>
                  <Link to={`/quiz/${quiz.id}`} className="btn-primary mt-3 w-full text-sm">
                    <Play size={14} /> Start quiz
                  </Link>
                </li>
              ))}
            </ul>
          )}
        </Card>
      </div>
    </div>
  );
}

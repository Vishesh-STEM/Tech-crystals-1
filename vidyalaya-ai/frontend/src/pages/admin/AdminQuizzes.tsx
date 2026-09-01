import { useEffect, useState } from "react";
import { Archive, Plus, Save, X } from "lucide-react";
import { Card, EmptyState, ErrorState, SectionHeader, Skeleton } from "../../components/ui/Primitives";
import { useToast } from "../../context/ToastContext";
import { endpoints, errorMessage } from "../../lib/api";
import { masteryTone, toneClasses } from "../../lib/format";

export default function AdminQuizzes() {
  const toast = useToast();
  const [quizzes, setQuizzes] = useState<any[]>([]);
  const [subjects, setSubjects] = useState<any[]>([]);
  const [chapters, setChapters] = useState<any[]>([]);
  const [questions, setQuestions] = useState<any[]>([]);
  const [creating, setCreating] = useState(false);
  const [form, setForm] = useState<any>({
    title: "",
    description: "",
    subject_id: "",
    chapter_id: "",
    time_limit_minutes: 15,
    pass_percentage: 60,
    question_ids: [] as number[],
  });
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");

  async function load() {
    setLoading(true);
    setError("");
    try {
      const [quizList, subjectList, chapterList] = await Promise.all([
        endpoints.adminQuizzes({ limit: 200 }),
        endpoints.adminSubjects(),
        endpoints.adminChapters(),
      ]);
      setQuizzes(quizList);
      setSubjects(subjectList);
      setChapters(chapterList);
    } catch (err) {
      setError(errorMessage(err));
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load();
  }, []);

  useEffect(() => {
    if (!form.chapter_id) {
      setQuestions([]);
      return;
    }
    endpoints
      .adminQuestions({ chapter_id: Number(form.chapter_id), limit: 100 })
      .then(setQuestions)
      .catch(() => setQuestions([]));
  }, [form.chapter_id]);

  async function create() {
    setSaving(true);
    try {
      await endpoints.create("quizzes", {
        title: form.title,
        description: form.description,
        subject_id: Number(form.subject_id),
        chapter_id: form.chapter_id ? Number(form.chapter_id) : null,
        time_limit_minutes: Number(form.time_limit_minutes) || 15,
        pass_percentage: Number(form.pass_percentage) || 60,
        question_ids: form.question_ids,
        is_published: true,
      });
      toast.success("Quiz published.");
      setCreating(false);
      setForm({ ...form, title: "", description: "", question_ids: [] });
      await load();
    } catch (err) {
      toast.error(errorMessage(err));
    } finally {
      setSaving(false);
    }
  }

  async function unpublish(quiz: any) {
    try {
      await endpoints.remove("quizzes", quiz.id);
      toast.success("Quiz unpublished.");
      await load();
    } catch (err) {
      toast.error(errorMessage(err));
    }
  }

  function toggleQuestion(id: number) {
    setForm((current: any) => ({
      ...current,
      question_ids: current.question_ids.includes(id)
        ? current.question_ids.filter((value: number) => value !== id)
        : [...current.question_ids, id],
    }));
  }

  return (
    <div className="space-y-5">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <h1 className="font-display text-2xl font-semibold text-ink-900 dark:text-white">Quizzes</h1>
          <p className="muted mt-1">{quizzes.length} quizzes · attempts feed straight into mastery.</p>
        </div>
        <button className="btn-primary" onClick={() => setCreating(true)}>
          <Plus size={15} /> New quiz
        </button>
      </div>

      {loading ? (
        <Skeleton className="h-80 w-full" />
      ) : error ? (
        <ErrorState message={error} onRetry={load} />
      ) : quizzes.length === 0 ? (
        <EmptyState title="No quizzes yet" action={<button className="btn-primary text-sm" onClick={() => setCreating(true)}>Create a quiz</button>} />
      ) : (
        <Card className="p-0">
          <div className="overflow-x-auto">
            <table className="w-full min-w-[680px] text-sm">
              <thead>
                <tr className="border-b border-ink-200/70 text-left text-xs uppercase tracking-wide text-ink-500 dark:border-white/10 dark:text-ink-400">
                  <th className="px-5 py-3">Quiz</th>
                  <th className="px-3 py-3">Subject</th>
                  <th className="px-3 py-3">Questions</th>
                  <th className="px-3 py-3">Attempts</th>
                  <th className="px-3 py-3">Average</th>
                  <th className="px-3 py-3"></th>
                </tr>
              </thead>
              <tbody className="divide-y divide-ink-200/70 dark:divide-white/10">
                {quizzes.map((quiz) => (
                  <tr key={quiz.id}>
                    <td className="px-5 py-3">
                      <p className="font-medium text-ink-900 dark:text-white">{quiz.title}</p>
                      {!quiz.is_published ? <span className="chip bg-ink-100 text-ink-500 dark:bg-white/10">unpublished</span> : null}
                    </td>
                    <td className="px-3 py-3 text-ink-600 dark:text-ink-300">{quiz.subject_name}</td>
                    <td className="px-3 py-3 text-ink-600 dark:text-ink-300">{quiz.question_count}</td>
                    <td className="px-3 py-3 text-ink-600 dark:text-ink-300">{quiz.attempts}</td>
                    <td className={`px-3 py-3 font-semibold ${toneClasses[masteryTone(quiz.average_accuracy || 0)].text}`}>
                      {quiz.average_accuracy != null ? `${Math.round(quiz.average_accuracy)}%` : "-"}
                    </td>
                    <td className="px-3 py-3 text-right">
                      <button className="btn-ghost text-sm" onClick={() => unpublish(quiz)} title="Unpublish">
                        <Archive size={15} />
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Card>
      )}

      {creating ? (
        <div className="fixed inset-0 z-50 flex items-end justify-center bg-ink-900/50 backdrop-blur-sm sm:items-center sm:p-6" onClick={() => setCreating(false)}>
          <div
            className="max-h-[92vh] w-full max-w-2xl overflow-y-auto rounded-t-2xl bg-white p-6 dark:bg-ink-900 sm:rounded-2xl"
            onClick={(event) => event.stopPropagation()}
          >
            <div className="mb-4 flex items-center justify-between">
              <SectionHeader title="New quiz" subtitle="Pick a chapter, then choose its questions." />
              <button onClick={() => setCreating(false)} aria-label="Close"><X size={18} /></button>
            </div>

            <div className="space-y-3">
              <div>
                <label className="label" htmlFor="title">Title *</label>
                <input id="title" className="input" value={form.title} onChange={(event) => setForm({ ...form, title: event.target.value })} />
              </div>
              <div>
                <label className="label" htmlFor="description">Description</label>
                <textarea id="description" className="input min-h-[70px]" value={form.description} onChange={(event) => setForm({ ...form, description: event.target.value })} />
              </div>
              <div className="grid gap-3 sm:grid-cols-2">
                <div>
                  <label className="label" htmlFor="subject">Subject *</label>
                  <select id="subject" className="input" value={form.subject_id} onChange={(event) => setForm({ ...form, subject_id: event.target.value, chapter_id: "" })}>
                    <option value="">Select...</option>
                    {subjects.map((subject) => (
                      <option key={subject.id} value={subject.id}>{subject.name}</option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="label" htmlFor="chapter">Chapter</label>
                  <select id="chapter" className="input" value={form.chapter_id} onChange={(event) => setForm({ ...form, chapter_id: event.target.value })}>
                    <option value="">Select...</option>
                    {chapters
                      .filter((chapter) => !form.subject_id || String(chapter.subject_id) === String(form.subject_id))
                      .map((chapter) => (
                        <option key={chapter.id} value={chapter.id}>{chapter.name}</option>
                      ))}
                  </select>
                </div>
                <div>
                  <label className="label" htmlFor="limit">Time limit (minutes)</label>
                  <input id="limit" type="number" min={1} max={240} className="input" value={form.time_limit_minutes} onChange={(event) => setForm({ ...form, time_limit_minutes: event.target.value })} />
                </div>
                <div>
                  <label className="label" htmlFor="pass">Pass percentage</label>
                  <input id="pass" type="number" min={0} max={100} className="input" value={form.pass_percentage} onChange={(event) => setForm({ ...form, pass_percentage: event.target.value })} />
                </div>
              </div>

              <div>
                <p className="label">Questions ({form.question_ids.length} selected)</p>
                {questions.length === 0 ? (
                  <p className="muted rounded-xl border border-dashed border-ink-200 p-3 dark:border-white/10">
                    Choose a chapter to list its questions.
                  </p>
                ) : (
                  <ul className="max-h-64 space-y-1.5 overflow-y-auto rounded-xl border border-ink-200 p-2 dark:border-white/10">
                    {questions.map((question) => (
                      <li key={question.id}>
                        <label className="flex cursor-pointer items-start gap-2 rounded-lg px-2 py-1.5 hover:bg-ink-50 dark:hover:bg-white/5">
                          <input
                            type="checkbox"
                            className="mt-1"
                            checked={form.question_ids.includes(question.id)}
                            onChange={() => toggleQuestion(question.id)}
                          />
                          <span className="text-sm text-ink-700 dark:text-ink-200">
                            <span className="chip mr-1.5 bg-ink-100 text-ink-500 dark:bg-white/10">{question.difficulty}</span>
                            {question.text}
                          </span>
                        </label>
                      </li>
                    ))}
                  </ul>
                )}
              </div>
            </div>

            <div className="mt-5 flex gap-2">
              <button
                className="btn-primary flex-1"
                onClick={create}
                disabled={saving || !form.title || !form.subject_id || form.question_ids.length === 0}
              >
                <Save size={15} /> {saving ? "Publishing..." : "Publish quiz"}
              </button>
              <button className="btn-secondary" onClick={() => setCreating(false)}>Cancel</button>
            </div>
          </div>
        </div>
      ) : null}
    </div>
  );
}

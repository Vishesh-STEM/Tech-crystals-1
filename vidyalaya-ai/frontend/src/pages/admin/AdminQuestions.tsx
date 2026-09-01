import { useEffect, useState } from "react";
import { Archive, Plus, Save, Search, X } from "lucide-react";
import { Card, EmptyState, ErrorState, SectionHeader, Skeleton } from "../../components/ui/Primitives";
import { useToast } from "../../context/ToastContext";
import { endpoints, errorMessage } from "../../lib/api";

const BLANK = {
  topic_id: "",
  text: "",
  options: ["", "", "", ""],
  correct_answer: "",
  explanation: "",
  difficulty: "medium",
  concept_tag: "",
  marks: 1,
};

export default function AdminQuestions() {
  const toast = useToast();
  const [questions, setQuestions] = useState<any[]>([]);
  const [topics, setTopics] = useState<any[]>([]);
  const [subjects, setSubjects] = useState<any[]>([]);
  const [filters, setFilters] = useState({ subject_id: "", difficulty: "", search: "" });
  const [editing, setEditing] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");

  async function load() {
    setLoading(true);
    setError("");
    try {
      const params: Record<string, unknown> = { limit: 200 };
      if (filters.subject_id) params.subject_id = Number(filters.subject_id);
      if (filters.difficulty) params.difficulty = filters.difficulty;
      if (filters.search) params.search = filters.search;
      const [questionList, topicList, subjectList] = await Promise.all([
        endpoints.adminQuestions(params),
        topics.length ? Promise.resolve(topics) : endpoints.adminTopics(),
        subjects.length ? Promise.resolve(subjects) : endpoints.adminSubjects(),
      ]);
      setQuestions(questionList);
      setTopics(topicList);
      setSubjects(subjectList);
    } catch (err) {
      setError(errorMessage(err));
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [filters.subject_id, filters.difficulty]);

  async function save() {
    if (!editing) return;
    setSaving(true);
    try {
      const options = (editing.options || []).map((option: string) => option.trim()).filter(Boolean);
      const payload = {
        topic_id: Number(editing.topic_id),
        text: editing.text,
        options,
        correct_answer: editing.correct_answer,
        explanation: editing.explanation,
        difficulty: editing.difficulty,
        concept_tag: editing.concept_tag,
        marks: Number(editing.marks) || 1,
      };
      if (editing.id) {
        const { topic_id, ...updatable } = payload;
        await endpoints.update("questions", editing.id, updatable);
      } else {
        await endpoints.create("questions", payload);
      }
      toast.success("Question saved.");
      setEditing(null);
      await load();
    } catch (err) {
      toast.error(errorMessage(err));
    } finally {
      setSaving(false);
    }
  }

  async function archive(question: any) {
    try {
      await endpoints.remove("questions", question.id);
      toast.success("Question archived.");
      await load();
    } catch (err) {
      toast.error(errorMessage(err));
    }
  }

  return (
    <div className="space-y-5">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <h1 className="font-display text-2xl font-semibold text-ink-900 dark:text-white">Question bank</h1>
          <p className="muted mt-1">{questions.length} questions loaded. Every question stores an explanation.</p>
        </div>
        <div className="flex w-full flex-wrap gap-2 sm:w-auto">
          <form
            className="relative flex-1 sm:w-56"
            onSubmit={(event) => {
              event.preventDefault();
              load();
            }}
          >
            <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-ink-400" />
            <input
              className="input pl-9"
              placeholder="Search questions"
              value={filters.search}
              onChange={(event) => setFilters({ ...filters, search: event.target.value })}
              aria-label="Search questions"
            />
          </form>
          <select
            className="input w-40"
            value={filters.subject_id}
            onChange={(event) => setFilters({ ...filters, subject_id: event.target.value })}
            aria-label="Subject"
          >
            <option value="">All subjects</option>
            {subjects.map((subject) => (
              <option key={subject.id} value={subject.id}>{subject.name}</option>
            ))}
          </select>
          <select
            className="input w-32"
            value={filters.difficulty}
            onChange={(event) => setFilters({ ...filters, difficulty: event.target.value })}
            aria-label="Difficulty"
          >
            <option value="">Any level</option>
            <option value="easy">Easy</option>
            <option value="medium">Medium</option>
            <option value="hard">Hard</option>
          </select>
          <button className="btn-primary" onClick={() => setEditing({ ...BLANK })}>
            <Plus size={15} /> New
          </button>
        </div>
      </div>

      {loading ? (
        <Skeleton className="h-80 w-full" />
      ) : error ? (
        <ErrorState message={error} onRetry={load} />
      ) : questions.length === 0 ? (
        <EmptyState title="No questions found" action={<button className="btn-primary text-sm" onClick={() => setEditing({ ...BLANK })}>Add a question</button>} />
      ) : (
        <ul className="space-y-3">
          {questions.map((question) => (
            <li key={question.id}>
              <Card>
                <div className="flex flex-wrap items-start justify-between gap-3">
                  <div className="min-w-0 flex-1">
                    <div className="mb-1 flex flex-wrap items-center gap-2">
                      <span className="chip bg-brand-50 text-brand-700 dark:bg-brand-500/15 dark:text-brand-200">{question.difficulty}</span>
                      <span className="muted">{question.concept_tag}</span>
                      {question.is_active === false ? <span className="chip bg-ink-100 text-ink-500 dark:bg-white/10">archived</span> : null}
                    </div>
                    <p className="font-medium text-ink-900 dark:text-white">{question.text}</p>
                    <ul className="mt-2 grid gap-1 sm:grid-cols-2">
                      {(question.options || []).map((option: string) => (
                        <li
                          key={option}
                          className={`rounded-lg px-3 py-1.5 text-sm ${
                            option === question.correct_answer
                              ? "bg-emerald-50 font-medium text-emerald-800 dark:bg-emerald-500/10 dark:text-emerald-200"
                              : "bg-ink-50 text-ink-600 dark:bg-white/5 dark:text-ink-300"
                          }`}
                        >
                          {option}
                        </li>
                      ))}
                    </ul>
                    {question.explanation ? (
                      <p className="mt-2 text-xs text-ink-500 dark:text-ink-400">{question.explanation}</p>
                    ) : null}
                  </div>
                  <div className="flex gap-2">
                    <button className="btn-secondary text-sm" onClick={() => setEditing({ ...question, options: question.options?.length ? question.options : ["", "", "", ""] })}>
                      Edit
                    </button>
                    <button className="btn-ghost text-sm" onClick={() => archive(question)} title="Archive">
                      <Archive size={15} />
                    </button>
                  </div>
                </div>
              </Card>
            </li>
          ))}
        </ul>
      )}

      {editing ? (
        <div className="fixed inset-0 z-50 flex items-end justify-center bg-ink-900/50 backdrop-blur-sm sm:items-center sm:p-6" onClick={() => setEditing(null)}>
          <div
            className="max-h-[92vh] w-full max-w-xl overflow-y-auto rounded-t-2xl bg-white p-6 dark:bg-ink-900 sm:rounded-2xl"
            onClick={(event) => event.stopPropagation()}
          >
            <div className="mb-4 flex items-center justify-between">
              <SectionHeader title={editing.id ? "Edit question" : "New question"} />
              <button onClick={() => setEditing(null)} aria-label="Close"><X size={18} /></button>
            </div>

            <div className="space-y-3">
              {!editing.id ? (
                <div>
                  <label className="label" htmlFor="topic">Topic *</label>
                  <select
                    id="topic"
                    className="input"
                    value={String(editing.topic_id ?? "")}
                    onChange={(event) => setEditing({ ...editing, topic_id: event.target.value })}
                  >
                    <option value="">Select a topic...</option>
                    {topics.map((topic) => (
                      <option key={topic.id} value={topic.id}>
                        {topic.subject_name} · {topic.name}
                      </option>
                    ))}
                  </select>
                </div>
              ) : null}

              <div>
                <label className="label" htmlFor="text">Question *</label>
                <textarea id="text" className="input min-h-[80px]" value={editing.text} onChange={(event) => setEditing({ ...editing, text: event.target.value })} />
              </div>

              <div>
                <p className="label">Options</p>
                {(editing.options || []).map((option: string, index: number) => (
                  <div key={index} className="mb-2 flex items-center gap-2">
                    <input
                      className="input"
                      placeholder={`Option ${String.fromCharCode(65 + index)}`}
                      value={option}
                      onChange={(event) => {
                        const options = [...editing.options];
                        options[index] = event.target.value;
                        setEditing({ ...editing, options });
                      }}
                    />
                    <button
                      type="button"
                      className={`btn text-xs ${editing.correct_answer === option && option ? "bg-emerald-500 text-white" : "btn-secondary"}`}
                      onClick={() => setEditing({ ...editing, correct_answer: option })}
                      title="Mark as the correct answer"
                    >
                      Correct
                    </button>
                  </div>
                ))}
                <button
                  type="button"
                  className="btn-ghost text-xs"
                  onClick={() => setEditing({ ...editing, options: [...(editing.options || []), ""] })}
                >
                  <Plus size={13} /> Add option
                </button>
              </div>

              <div>
                <label className="label" htmlFor="answer">Correct answer *</label>
                <input id="answer" className="input" value={editing.correct_answer} onChange={(event) => setEditing({ ...editing, correct_answer: event.target.value })} />
                <p className="mt-1 text-xs text-ink-400">Must match one of the options exactly.</p>
              </div>

              <div>
                <label className="label" htmlFor="explanation">Explanation</label>
                <textarea id="explanation" className="input min-h-[70px]" value={editing.explanation} onChange={(event) => setEditing({ ...editing, explanation: event.target.value })} />
              </div>

              <div className="grid grid-cols-3 gap-3">
                <div>
                  <label className="label" htmlFor="difficulty">Difficulty</label>
                  <select id="difficulty" className="input" value={editing.difficulty} onChange={(event) => setEditing({ ...editing, difficulty: event.target.value })}>
                    <option value="easy">Easy</option>
                    <option value="medium">Medium</option>
                    <option value="hard">Hard</option>
                  </select>
                </div>
                <div>
                  <label className="label" htmlFor="concept">Concept tag</label>
                  <input id="concept" className="input" value={editing.concept_tag} onChange={(event) => setEditing({ ...editing, concept_tag: event.target.value })} />
                </div>
                <div>
                  <label className="label" htmlFor="marks">Marks</label>
                  <input id="marks" type="number" min={1} max={10} className="input" value={editing.marks} onChange={(event) => setEditing({ ...editing, marks: event.target.value })} />
                </div>
              </div>
            </div>

            <div className="mt-5 flex gap-2">
              <button className="btn-primary flex-1" onClick={save} disabled={saving}>
                <Save size={15} /> {saving ? "Saving..." : "Save question"}
              </button>
              <button className="btn-secondary" onClick={() => setEditing(null)}>Cancel</button>
            </div>
          </div>
        </div>
      ) : null}
    </div>
  );
}

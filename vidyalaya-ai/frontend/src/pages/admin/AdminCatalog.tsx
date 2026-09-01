import { useEffect, useMemo, useState } from "react";
import { Archive, Plus, Save, Search, X } from "lucide-react";
import { Card, EmptyState, ErrorState, SectionHeader, Skeleton } from "../../components/ui/Primitives";
import { useToast } from "../../context/ToastContext";
import { endpoints, errorMessage } from "../../lib/api";

type Entity = "subjects" | "chapters" | "topics" | "resources";

interface FieldSpec {
  name: string;
  label: string;
  type?: "text" | "textarea" | "number" | "select" | "list";
  options?: { value: string; label: string }[];
  required?: boolean;
  help?: string;
}

const titles: Record<Entity, { title: string; subtitle: string }> = {
  subjects: { title: "Subjects", subtitle: "The six Class 12 subjects and any you add." },
  chapters: { title: "Chapters", subtitle: "NCERT-aligned chapters inside each subject." },
  topics: { title: "Topics", subtitle: "Teachable units with summaries, key concepts and NCERT links." },
  resources: { title: "Resources", subtitle: "Text, visual, audio and practice study material." },
};

export default function AdminCatalog({ entity }: { entity: Entity }) {
  const toast = useToast();
  const [rows, setRows] = useState<any[]>([]);
  const [subjects, setSubjects] = useState<any[]>([]);
  const [chapters, setChapters] = useState<any[]>([]);
  const [topics, setTopics] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [query, setQuery] = useState("");
  const [editing, setEditing] = useState<any>(null);
  const [saving, setSaving] = useState(false);

  const fields = useMemo<FieldSpec[]>(() => {
    if (entity === "subjects") {
      return [
        { name: "code", label: "Code", required: true, help: "Short unique code, e.g. PHY" },
        { name: "name", label: "Name", required: true },
        { name: "description", label: "Description", type: "textarea" },
        { name: "icon", label: "Icon (emoji)" },
        {
          name: "color",
          label: "Accent colour",
          type: "select",
          options: ["blue", "violet", "emerald", "green", "amber", "cyan", "indigo"].map((value) => ({ value, label: value })),
        },
        { name: "ncert_url", label: "NCERT link" },
      ];
    }
    if (entity === "chapters") {
      return [
        {
          name: "subject_id",
          label: "Subject",
          type: "select",
          required: true,
          options: subjects.map((subject) => ({ value: String(subject.id), label: subject.name })),
        },
        { name: "name", label: "Chapter name", required: true },
        { name: "number", label: "Chapter number", type: "number" },
        { name: "description", label: "Description", type: "textarea" },
        { name: "ncert_url", label: "NCERT chapter link" },
        { name: "estimated_hours", label: "Estimated hours", type: "number" },
      ];
    }
    if (entity === "topics") {
      return [
        {
          name: "chapter_id",
          label: "Chapter",
          type: "select",
          required: true,
          options: chapters.map((chapter) => ({
            value: String(chapter.id),
            label: `${chapter.subject_name} · ${chapter.name}`,
          })),
        },
        { name: "name", label: "Topic name", required: true },
        { name: "summary", label: "Summary", type: "textarea" },
        { name: "key_concepts", label: "Key concepts", type: "list", help: "One per line" },
        { name: "examples", label: "Examples", type: "list", help: "One per line" },
        { name: "prerequisites", label: "Prerequisite topic slugs", type: "list", help: "One slug per line" },
        {
          name: "difficulty",
          label: "Difficulty",
          type: "select",
          options: ["easy", "medium", "hard"].map((value) => ({ value, label: value })),
        },
        { name: "estimated_minutes", label: "Estimated minutes", type: "number" },
        { name: "ncert_url", label: "NCERT link" },
      ];
    }
    return [
      {
        name: "topic_id",
        label: "Topic",
        type: "select",
        required: true,
        options: topics.map((topic) => ({ value: String(topic.id), label: `${topic.subject_name} · ${topic.name}` })),
      },
      { name: "title", label: "Title", required: true },
      {
        name: "type",
        label: "Format",
        type: "select",
        required: true,
        options: ["text", "visual", "audio", "practice"].map((value) => ({ value, label: value })),
      },
      { name: "description", label: "Description", type: "textarea" },
      { name: "body", label: "Content (markdown)", type: "textarea" },
      { name: "estimated_minutes", label: "Estimated minutes", type: "number" },
      { name: "ncert_url", label: "NCERT link" },
    ];
  }, [entity, subjects, chapters, topics]);

  async function load() {
    setLoading(true);
    setError("");
    try {
      const [subjectList, chapterList] = await Promise.all([
        endpoints.adminSubjects(),
        entity === "topics" || entity === "chapters" ? endpoints.adminChapters() : Promise.resolve([]),
      ]);
      setSubjects(subjectList);
      setChapters(chapterList);
      if (entity === "subjects") setRows(subjectList);
      else if (entity === "chapters") setRows(chapterList);
      else if (entity === "topics") {
        const topicList = await endpoints.adminTopics();
        setTopics(topicList);
        setRows(topicList);
      } else {
        const topicList = await endpoints.adminTopics();
        setTopics(topicList);
        setRows(await endpoints.adminResources());
      }
    } catch (err) {
      setError(errorMessage(err));
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load();
    setEditing(null);
    setQuery("");
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [entity]);

  function startCreate() {
    const blank: Record<string, any> = {};
    fields.forEach((field) => {
      blank[field.name] = field.type === "number" ? 0 : field.type === "list" ? [] : "";
    });
    if (entity === "subjects") {
      blank.icon = "📘";
      blank.color = "indigo";
    }
    if (entity === "topics") blank.difficulty = "medium";
    if (entity === "resources") blank.type = "text";
    setEditing({ ...blank, __new: true });
  }

  function startEdit(row: any) {
    const draft: Record<string, any> = { __new: false, id: row.id };
    fields.forEach((field) => {
      const value = row[field.name];
      draft[field.name] = value === null || value === undefined ? (field.type === "list" ? [] : "") : value;
    });
    setEditing(draft);
  }

  async function save() {
    if (!editing) return;
    setSaving(true);
    try {
      const payload: Record<string, any> = {};
      fields.forEach((field) => {
        let value = editing[field.name];
        if (field.type === "number") value = Number(value) || 0;
        if (field.name.endsWith("_id")) value = Number(value) || undefined;
        if (field.type === "list" && typeof value === "string") {
          value = value.split("\n").map((line: string) => line.trim()).filter(Boolean);
        }
        payload[field.name] = value;
      });
      if (editing.__new) {
        await endpoints.create(entity, payload);
        toast.success("Created successfully.");
      } else {
        const { code, subject_id, chapter_id, topic_id, ...updatable } = payload;
        await endpoints.update(entity, editing.id, updatable);
        toast.success("Saved.");
      }
      setEditing(null);
      await load();
    } catch (err) {
      toast.error(errorMessage(err));
    } finally {
      setSaving(false);
    }
  }

  async function archive(row: any) {
    try {
      await endpoints.remove(entity, row.id);
      toast.success("Archived. Student history is preserved.");
      await load();
    } catch (err) {
      toast.error(errorMessage(err));
    }
  }

  const filtered = rows.filter((row) =>
    JSON.stringify(row).toLowerCase().includes(query.trim().toLowerCase()),
  );
  const meta = titles[entity];

  return (
    <div className="space-y-5">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <h1 className="font-display text-2xl font-semibold text-ink-900 dark:text-white">{meta.title}</h1>
          <p className="muted mt-1">{meta.subtitle}</p>
        </div>
        <div className="flex w-full gap-2 sm:w-auto">
          <label className="relative flex-1 sm:w-60">
            <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-ink-400" />
            <input className="input pl-9" placeholder="Search" value={query} onChange={(event) => setQuery(event.target.value)} aria-label="Search" />
          </label>
          <button className="btn-primary" onClick={startCreate}>
            <Plus size={15} /> New
          </button>
        </div>
      </div>

      {loading ? (
        <Skeleton className="h-80 w-full" />
      ) : error ? (
        <ErrorState message={error} onRetry={load} />
      ) : filtered.length === 0 ? (
        <EmptyState title={`No ${entity} yet`} action={<button className="btn-primary text-sm" onClick={startCreate}>Create one</button>} />
      ) : (
        <Card className="p-0">
          <ul className="divide-y divide-ink-200/70 dark:divide-white/10">
            {filtered.map((row) => (
              <li key={row.id} className="flex flex-wrap items-center gap-3 px-5 py-3">
                <div className="min-w-0 flex-1">
                  <p className="truncate font-medium text-ink-900 dark:text-white">
                    {row.name || row.title}
                    {row.is_active === false ? <span className="chip ml-2 bg-ink-100 text-ink-500 dark:bg-white/10">archived</span> : null}
                  </p>
                  <p className="muted truncate">
                    {entity === "subjects" ? `${row.chapter_count} chapters · ${row.topic_count} topics` : null}
                    {entity === "chapters" ? `${row.subject_name} · ${row.topic_count} topics` : null}
                    {entity === "topics" ? `${row.subject_name} · ${row.chapter_name} · ${row.resource_count} resources · ${row.question_count} questions` : null}
                    {entity === "resources" ? `${row.type} · ${row.estimated_minutes} min` : null}
                  </p>
                </div>
                <div className="flex gap-2">
                  <button className="btn-secondary text-sm" onClick={() => startEdit(row)}>Edit</button>
                  <button className="btn-ghost text-sm" onClick={() => archive(row)} title="Archive">
                    <Archive size={15} />
                  </button>
                </div>
              </li>
            ))}
          </ul>
        </Card>
      )}

      {editing ? (
        <div className="fixed inset-0 z-50 flex items-end justify-center bg-ink-900/50 backdrop-blur-sm sm:items-center sm:p-6" onClick={() => setEditing(null)}>
          <div
            className="max-h-[92vh] w-full max-w-xl overflow-y-auto rounded-t-2xl bg-white p-6 dark:bg-ink-900 sm:rounded-2xl"
            onClick={(event) => event.stopPropagation()}
          >
            <div className="mb-4 flex items-center justify-between">
              <SectionHeader title={editing.__new ? `New ${entity.slice(0, -1)}` : `Edit ${entity.slice(0, -1)}`} />
              <button onClick={() => setEditing(null)} aria-label="Close"><X size={18} /></button>
            </div>
            <div className="space-y-3">
              {fields.map((field) => {
                const value = editing[field.name];
                const disabled = !editing.__new && (field.name.endsWith("_id") || field.name === "code");
                return (
                  <div key={field.name}>
                    <label className="label" htmlFor={field.name}>
                      {field.label} {field.required ? <span className="text-rose-500">*</span> : null}
                    </label>
                    {field.type === "select" ? (
                      <select
                        id={field.name}
                        className="input"
                        value={String(value ?? "")}
                        disabled={disabled}
                        onChange={(event) => setEditing({ ...editing, [field.name]: event.target.value })}
                      >
                        <option value="">Select...</option>
                        {(field.options ?? []).map((option) => (
                          <option key={option.value} value={option.value}>{option.label}</option>
                        ))}
                      </select>
                    ) : field.type === "textarea" ? (
                      <textarea
                        id={field.name}
                        className="input min-h-[90px]"
                        value={String(value ?? "")}
                        onChange={(event) => setEditing({ ...editing, [field.name]: event.target.value })}
                      />
                    ) : field.type === "list" ? (
                      <textarea
                        id={field.name}
                        className="input min-h-[90px]"
                        value={Array.isArray(value) ? value.join("\n") : String(value ?? "")}
                        onChange={(event) => setEditing({ ...editing, [field.name]: event.target.value })}
                      />
                    ) : (
                      <input
                        id={field.name}
                        type={field.type === "number" ? "number" : "text"}
                        className="input"
                        value={String(value ?? "")}
                        disabled={disabled}
                        onChange={(event) => setEditing({ ...editing, [field.name]: event.target.value })}
                      />
                    )}
                    {field.help ? <p className="mt-1 text-xs text-ink-400">{field.help}</p> : null}
                  </div>
                );
              })}
            </div>
            <div className="mt-5 flex gap-2">
              <button className="btn-primary flex-1" onClick={save} disabled={saving}>
                <Save size={15} /> {saving ? "Saving..." : "Save"}
              </button>
              <button className="btn-secondary" onClick={() => setEditing(null)}>Cancel</button>
            </div>
          </div>
        </div>
      ) : null}
    </div>
  );
}

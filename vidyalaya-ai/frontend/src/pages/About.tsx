import { Link } from "react-router-dom";
import {
  ArrowRight, Bot, BookOpen, Brain, Database, GraduationCap, LineChart, Server, ShieldCheck, Sparkles,
} from "lucide-react";

const features = [
  { icon: Brain, title: "Transparent mastery", text: "Each topic carries a 0-100 mastery score built from recent scores, historical scores, attempt count, question difficulty, repeated mistakes, improvement and recency." },
  { icon: LineChart, title: "Weak-topic detection", text: "Multiple signals combine into a weakness confidence level, and you always get the reason: 'You scored below 50% in your last 3 attempts on this topic.'" },
  { icon: Sparkles, title: "Recommendations that adapt", text: "Revision, practice, prerequisites and stretch work are ranked by mastery, recency, weakness and which study format actually works for you." },
  { icon: Bot, title: "AI tutor with RAG", text: "Questions are embedded, matched against your own syllabus content in a vector store, and answered by a local Ollama model - with an offline answer engine when Ollama is not running." },
  { icon: BookOpen, title: "NCERT aligned", text: "Six Class 12 subjects with chapters, topics, four resource formats and official NCERT reference links. No textbook is reproduced." },
  { icon: ShieldCheck, title: "Private by design", text: "JWT authentication, role-based access, hashed passwords and strict student data isolation. Your data stays on your own server." },
];

const stack = [
  { icon: Server, label: "FastAPI + SQLAlchemy", text: "REST API, migrations and services" },
  { icon: Database, label: "PostgreSQL / SQLite", text: "Production database with a dev fallback" },
  { icon: Bot, label: "Ollama + ChromaDB", text: "Free local LLM and vector search" },
  { icon: GraduationCap, label: "React + TypeScript", text: "Tailwind UI with charts and dark mode" },
];

export default function About() {
  return (
    <div className="min-h-screen bg-ink-50 dark:bg-ink-950">
      <header className="border-b border-ink-200/70 bg-white/80 backdrop-blur dark:border-white/10 dark:bg-ink-900/80">
        <div className="mx-auto flex max-w-6xl items-center gap-3 px-4 py-4 sm:px-6">
          <span className="grid h-10 w-10 place-items-center rounded-xl bg-gradient-to-br from-brand-500 to-violet-500 text-white">
            <GraduationCap size={20} />
          </span>
          <div className="min-w-0">
            <p className="font-display font-semibold text-ink-900 dark:text-white">Vidyalaya AI</p>
            <p className="truncate text-xs text-ink-500 dark:text-ink-400">Learn smarter. Study what matters.</p>
          </div>
          <div className="ml-auto flex gap-2">
            <Link to="/login" className="btn-secondary">Log in</Link>
            <Link to="/register" className="btn-primary">Get started</Link>
          </div>
        </div>
      </header>

      <section className="mx-auto max-w-6xl px-4 py-14 sm:px-6">
        <p className="chip bg-brand-50 text-brand-700 dark:bg-brand-500/15 dark:text-brand-200">
          Class 12 · CBSE · NCERT aligned
        </p>
        <h1 className="mt-4 max-w-3xl font-display text-4xl font-semibold leading-tight text-ink-900 dark:text-white sm:text-5xl">
          A personalised learning platform that knows which topic you should study next.
        </h1>
        <p className="muted mt-4 max-w-2xl text-base">
          Vidyalaya AI tracks every quiz, resource and question you attempt across Mathematics, Physics,
          Chemistry, Biology, English and Computer Science - then turns that into mastery scores, weak-topic
          alerts and a study plan you can act on today.
        </p>
        <div className="mt-7 flex flex-wrap gap-3">
          <Link to="/register" className="btn-primary">
            Create your account <ArrowRight size={16} />
          </Link>
          <Link to="/login" className="btn-secondary">Try the demo student</Link>
        </div>
      </section>

      <section className="mx-auto max-w-6xl px-4 pb-14 sm:px-6">
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {features.map((feature) => {
            const Icon = feature.icon;
            return (
              <div key={feature.title} className="card card-hover p-5">
                <span className="mb-3 grid h-10 w-10 place-items-center rounded-xl bg-brand-50 text-brand-600 dark:bg-brand-500/15 dark:text-brand-300">
                  <Icon size={19} />
                </span>
                <h3 className="font-display font-semibold text-ink-900 dark:text-white">{feature.title}</h3>
                <p className="muted mt-1.5">{feature.text}</p>
              </div>
            );
          })}
        </div>
      </section>

      <section className="mx-auto max-w-6xl px-4 pb-20 sm:px-6">
        <h2 className="section-title mb-4">Built on free, open technology</h2>
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {stack.map((item) => {
            const Icon = item.icon;
            return (
              <div key={item.label} className="card p-5">
                <Icon className="mb-2 text-brand-500" size={20} />
                <p className="font-semibold text-ink-900 dark:text-white">{item.label}</p>
                <p className="muted mt-0.5">{item.text}</p>
              </div>
            );
          })}
        </div>
        <p className="muted mt-6">
          No paid AI APIs and no API keys required. The tutor runs on a local Ollama model, and when Ollama is
          unavailable the platform answers from its own syllabus content and your performance data.
        </p>
      </section>

      <footer className="border-t border-ink-200/70 py-8 text-center text-sm text-ink-500 dark:border-white/10 dark:text-ink-400">
        Vidyalaya AI · Learn smarter. Study what matters.
      </footer>
    </div>
  );
}

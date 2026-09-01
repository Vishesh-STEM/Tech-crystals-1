import { ReactNode } from "react";
import { Link } from "react-router-dom";
import { BookOpen, Brain, GraduationCap, LineChart } from "lucide-react";

const highlights = [
  { icon: Brain, title: "Mastery you can trust", text: "Every topic gets a transparent 0-100 score built from your real attempts." },
  { icon: LineChart, title: "Weak topics, explained", text: "We tell you what needs work and exactly why it was flagged." },
  { icon: BookOpen, title: "NCERT aligned", text: "Six Class 12 subjects, chapter by chapter, with official references." },
];

export default function AuthShell({
  title,
  subtitle,
  children,
  footer,
}: {
  title: string;
  subtitle: string;
  children: ReactNode;
  footer?: ReactNode;
}) {
  return (
    <div className="min-h-screen bg-ink-50 dark:bg-ink-950 lg:grid lg:grid-cols-2">
      <div className="relative hidden overflow-hidden bg-gradient-to-br from-brand-700 via-brand-600 to-violet-600 p-12 text-white lg:flex lg:flex-col">
        <div className="absolute -right-24 -top-24 h-72 w-72 rounded-full bg-white/10 blur-3xl" />
        <div className="absolute -bottom-32 -left-16 h-80 w-80 rounded-full bg-violet-400/20 blur-3xl" />
        <Link to="/about" className="relative flex items-center gap-3">
          <span className="grid h-11 w-11 place-items-center rounded-2xl bg-white/15 backdrop-blur">
            <GraduationCap size={22} />
          </span>
          <span>
            <span className="block font-display text-xl font-semibold">Vidyalaya AI</span>
            <span className="block text-sm text-white/70">Learn smarter. Study what matters.</span>
          </span>
        </Link>

        <div className="relative mt-auto space-y-7">
          <h1 className="max-w-md font-display text-4xl font-semibold leading-tight">
            Your Class 12 year, personalised topic by topic.
          </h1>
          <div className="space-y-4">
            {highlights.map((item) => {
              const Icon = item.icon;
              return (
                <div key={item.title} className="flex gap-3">
                  <span className="mt-0.5 grid h-9 w-9 shrink-0 place-items-center rounded-xl bg-white/15">
                    <Icon size={18} />
                  </span>
                  <span>
                    <span className="block font-semibold">{item.title}</span>
                    <span className="block text-sm text-white/75">{item.text}</span>
                  </span>
                </div>
              );
            })}
          </div>
          <p className="text-xs text-white/60">
            Runs entirely on free and open technology - a local Ollama model with an offline fallback.
          </p>
        </div>
      </div>

      <div className="flex min-h-screen items-center justify-center px-4 py-10 lg:min-h-0">
        <div className="w-full max-w-md">
          <div className="mb-6 flex items-center gap-2.5 lg:hidden">
            <span className="grid h-10 w-10 place-items-center rounded-xl bg-gradient-to-br from-brand-500 to-violet-500 text-white">
              <GraduationCap size={20} />
            </span>
            <span>
              <span className="block font-display font-semibold text-ink-900 dark:text-white">Vidyalaya AI</span>
              <span className="block text-xs text-ink-500 dark:text-ink-400">Learn smarter. Study what matters.</span>
            </span>
          </div>
          <div className="card p-6 sm:p-8">
            <h2 className="font-display text-2xl font-semibold text-ink-900 dark:text-white">{title}</h2>
            <p className="muted mb-6 mt-1">{subtitle}</p>
            {children}
          </div>
          <div className="mt-5 text-center">{footer}</div>
        </div>
      </div>
    </div>
  );
}

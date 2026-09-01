export function masteryTone(value: number): "danger" | "warn" | "ok" | "great" {
  if (value < 40) return "danger";
  if (value < 60) return "warn";
  if (value < 80) return "ok";
  return "great";
}

export const toneClasses: Record<string, { bar: string; text: string; chip: string }> = {
  danger: {
    bar: "bg-rose-500",
    text: "text-rose-600 dark:text-rose-400",
    chip: "bg-rose-50 text-rose-700 dark:bg-rose-500/10 dark:text-rose-300",
  },
  warn: {
    bar: "bg-amber-500",
    text: "text-amber-600 dark:text-amber-400",
    chip: "bg-amber-50 text-amber-700 dark:bg-amber-500/10 dark:text-amber-300",
  },
  ok: {
    bar: "bg-brand-500",
    text: "text-brand-600 dark:text-brand-400",
    chip: "bg-brand-50 text-brand-700 dark:bg-brand-500/10 dark:text-brand-300",
  },
  great: {
    bar: "bg-emerald-500",
    text: "text-emerald-600 dark:text-emerald-400",
    chip: "bg-emerald-50 text-emerald-700 dark:bg-emerald-500/10 dark:text-emerald-300",
  },
};

export const subjectAccent: Record<string, string> = {
  blue: "from-blue-500 to-indigo-500",
  violet: "from-violet-500 to-purple-500",
  emerald: "from-emerald-500 to-teal-500",
  green: "from-green-500 to-emerald-500",
  amber: "from-amber-500 to-orange-500",
  cyan: "from-cyan-500 to-sky-500",
  indigo: "from-indigo-500 to-blue-500",
};

export function formatDate(value?: string | null): string {
  if (!value) return "-";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "-";
  return date.toLocaleDateString(undefined, { day: "numeric", month: "short", year: "numeric" });
}

export function timeAgo(value?: string | null): string {
  if (!value) return "-";
  const date = new Date(value);
  const seconds = Math.floor((Date.now() - date.getTime()) / 1000);
  if (Number.isNaN(seconds)) return "-";
  if (seconds < 60) return "just now";
  const minutes = Math.floor(seconds / 60);
  if (minutes < 60) return `${minutes}m ago`;
  const hours = Math.floor(minutes / 60);
  if (hours < 24) return `${hours}h ago`;
  const days = Math.floor(hours / 24);
  if (days < 30) return `${days}d ago`;
  return formatDate(value);
}

export function formatMinutes(minutes: number): string {
  if (!minutes) return "0m";
  const hours = Math.floor(minutes / 60);
  const rest = minutes % 60;
  return hours ? `${hours}h ${rest}m` : `${rest}m`;
}

export const formatIcon: Record<string, string> = {
  text: "📄",
  visual: "🖼️",
  audio: "🎧",
  practice: "✍️",
};

export const eventLabels: Record<string, string> = {
  opened_subject: "Opened subject",
  opened_chapter: "Opened chapter",
  opened_topic: "Opened topic",
  opened_resource: "Opened resource",
  completed_resource: "Completed resource",
  spent_time: "Studied",
  attempted_question: "Attempted question",
  correct_answer: "Correct answer",
  incorrect_answer: "Incorrect answer",
  started_quiz: "Started quiz",
  completed_quiz: "Completed quiz",
  retook_quiz: "Retook quiz",
  asked_chatbot: "Asked the AI tutor",
  requested_explanation: "Requested an explanation",
  selected_text: "Chose a text resource",
  selected_visual: "Chose a visual resource",
  selected_audio: "Chose an audio resource",
  selected_practice: "Chose a practice resource",
  abandoned_topic: "Left a topic early",
  viewed_recommendation: "Viewed a recommendation",
  completed_recommendation: "Completed a recommendation",
};

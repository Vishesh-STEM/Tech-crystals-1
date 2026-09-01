import { ReactNode } from "react";
import { AlertCircle, Inbox, Loader2, RefreshCw } from "lucide-react";
import { masteryTone, toneClasses } from "../../lib/format";

export function Card({ children, className = "" }: { children: ReactNode; className?: string }) {
  return <div className={`card p-5 ${className}`}>{children}</div>;
}

export function SectionHeader({
  title,
  subtitle,
  action,
}: {
  title: string;
  subtitle?: string;
  action?: ReactNode;
}) {
  return (
    <div className="mb-4 flex items-end justify-between gap-3">
      <div>
        <h2 className="section-title">{title}</h2>
        {subtitle ? <p className="muted mt-0.5">{subtitle}</p> : null}
      </div>
      {action}
    </div>
  );
}

export function ProgressBar({
  value,
  className = "",
  showLabel = false,
}: {
  value: number;
  className?: string;
  showLabel?: boolean;
}) {
  const clamped = Math.max(0, Math.min(100, value || 0));
  const tone = toneClasses[masteryTone(clamped)];
  return (
    <div className={`flex items-center gap-2 ${className}`}>
      <div className="h-2 w-full overflow-hidden rounded-full bg-ink-200 dark:bg-white/10">
        <div
          className={`h-full rounded-full transition-all duration-700 ${tone.bar}`}
          style={{ width: `${clamped}%` }}
          role="progressbar"
          aria-valuenow={Math.round(clamped)}
          aria-valuemin={0}
          aria-valuemax={100}
        />
      </div>
      {showLabel ? (
        <span className={`w-11 shrink-0 text-right text-xs font-semibold ${tone.text}`}>
          {Math.round(clamped)}%
        </span>
      ) : null}
    </div>
  );
}

export function MasteryChip({ value, label }: { value: number; label?: string }) {
  const tone = toneClasses[masteryTone(value)];
  return (
    <span className={`chip ${tone.chip}`}>
      {label ?? `${Math.round(value)}/100`}
    </span>
  );
}

export function Badge({ children, tone = "neutral" }: { children: ReactNode; tone?: string }) {
  const tones: Record<string, string> = {
    neutral: "bg-ink-100 text-ink-600 dark:bg-white/10 dark:text-ink-200",
    brand: "bg-brand-50 text-brand-700 dark:bg-brand-500/15 dark:text-brand-200",
    success: "bg-emerald-50 text-emerald-700 dark:bg-emerald-500/15 dark:text-emerald-300",
    warn: "bg-amber-50 text-amber-700 dark:bg-amber-500/15 dark:text-amber-300",
    danger: "bg-rose-50 text-rose-700 dark:bg-rose-500/15 dark:text-rose-300",
  };
  return <span className={`chip ${tones[tone] ?? tones.neutral}`}>{children}</span>;
}

export function Spinner({ label }: { label?: string }) {
  return (
    <div className="flex items-center justify-center gap-2 py-10 text-ink-500 dark:text-ink-400">
      <Loader2 className="animate-spin" size={18} />
      <span className="text-sm">{label ?? "Loading..."}</span>
    </div>
  );
}

export function Skeleton({ className = "" }: { className?: string }) {
  return (
    <div className={`relative overflow-hidden rounded-xl bg-ink-200/70 dark:bg-white/5 ${className}`}>
      <div className="absolute inset-0 -translate-x-full animate-shimmer bg-gradient-to-r from-transparent via-white/50 to-transparent dark:via-white/10" />
    </div>
  );
}

export function EmptyState({
  title,
  description,
  action,
  icon,
}: {
  title: string;
  description?: string;
  action?: ReactNode;
  icon?: ReactNode;
}) {
  return (
    <div className="flex flex-col items-center justify-center rounded-2xl border border-dashed border-ink-200 px-6 py-12 text-center dark:border-white/10">
      <div className="mb-3 text-ink-400 dark:text-ink-500">{icon ?? <Inbox size={28} />}</div>
      <p className="font-semibold text-ink-800 dark:text-ink-100">{title}</p>
      {description ? <p className="muted mt-1 max-w-md">{description}</p> : null}
      {action ? <div className="mt-4">{action}</div> : null}
    </div>
  );
}

export function ErrorState({ message, onRetry }: { message: string; onRetry?: () => void }) {
  return (
    <div className="flex flex-col items-center justify-center rounded-2xl border border-rose-200 bg-rose-50/60 px-6 py-10 text-center dark:border-rose-500/20 dark:bg-rose-500/5">
      <AlertCircle className="mb-2 text-rose-500" size={26} />
      <p className="font-semibold text-rose-800 dark:text-rose-200">Something went wrong</p>
      <p className="mt-1 max-w-md text-sm text-rose-700/80 dark:text-rose-300/80">{message}</p>
      {onRetry ? (
        <button className="btn-secondary mt-4" onClick={onRetry}>
          <RefreshCw size={15} /> Try again
        </button>
      ) : null}
    </div>
  );
}

export function StatTile({
  label,
  value,
  hint,
  icon,
}: {
  label: string;
  value: ReactNode;
  hint?: string;
  icon?: ReactNode;
}) {
  return (
    <div className="card flex items-center gap-3 p-4">
      {icon ? (
        <div className="grid h-10 w-10 shrink-0 place-items-center rounded-xl bg-brand-50 text-brand-600 dark:bg-brand-500/15 dark:text-brand-300">
          {icon}
        </div>
      ) : null}
      <div className="min-w-0">
        <p className="truncate text-xs font-medium uppercase tracking-wide text-ink-500 dark:text-ink-400">{label}</p>
        <p className="font-display text-xl font-semibold text-ink-900 dark:text-white">{value}</p>
        {hint ? <p className="truncate text-xs text-ink-500 dark:text-ink-400">{hint}</p> : null}
      </div>
    </div>
  );
}

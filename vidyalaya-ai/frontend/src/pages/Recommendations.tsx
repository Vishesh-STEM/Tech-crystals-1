import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { CheckCircle2, ListChecks, Play, RefreshCw, X } from "lucide-react";
import { Card, EmptyState, ErrorState, SectionHeader, Skeleton } from "../components/ui/Primitives";
import { useToast } from "../context/ToastContext";
import { endpoints, errorMessage } from "../lib/api";

const kindStyles: Record<string, string> = {
  revise: "bg-amber-50 text-amber-700 dark:bg-amber-500/15 dark:text-amber-300",
  practice: "bg-brand-50 text-brand-700 dark:bg-brand-500/15 dark:text-brand-200",
  advance: "bg-emerald-50 text-emerald-700 dark:bg-emerald-500/15 dark:text-emerald-300",
  resume: "bg-violet-50 text-violet-700 dark:bg-violet-500/15 dark:text-violet-300",
  prerequisite: "bg-rose-50 text-rose-700 dark:bg-rose-500/15 dark:text-rose-300",
  format: "bg-cyan-50 text-cyan-700 dark:bg-cyan-500/15 dark:text-cyan-300",
};

export default function Recommendations() {
  const toast = useToast();
  const [items, setItems] = useState<any[]>([]);
  const [status, setStatus] = useState("pending");
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState("");

  async function load(nextStatus = status) {
    setLoading(true);
    setError("");
    try {
      setItems(await endpoints.recommendations(nextStatus, 20));
    } catch (err) {
      setError(errorMessage(err));
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load(status);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [status]);

  async function regenerate() {
    setRefreshing(true);
    try {
      setItems(await endpoints.refreshRecommendations());
      setStatus("pending");
      toast.success("Study plan refreshed from your latest results.");
    } catch (err) {
      toast.error(errorMessage(err));
    } finally {
      setRefreshing(false);
    }
  }

  async function act(id: number, action: "complete" | "dismiss") {
    try {
      await endpoints.recommendationAction(id, action);
      setItems((current) => current.filter((item) => item.id !== id));
      toast.success(action === "complete" ? "Marked as done." : "Dismissed.");
    } catch (err) {
      toast.error(errorMessage(err));
    }
  }

  return (
    <div className="space-y-5">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <h1 className="font-display text-2xl font-semibold text-ink-900 dark:text-white">For you</h1>
          <p className="muted mt-1">
            Built from mastery, recent performance, prerequisites, difficulty and which formats work for you.
          </p>
        </div>
        <div className="flex gap-2">
          <select className="input w-36" value={status} onChange={(event) => setStatus(event.target.value)} aria-label="Filter">
            <option value="pending">Pending</option>
            <option value="done">Completed</option>
            <option value="dismissed">Dismissed</option>
            <option value="all">All</option>
          </select>
          <button className="btn-primary" onClick={regenerate} disabled={refreshing}>
            <RefreshCw size={15} className={refreshing ? "animate-spin" : ""} /> Refresh plan
          </button>
        </div>
      </div>

      {loading ? (
        <div className="space-y-3">
          {[0, 1, 2].map((key) => (
            <Skeleton key={key} className="h-24" />
          ))}
        </div>
      ) : error ? (
        <ErrorState message={error} onRetry={() => load()} />
      ) : items.length === 0 ? (
        <EmptyState
          icon={<ListChecks size={26} />}
          title="Nothing here yet"
          description="Attempt a quiz or study a topic and your personalised plan will appear."
          action={<Link to="/quizzes" className="btn-primary text-sm">Browse quizzes</Link>}
        />
      ) : (
        <ul className="space-y-3">
          {items.map((item) => (
            <li key={item.id}>
              <Card className="flex flex-wrap items-start gap-4">
                <div className="min-w-0 flex-1">
                  <div className="mb-1 flex flex-wrap items-center gap-2">
                    <span className={`chip ${kindStyles[item.kind] ?? kindStyles.revise}`}>{item.kind}</span>
                    <span className="text-xs text-ink-400">
                      priority {Math.round(item.priority * 100)}% · ~{item.estimated_minutes} min
                    </span>
                  </div>
                  <p className="font-semibold text-ink-900 dark:text-white">{item.title}</p>
                  <p className="muted mt-1">{item.reason}</p>
                </div>
                <div className="flex flex-wrap gap-2">
                  <Link to={item.action_url || "/subjects"} className="btn-primary text-sm">
                    <Play size={14} /> {item.action_label}
                  </Link>
                  {item.status === "pending" ? (
                    <>
                      <button className="btn-secondary text-sm" onClick={() => act(item.id, "complete")}>
                        <CheckCircle2 size={14} /> Done
                      </button>
                      <button className="btn-ghost text-sm" onClick={() => act(item.id, "dismiss")} aria-label="Dismiss">
                        <X size={14} />
                      </button>
                    </>
                  ) : null}
                </div>
              </Card>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

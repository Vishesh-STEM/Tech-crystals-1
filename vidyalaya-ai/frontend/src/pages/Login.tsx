import { FormEvent, useEffect, useState } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";
import { GraduationCap, Loader2, LogIn, Sparkles } from "lucide-react";
import { useAuth } from "../context/AuthContext";
import { useToast } from "../context/ToastContext";
import { endpoints, errorMessage } from "../lib/api";
import AuthShell from "./AuthShell";

export default function Login() {
  const { login, user } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const toast = useToast();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [demo, setDemo] = useState<any>(null);

  useEffect(() => {
    if (user) navigate("/dashboard", { replace: true });
  }, [user, navigate]);

  useEffect(() => {
    if (new URLSearchParams(location.search).get("expired")) {
      toast.info("Your session expired. Please log in again.");
    }
    endpoints.demoCredentials().then(setDemo).catch(() => undefined);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  async function onSubmit(event: FormEvent) {
    event.preventDefault();
    setError("");
    setLoading(true);
    try {
      const account = await login(email.trim(), password);
      toast.success(`Welcome back, ${account.full_name.split(" ")[0]}!`);
      navigate(account.role === "student" ? "/dashboard" : "/admin", { replace: true });
    } catch (err) {
      setError(errorMessage(err, "Could not log you in."));
    } finally {
      setLoading(false);
    }
  }

  function fillDemo(kind: "student" | "teacher") {
    const account = demo?.[kind];
    if (!account) return;
    setEmail(account.email);
    setPassword(account.password);
  }

  return (
    <AuthShell
      title="Welcome back"
      subtitle="Log in to continue your Class 12 preparation."
      footer={
        <p className="muted">
          New to Vidyalaya AI?{" "}
          <Link to="/register" className="font-semibold text-brand-600 hover:underline dark:text-brand-300">
            Create a free account
          </Link>
        </p>
      }
    >
      <form onSubmit={onSubmit} className="space-y-4" noValidate>
        <div>
          <label className="label" htmlFor="email">Email address</label>
          <input
            id="email"
            type="email"
            autoComplete="email"
            className="input"
            placeholder="you@school.edu"
            value={email}
            onChange={(event) => setEmail(event.target.value)}
            required
          />
        </div>
        <div>
          <label className="label" htmlFor="password">Password</label>
          <input
            id="password"
            type="password"
            autoComplete="current-password"
            className="input"
            placeholder="••••••••"
            value={password}
            onChange={(event) => setPassword(event.target.value)}
            required
          />
        </div>

        {error ? (
          <p role="alert" className="rounded-xl bg-rose-50 px-3 py-2 text-sm text-rose-700 dark:bg-rose-500/10 dark:text-rose-300">
            {error}
          </p>
        ) : null}

        <button type="submit" className="btn-primary w-full" disabled={loading}>
          {loading ? <Loader2 className="animate-spin" size={17} /> : <LogIn size={17} />}
          {loading ? "Signing in..." : "Log in"}
        </button>
      </form>

      {demo ? (
        <div className="mt-6 rounded-xl border border-dashed border-ink-200 p-4 dark:border-white/10">
          <p className="mb-2 flex items-center gap-1.5 text-xs font-semibold uppercase tracking-wide text-ink-500 dark:text-ink-400">
            <Sparkles size={14} /> Demo accounts
          </p>
          <div className="flex flex-wrap gap-2">
            <button type="button" className="btn-secondary text-xs" onClick={() => fillDemo("student")}>
              <GraduationCap size={14} /> Student · {demo.student?.email}
            </button>
            <button type="button" className="btn-secondary text-xs" onClick={() => fillDemo("teacher")}>
              Teacher · {demo.teacher?.email}
            </button>
          </div>
        </div>
      ) : null}
    </AuthShell>
  );
}

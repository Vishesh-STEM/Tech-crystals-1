import { FormEvent, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { Loader2, UserPlus } from "lucide-react";
import { useAuth } from "../context/AuthContext";
import { useToast } from "../context/ToastContext";
import { errorMessage } from "../lib/api";
import AuthShell from "./AuthShell";

export default function Register() {
  const { register } = useAuth();
  const navigate = useNavigate();
  const toast = useToast();
  const [form, setForm] = useState({
    full_name: "",
    email: "",
    password: "",
    school: "",
    stream: "Science",
    class_level: "12",
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  function update(field: string, value: string) {
    setForm((current) => ({ ...current, [field]: value }));
  }

  async function onSubmit(event: FormEvent) {
    event.preventDefault();
    setError("");
    setLoading(true);
    try {
      const account = await register({ ...form, email: form.email.trim().toLowerCase() });
      toast.success(`Welcome to Vidyalaya AI, ${account.full_name.split(" ")[0]}!`);
      navigate("/dashboard", { replace: true });
    } catch (err) {
      setError(errorMessage(err, "Could not create your account."));
    } finally {
      setLoading(false);
    }
  }

  return (
    <AuthShell
      title="Create your account"
      subtitle="Start tracking your Class 12 mastery in under a minute."
      footer={
        <p className="muted">
          Already have an account?{" "}
          <Link to="/login" className="font-semibold text-brand-600 hover:underline dark:text-brand-300">
            Log in
          </Link>
        </p>
      }
    >
      <form onSubmit={onSubmit} className="space-y-4" noValidate>
        <div>
          <label className="label" htmlFor="full_name">Full name</label>
          <input
            id="full_name"
            className="input"
            placeholder="Abhinav Sharma"
            value={form.full_name}
            onChange={(event) => update("full_name", event.target.value)}
            required
            minLength={2}
          />
        </div>
        <div>
          <label className="label" htmlFor="email">Email address</label>
          <input
            id="email"
            type="email"
            className="input"
            placeholder="you@school.edu"
            value={form.email}
            onChange={(event) => update("email", event.target.value)}
            required
          />
        </div>
        <div>
          <label className="label" htmlFor="password">Password</label>
          <input
            id="password"
            type="password"
            className="input"
            placeholder="At least 8 characters with a number"
            value={form.password}
            onChange={(event) => update("password", event.target.value)}
            required
            minLength={8}
          />
          <p className="mt-1 text-xs text-ink-500 dark:text-ink-400">
            Minimum 8 characters, including at least one letter and one number.
          </p>
        </div>
        <div className="grid grid-cols-2 gap-3">
          <div>
            <label className="label" htmlFor="school">School (optional)</label>
            <input
              id="school"
              className="input"
              placeholder="Delhi Public School"
              value={form.school}
              onChange={(event) => update("school", event.target.value)}
            />
          </div>
          <div>
            <label className="label" htmlFor="stream">Stream</label>
            <select
              id="stream"
              className="input"
              value={form.stream}
              onChange={(event) => update("stream", event.target.value)}
            >
              <option>Science</option>
              <option>Commerce</option>
              <option>Humanities</option>
            </select>
          </div>
        </div>

        {error ? (
          <p role="alert" className="rounded-xl bg-rose-50 px-3 py-2 text-sm text-rose-700 dark:bg-rose-500/10 dark:text-rose-300">
            {error}
          </p>
        ) : null}

        <button type="submit" className="btn-primary w-full" disabled={loading}>
          {loading ? <Loader2 className="animate-spin" size={17} /> : <UserPlus size={17} />}
          {loading ? "Creating your account..." : "Create account"}
        </button>
      </form>
    </AuthShell>
  );
}

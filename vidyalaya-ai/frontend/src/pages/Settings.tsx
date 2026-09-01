import { useEffect, useState } from "react";
import { KeyRound, Moon, RefreshCw, Server, Sun } from "lucide-react";
import { Card, SectionHeader } from "../components/ui/Primitives";
import { useAuth } from "../context/AuthContext";
import { useTheme } from "../context/ThemeContext";
import { useToast } from "../context/ToastContext";
import { endpoints, errorMessage } from "../lib/api";

const EMOJI = ["🎓", "📚", "🚀", "🧠", "⭐", "🔥", "🌱", "🦉"];

export default function Settings() {
  const { user, applyAuth } = useAuth();
  const { theme, toggle } = useTheme();
  const toast = useToast();
  const [meta, setMeta] = useState<any>(null);
  const [health, setHealth] = useState<any>(null);
  const [passwords, setPasswords] = useState({ current_password: "", new_password: "" });
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    endpoints.meta().then(setMeta).catch(() => undefined);
    endpoints.health().then(setHealth).catch(() => undefined);
  }, []);

  async function chooseEmoji(emoji: string) {
    try {
      const data = await endpoints.updateProfile({ avatar_emoji: emoji });
      applyAuth(data);
      toast.success("Avatar updated.");
    } catch (err) {
      toast.error(errorMessage(err));
    }
  }

  async function changePassword() {
    setSaving(true);
    try {
      await endpoints.changePassword(passwords.current_password, passwords.new_password);
      setPasswords({ current_password: "", new_password: "" });
      toast.success("Password changed.");
    } catch (err) {
      toast.error(errorMessage(err));
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="max-w-3xl space-y-6">
      <h1 className="font-display text-2xl font-semibold text-ink-900 dark:text-white">Settings</h1>

      <Card>
        <SectionHeader title="Appearance" subtitle="Vidyalaya AI follows your system theme by default." />
        <button className="btn-secondary" onClick={toggle}>
          {theme === "dark" ? <Sun size={15} /> : <Moon size={15} />}
          Switch to {theme === "dark" ? "light" : "dark"} mode
        </button>
        <div className="mt-5">
          <p className="label">Avatar</p>
          <div className="flex flex-wrap gap-2">
            {EMOJI.map((emoji) => (
              <button
                key={emoji}
                onClick={() => chooseEmoji(emoji)}
                className={`grid h-11 w-11 place-items-center rounded-xl border text-xl transition ${
                  user?.avatar_emoji === emoji
                    ? "border-brand-400 bg-brand-50 dark:border-brand-500/50 dark:bg-brand-500/10"
                    : "border-ink-200 hover:border-brand-300 dark:border-white/10"
                }`}
              >
                {emoji}
              </button>
            ))}
          </div>
        </div>
      </Card>

      <Card>
        <SectionHeader title="Password" subtitle="Use at least 8 characters with a letter and a number." />
        <div className="grid gap-3 sm:grid-cols-2">
          <div>
            <label className="label" htmlFor="current">Current password</label>
            <input
              id="current"
              type="password"
              className="input"
              value={passwords.current_password}
              onChange={(event) => setPasswords({ ...passwords, current_password: event.target.value })}
            />
          </div>
          <div>
            <label className="label" htmlFor="next">New password</label>
            <input
              id="next"
              type="password"
              className="input"
              value={passwords.new_password}
              onChange={(event) => setPasswords({ ...passwords, new_password: event.target.value })}
            />
          </div>
        </div>
        <button
          className="btn-primary mt-4"
          onClick={changePassword}
          disabled={saving || !passwords.current_password || passwords.new_password.length < 8}
        >
          <KeyRound size={15} /> {saving ? "Updating..." : "Change password"}
        </button>
      </Card>

      <Card>
        <SectionHeader
          title="Platform status"
          subtitle="Everything runs locally - no paid AI APIs."
          action={
            <button className="btn-ghost text-sm" onClick={() => endpoints.meta().then(setMeta)}>
              <RefreshCw size={14} /> Refresh
            </button>
          }
        />
        {meta ? (
          <dl className="grid gap-3 sm:grid-cols-2">
            {[
              ["AI tutor", `${meta.ai.mode === "ollama" ? "Local model" : "Offline mode"} · ${meta.ai.configured_model}`],
              ["AI detail", meta.ai.detail],
              ["Vector store", `${meta.vector.backend} · ${meta.vector.documents} passages`],
              ["Embeddings", `${meta.vector.embedding_backend} (${meta.vector.embedding_dimension}d)`],
              ["ML models", Object.values(meta.ml_models).join(", ")],
              ["Moodle", meta.moodle.enabled ? "Connected" : "Integration layer ready (disabled)"],
              [
                "Database",
                health
                  ? `${health.database_engine} · ${health.database}${health.database_fallback_active ? " (SQLite fallback active)" : ""}`
                  : "checking...",
              ],
              ["Status", health ? `${health.status} · v${health.version} · ${health.environment}` : "checking..."],
            ].map(([label, value]) => (
              <div key={String(label)} className="rounded-xl bg-ink-50 p-3 dark:bg-white/5">
                <dt className="text-[11px] uppercase tracking-wide text-ink-500 dark:text-ink-400">{label}</dt>
                <dd className="mt-0.5 text-sm text-ink-800 dark:text-ink-100">{String(value)}</dd>
              </div>
            ))}
          </dl>
        ) : (
          <p className="muted"><Server size={14} className="mr-1 inline" /> Loading platform status...</p>
        )}
      </Card>
    </div>
  );
}

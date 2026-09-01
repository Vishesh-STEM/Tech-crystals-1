import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { Activity, BookOpen, Flame, GraduationCap, Save } from "lucide-react";
import { LearningProfileRadar } from "../components/charts/Charts";
import { Card, EmptyState, ErrorState, ProgressBar, SectionHeader, Skeleton, StatTile } from "../components/ui/Primitives";
import { useAuth } from "../context/AuthContext";
import { useToast } from "../context/ToastContext";
import { endpoints, errorMessage } from "../lib/api";
import { eventLabels, formatMinutes, timeAgo } from "../lib/format";

export default function Profile() {
  const { user, student, applyAuth } = useAuth();
  const toast = useToast();
  const [profile, setProfile] = useState<any>(null);
  const [activity, setActivity] = useState<any[]>([]);
  const [years, setYears] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [saving, setSaving] = useState(false);
  const [form, setForm] = useState({ full_name: "", school: "", roll_number: "", guardian_name: "", phone: "", daily_goal_minutes: 45 });

  async function load() {
    setLoading(true);
    setError("");
    try {
      const [learningProfile, events, yearList] = await Promise.all([
        endpoints.learningProfile(true),
        endpoints.activity(15),
        endpoints.years(),
      ]);
      setProfile(learningProfile);
      setActivity(events);
      setYears(yearList);
    } catch (err) {
      setError(errorMessage(err));
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load();
  }, []);

  useEffect(() => {
    setForm({
      full_name: user?.full_name ?? "",
      school: student?.school ?? "",
      roll_number: student?.roll_number ?? "",
      guardian_name: student?.guardian_name ?? "",
      phone: student?.phone ?? "",
      daily_goal_minutes: student?.daily_goal_minutes ?? 45,
    });
  }, [user, student]);

  async function save() {
    setSaving(true);
    try {
      const data = await endpoints.updateProfile({ ...form, daily_goal_minutes: Number(form.daily_goal_minutes) });
      applyAuth(data);
      toast.success("Profile updated.");
    } catch (err) {
      toast.error(errorMessage(err));
    } finally {
      setSaving(false);
    }
  }

  if (loading) return <Skeleton className="h-96 w-full" />;
  if (error) return <ErrorState message={error} onRetry={load} />;

  const formats: [string, number][] = [
    ["Text", profile?.text_effectiveness ?? 0],
    ["Visual", profile?.visual_effectiveness ?? 0],
    ["Audio", profile?.audio_effectiveness ?? 0],
    ["Practice", profile?.practice_effectiveness ?? 0],
  ];

  return (
    <div className="space-y-6">
      <Card className="flex flex-wrap items-center gap-4">
        <span className="grid h-16 w-16 place-items-center rounded-2xl bg-gradient-to-br from-brand-500 to-violet-500 text-3xl text-white">
          {user?.avatar_emoji || "🎓"}
        </span>
        <div className="min-w-0 flex-1">
          <h1 className="font-display text-2xl font-semibold text-ink-900 dark:text-white">{user?.full_name}</h1>
          <p className="muted">{user?.email}</p>
          <p className="muted mt-0.5">
            Class {profile?.student?.class_level ?? "12"} · {profile?.student?.stream ?? "Science"} ·{" "}
            {profile?.student?.school || "School not set"} · {profile?.student?.academic_year}
          </p>
        </div>
        <Link to="/settings" className="btn-secondary">Settings</Link>
      </Card>

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <StatTile label="Study streak" value={`${profile?.study_streak_days ?? 0} days`} icon={<Flame size={18} />} />
        <StatTile label="Average session" value={formatMinutes(Math.round(profile?.average_session_minutes ?? 0))} icon={<Activity size={18} />} />
        <StatTile label="Best format" value={(profile?.strongest_format ?? "practice").replace(/^\w/, (c: string) => c.toUpperCase())} icon={<BookOpen size={18} />} />
        <StatTile label="Preferred difficulty" value={profile?.preferred_difficulty ?? "medium"} icon={<GraduationCap size={18} />} />
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        <Card>
          <SectionHeader title="Learning profile" subtitle="How effective each study format has been for you." />
          <LearningProfileRadar profile={profile || {}} />
          <ul className="mt-4 space-y-2">
            {formats.map(([label, value]) => (
              <li key={label}>
                <div className="mb-1 flex items-center justify-between text-sm">
                  <span className="text-ink-700 dark:text-ink-200">{label}</span>
                  <span className="font-semibold text-ink-900 dark:text-white">{Math.round(value * 100)}%</span>
                </div>
                <ProgressBar value={value * 100} />
                <p className="mt-0.5 text-[11px] text-ink-400">
                  {profile?.samples?.[label.toLowerCase()] ?? 0} sessions measured
                </p>
              </li>
            ))}
          </ul>
          <p className="muted mt-4 text-xs">{profile?.note}</p>
        </Card>

        <div className="space-y-6">
          <Card>
            <SectionHeader title="Your details" subtitle="Keep your profile up to date." />
            <div className="grid gap-3 sm:grid-cols-2">
              <div className="sm:col-span-2">
                <label className="label" htmlFor="full_name">Full name</label>
                <input id="full_name" className="input" value={form.full_name} onChange={(e) => setForm({ ...form, full_name: e.target.value })} />
              </div>
              <div>
                <label className="label" htmlFor="school">School</label>
                <input id="school" className="input" value={form.school} onChange={(e) => setForm({ ...form, school: e.target.value })} />
              </div>
              <div>
                <label className="label" htmlFor="roll">Roll number</label>
                <input id="roll" className="input" value={form.roll_number} onChange={(e) => setForm({ ...form, roll_number: e.target.value })} />
              </div>
              <div>
                <label className="label" htmlFor="guardian">Guardian name</label>
                <input id="guardian" className="input" value={form.guardian_name} onChange={(e) => setForm({ ...form, guardian_name: e.target.value })} />
              </div>
              <div>
                <label className="label" htmlFor="goal">Daily goal (minutes)</label>
                <input
                  id="goal"
                  type="number"
                  min={10}
                  max={600}
                  className="input"
                  value={form.daily_goal_minutes}
                  onChange={(e) => setForm({ ...form, daily_goal_minutes: Number(e.target.value) })}
                />
              </div>
            </div>
            <button className="btn-primary mt-4" onClick={save} disabled={saving}>
              <Save size={15} /> {saving ? "Saving..." : "Save changes"}
            </button>
          </Card>

          <Card>
            <SectionHeader title="Academic years" subtitle="Old progress is preserved, never deleted." />
            <ul className="space-y-2">
              {years.map((year) => (
                <li key={year.id} className="flex items-center justify-between rounded-lg bg-ink-50 px-3 py-2 text-sm dark:bg-white/5">
                  <span className="text-ink-800 dark:text-ink-100">
                    {year.label} {year.is_current ? <span className="chip ml-1 bg-brand-100 text-brand-700 dark:bg-brand-500/20 dark:text-brand-200">current</span> : null}
                  </span>
                  <span className="font-semibold text-ink-900 dark:text-white">{Math.round(year.overall_mastery)}%</span>
                </li>
              ))}
            </ul>
          </Card>
        </div>
      </div>

      <Card>
        <SectionHeader title="Recent activity" subtitle="Everything the platform learns from." />
        {activity.length === 0 ? (
          <EmptyState title="No activity yet" />
        ) : (
          <ul className="divide-y divide-ink-200/70 dark:divide-white/10">
            {activity.map((event) => (
              <li key={event.id} className="flex items-center justify-between gap-3 py-2.5 text-sm">
                <span className="min-w-0 flex-1 truncate text-ink-700 dark:text-ink-200">
                  {eventLabels[event.event_type] ?? event.event_type}
                  {event.result ? <span className="text-ink-400"> · {event.result}</span> : null}
                </span>
                <span className="shrink-0 text-xs text-ink-400">{timeAgo(event.created_at)}</span>
              </li>
            ))}
          </ul>
        )}
      </Card>
    </div>
  );
}

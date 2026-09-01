import { useEffect, useMemo, useRef, useState } from "react";
import { Link, useParams } from "react-router-dom";
import {
  ArrowLeft, ArrowRight, CheckCircle2, Clock, Eye, RotateCcw, Send, Sparkles, Target, XCircle,
} from "lucide-react";
import { DifficultyBars } from "../components/charts/Charts";
import { Card, EmptyState, ErrorState, ProgressBar, SectionHeader, Skeleton } from "../components/ui/Primitives";
import { useToast } from "../context/ToastContext";
import { endpoints, errorMessage } from "../lib/api";
import { formatDate, masteryTone, toneClasses } from "../lib/format";

type Stage = "intro" | "running" | "result";

export default function Quiz() {
  const { quizId } = useParams();
  const toast = useToast();
  const [quiz, setQuiz] = useState<any>(null);
  const [stage, setStage] = useState<Stage>("intro");
  const [attempt, setAttempt] = useState<any>(null);
  const [answers, setAnswers] = useState<Record<number, string>>({});
  const [index, setIndex] = useState(0);
  const [result, setResult] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");
  const [seconds, setSeconds] = useState(0);
  const timer = useRef<number | null>(null);

  async function load() {
    setLoading(true);
    setError("");
    try {
      setQuiz(await endpoints.quiz(quizId!));
    } catch (err) {
      setError(errorMessage(err));
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load();
    return () => {
      if (timer.current) window.clearInterval(timer.current);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [quizId]);

  const questions = attempt?.questions ?? [];
  const answeredCount = useMemo(
    () => questions.filter((question: any) => answers[question.id]).length,
    [questions, answers],
  );

  async function start() {
    try {
      const data = await endpoints.startAttempt(quizId!);
      setAttempt(data);
      setAnswers({});
      setIndex(0);
      setSeconds(0);
      setStage("running");
      timer.current = window.setInterval(() => setSeconds((value) => value + 1), 1000);
    } catch (err) {
      toast.error(errorMessage(err));
    }
  }

  async function openStoredAttempt(attemptId: number) {
    try {
      const stored = await endpoints.attempt(attemptId);
      setResult({ ...stored, mastery_updates: [], new_recommendations: [] });
      setStage("result");
    } catch (err) {
      toast.error(errorMessage(err));
    }
  }

  async function submit() {
    if (!attempt) return;
    setSubmitting(true);
    try {
      const payload = {
        answers: questions.map((question: any) => ({
          question_id: question.id,
          answer: answers[question.id] ?? "",
          time_spent_seconds: Math.round(seconds / Math.max(1, questions.length)),
        })),
        duration_seconds: seconds,
      };
      const data = await endpoints.submitAttempt(quizId!, attempt.attempt_id, payload);
      if (timer.current) window.clearInterval(timer.current);
      setResult(data);
      setStage("result");
      toast.success(`Scored ${Math.round(data.accuracy)}% - mastery and recommendations updated.`);
    } catch (err) {
      toast.error(errorMessage(err));
    } finally {
      setSubmitting(false);
    }
  }

  if (loading) return <Skeleton className="h-96 w-full" />;
  if (error) return <ErrorState message={error} onRetry={load} />;
  if (!quiz) return null;

  const minutes = String(Math.floor(seconds / 60)).padStart(2, "0");
  const secs = String(seconds % 60).padStart(2, "0");

  // ---------- intro ----------
  if (stage === "intro") {
    return (
      <div className="mx-auto max-w-3xl space-y-5">
        <Link to={`/subjects/${quiz.subject_id}`} className="btn-ghost -ml-2 text-sm">
          <ArrowLeft size={15} /> {quiz.subject_name}
        </Link>
        <Card>
          <div className="flex items-start gap-3">
            <span className="text-3xl">{quiz.icon}</span>
            <div>
              <h1 className="font-display text-2xl font-semibold text-ink-900 dark:text-white">{quiz.title}</h1>
              <p className="muted mt-1">{quiz.description}</p>
            </div>
          </div>
          <dl className="mt-5 grid grid-cols-2 gap-3 sm:grid-cols-4">
            {[
              ["Questions", quiz.question_count],
              ["Time limit", `${quiz.time_limit_minutes} min`],
              ["Pass mark", `${quiz.pass_percentage}%`],
              ["Difficulty", quiz.difficulty],
            ].map(([label, value]) => (
              <div key={String(label)} className="rounded-xl bg-ink-50 p-3 text-center dark:bg-white/5">
                <dt className="text-[11px] uppercase tracking-wide text-ink-500 dark:text-ink-400">{label}</dt>
                <dd className="font-display font-semibold text-ink-900 dark:text-white">{value}</dd>
              </div>
            ))}
          </dl>

          {quiz.previous_attempts?.length ? (
            <div className="mt-5">
              <h2 className="mb-2 text-sm font-semibold text-ink-800 dark:text-ink-100">Your previous attempts</h2>
              <ul className="space-y-2">
                {quiz.previous_attempts.map((previous: any) => (
                  <li key={previous.id}>
                    <button
                      onClick={() => openStoredAttempt(previous.id)}
                      className="flex w-full items-center justify-between rounded-lg bg-ink-50 px-3 py-2 text-sm transition hover:bg-ink-100 dark:bg-white/5 dark:hover:bg-white/10"
                      title="View this attempt with the correct answers"
                    >
                      <span className="text-ink-600 dark:text-ink-300">
                        Attempt {previous.attempt_number} · {formatDate(previous.submitted_at)}
                      </span>
                      <span className={`font-semibold ${toneClasses[masteryTone(previous.accuracy)].text}`}>
                        {Math.round(previous.accuracy)}% <Eye size={13} className="ml-1 inline opacity-60" />
                      </span>
                    </button>
                  </li>
                ))}
              </ul>
            </div>
          ) : null}

          <button className="btn-primary mt-6 w-full" onClick={start} disabled={!quiz.question_count}>
            <Target size={16} /> {quiz.previous_attempts?.length ? "Retake quiz" : "Start quiz"}
          </button>
        </Card>
      </div>
    );
  }

  // ---------- running ----------
  if (stage === "running") {
    const question = questions[index];
    if (!question) return <EmptyState title="This quiz has no questions" />;
    return (
      <div className="mx-auto max-w-3xl space-y-4">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <p className="font-display font-semibold text-ink-900 dark:text-white">{quiz.title}</p>
            <p className="muted">
              Question {index + 1} of {questions.length} · {answeredCount} answered
            </p>
          </div>
          <span className="chip bg-ink-100 text-ink-700 dark:bg-white/10 dark:text-ink-200">
            <Clock size={13} /> {minutes}:{secs}
          </span>
        </div>
        <ProgressBar value={((index + 1) / questions.length) * 100} />

        <Card>
          <div className="mb-3 flex items-center gap-2">
            <span className="chip bg-brand-50 text-brand-700 dark:bg-brand-500/15 dark:text-brand-200">
              {question.difficulty}
            </span>
            <span className="muted">{question.concept_tag}</span>
          </div>
          <p className="text-base font-medium text-ink-900 dark:text-white">{question.text}</p>

          <div className="mt-4 space-y-2">
            {(question.options || []).map((option: string) => {
              const selected = answers[question.id] === option;
              return (
                <button
                  key={option}
                  onClick={() => setAnswers((current) => ({ ...current, [question.id]: option }))}
                  className={`flex w-full items-center gap-3 rounded-xl border px-4 py-3 text-left text-sm transition ${
                    selected
                      ? "border-brand-400 bg-brand-50 text-brand-900 dark:border-brand-500/50 dark:bg-brand-500/10 dark:text-brand-100"
                      : "border-ink-200 hover:border-brand-300 hover:bg-ink-50 dark:border-white/10 dark:hover:bg-white/5"
                  }`}
                >
                  <span
                    className={`grid h-5 w-5 shrink-0 place-items-center rounded-full border ${
                      selected ? "border-brand-500 bg-brand-500 text-white" : "border-ink-300 dark:border-white/20"
                    }`}
                  >
                    {selected ? <CheckCircle2 size={13} /> : null}
                  </span>
                  {option}
                </button>
              );
            })}
            {!question.options?.length ? (
              <input
                className="input"
                placeholder="Type your answer"
                value={answers[question.id] ?? ""}
                onChange={(event) => setAnswers((current) => ({ ...current, [question.id]: event.target.value }))}
              />
            ) : null}
          </div>
        </Card>

        <div className="flex flex-wrap items-center justify-between gap-2">
          <button className="btn-secondary" disabled={index === 0} onClick={() => setIndex((value) => value - 1)}>
            <ArrowLeft size={15} /> Previous
          </button>
          <div className="flex flex-wrap gap-1.5">
            {questions.map((item: any, position: number) => (
              <button
                key={item.id}
                onClick={() => setIndex(position)}
                aria-label={`Go to question ${position + 1}`}
                className={`h-8 w-8 rounded-lg text-xs font-semibold transition ${
                  position === index
                    ? "bg-brand-600 text-white"
                    : answers[item.id]
                      ? "bg-emerald-100 text-emerald-700 dark:bg-emerald-500/20 dark:text-emerald-300"
                      : "bg-ink-100 text-ink-500 dark:bg-white/10 dark:text-ink-300"
                }`}
              >
                {position + 1}
              </button>
            ))}
          </div>
          {index === questions.length - 1 ? (
            <button className="btn-primary" onClick={submit} disabled={submitting}>
              <Send size={15} /> {submitting ? "Submitting..." : "Submit quiz"}
            </button>
          ) : (
            <button className="btn-primary" onClick={() => setIndex((value) => value + 1)}>
              Next <ArrowRight size={15} />
            </button>
          )}
        </div>
      </div>
    );
  }

  // ---------- result ----------
  const tone = toneClasses[masteryTone(result.accuracy)];
  const difficultyData = Object.entries(result.difficulty_breakdown || {}).map(([name, value]: any) => ({
    name,
    accuracy: value.accuracy ?? 0,
  }));

  return (
    <div className="mx-auto max-w-3xl space-y-5">
      <Card className="text-center">
        <p className="muted">{result.quiz_title} · attempt {result.attempt_number}</p>
        <p className={`font-display text-6xl font-semibold ${tone.text}`}>{Math.round(result.accuracy)}%</p>
        <p className="mt-1 text-ink-700 dark:text-ink-200">
          {result.score}/{result.max_score} marks · {Math.floor(result.duration_seconds / 60)}m {result.duration_seconds % 60}s
        </p>
        <span className={`chip mt-3 ${result.passed ? "bg-emerald-50 text-emerald-700 dark:bg-emerald-500/15 dark:text-emerald-300" : "bg-amber-50 text-amber-700 dark:bg-amber-500/15 dark:text-amber-300"}`}>
          {result.passed ? "Passed" : "Below the pass mark - review and retry"}
        </span>
        <div className="mt-5 flex flex-wrap justify-center gap-2">
          <button className="btn-secondary" onClick={start}>
            <RotateCcw size={15} /> Retry quiz
          </button>
          <Link to="/recommendations" className="btn-primary">
            <Sparkles size={15} /> See what to study next
          </Link>
        </div>
      </Card>

      {result.mastery_updates?.length ? (
        <Card>
          <SectionHeader title="Mastery updated" subtitle="Recomputed from this attempt and your history." />
          <ul className="space-y-2">
            {result.mastery_updates.map((update: any) => (
              <li key={update.topic_id} className="rounded-xl border border-ink-200/70 p-3 dark:border-white/10">
                <div className="flex items-center justify-between gap-2">
                  <Link to={`/topics/${update.topic_id}`} className="truncate text-sm font-medium text-ink-900 hover:underline dark:text-white">
                    {update.topic_name}
                  </Link>
                  <span className={`font-display font-semibold ${toneClasses[masteryTone(update.mastery)].text}`}>
                    {Math.round(update.mastery)}/100
                  </span>
                </div>
                {update.is_weak ? (
                  <p className="mt-1 text-xs text-amber-700 dark:text-amber-300">{update.reason}</p>
                ) : null}
              </li>
            ))}
          </ul>
        </Card>
      ) : null}

      {difficultyData.length ? (
        <Card>
          <SectionHeader title="Accuracy by difficulty" />
          <DifficultyBars data={difficultyData} />
        </Card>
      ) : null}

      <Card>
        <SectionHeader title="Review answers" subtitle="Every question with the correct answer and an explanation." />
        <ol className="space-y-3">
          {result.answers.map((answer: any, position: number) => (
            <li
              key={answer.question_id}
              className={`rounded-xl border p-4 ${
                answer.is_correct
                  ? "border-emerald-200 bg-emerald-50/50 dark:border-emerald-500/20 dark:bg-emerald-500/5"
                  : "border-rose-200 bg-rose-50/50 dark:border-rose-500/20 dark:bg-rose-500/5"
              }`}
            >
              <div className="flex items-start gap-2">
                {answer.is_correct ? (
                  <CheckCircle2 size={17} className="mt-0.5 shrink-0 text-emerald-500" />
                ) : (
                  <XCircle size={17} className="mt-0.5 shrink-0 text-rose-500" />
                )}
                <div className="min-w-0">
                  <p className="text-sm font-medium text-ink-900 dark:text-white">
                    {position + 1}. {answer.question_text}
                  </p>
                  <p className="mt-1.5 text-sm text-ink-600 dark:text-ink-300">
                    Your answer: <span className="font-medium">{answer.given_answer || "(not answered)"}</span>
                  </p>
                  {!answer.is_correct ? (
                    <p className="text-sm text-emerald-700 dark:text-emerald-300">
                      Correct answer: <span className="font-medium">{answer.correct_answer}</span>
                    </p>
                  ) : null}
                  {answer.explanation ? (
                    <p className="mt-1.5 text-xs text-ink-600 dark:text-ink-400">{answer.explanation}</p>
                  ) : null}
                  <Link to={`/topics/${answer.topic_id}`} className="mt-1.5 inline-block text-xs font-medium text-brand-600 hover:underline dark:text-brand-300">
                    Revise {answer.topic_name}
                  </Link>
                </div>
              </div>
            </li>
          ))}
        </ol>
      </Card>
    </div>
  );
}

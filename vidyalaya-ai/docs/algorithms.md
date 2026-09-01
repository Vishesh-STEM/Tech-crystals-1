# Algorithms

Every number the UI shows is derived from stored answers and events. Nothing is
hard-coded, and each rule lives in one function so it can be swapped for a
trained model later (see `app/ml/predictors.py`).

## 1. Topic mastery — `services/mastery.recompute_topic_mastery`

Inputs: all graded answers for (student, topic, academic year), plus the
student's activity events on that topic.

```
scores            = per-attempt percentage, newest first
recent            = 0.5·s1 + 0.3·s2 + 0.2·s3            (weights trimmed to len)
historical        = mean(scores)
base              = 0.65·recent + 0.35·historical
difficulty_acc    = 100 · Σ(weight of correct) / Σ(weight of all)
                    weights: easy 0.8, medium 1.0, hard 1.3
mastery           = 0.75·base + 0.25·difficulty_acc
mastery          += clamp(trend · 0.15, -6, +8)          trend = s1 - mean(rest)
mastery          -= 2 per repeated-mistake concept       (max 6)
mastery          += 1.5 per completed resource           (max 4)
mastery          -= min(10, (idle_days - 14)/7 · 2.5)    when idle_days > 14
mastery           = clamp(mastery, 0, 100)
confidence        = min(1, questions/12 · 0.7 + attempts/4 · 0.3)
```

A "repeated-mistake concept" is one missed at least twice **and** in at least
half of the times it was asked — two slips out of ten do not count.

Studied but never assessed → a low-confidence exposure score (max 30) and the
topic is never marked weak.

## 2. Weak-topic detection — `services/mastery.detect_weakness`

Requires ≥ 3 answered questions. Signal weights:

| Signal | Weight |
| --- | --- |
| mastery < 50 | 2 |
| mastery 50–65 | 1 |
| average score < 50 | 2 |
| average score 50–60 | 1 |
| last three attempts all < 50% | 2 |
| ≥ 2 recent attempts < 50% | 1 |
| trend < −10 points | 1 |
| repeated mistake concepts | 2 |

Total ≥ 5 → `high`, 3–4 → `medium`, 1–2 → `low`. `is_weak` = medium or high.
The first three signal sentences become `weakness_reason`, e.g.

> "Your mastery score is 42/100. Your average score on this topic is 43%.
> You have scored below 50% in your last 3 attempts on this topic."

## 3. Subject mastery

Confidence-weighted mean of assessed topics
(`Σ mastery·max(0.25, confidence) / Σ weights`), plus counts of topics started,
mastered (≥ 80) and weak. Monthly `mastery_snapshots` give the improvement
chart and are never deleted.

## 4. Learning profile — `services/learning_profile`

For each format f ∈ {text, visual, audio, practice}:

```
samples = resource events of that format (opened / completed)
for each sample: accuracy of quiz answers on the same topic within 7 days after
weight        = completion_weight(1.0 opened=0.6) · min(2, 0.5 + n_answers/4)
effectiveness = (0.5·2 + Σ accuracy·weight) / (2 + Σ weight)      # neutral prior
+0.02 per follow-up beyond 3 (max +0.1) when a format keeps producing results
```

The result is four values in 0–1 that move with behaviour — an adaptive
resource-effectiveness profile, not a fixed "learning style" label. The UI says
so explicitly.

## 5. Recommendation engine — `services/recommendations`

| Rule | Kind | Base priority |
| --- | --- | --- |
| Weak topic | `revise` | 0.75 / 0.9 (+ (100−mastery)/500) |
| Prerequisite below the dependent topic | `prerequisite` | 0.72 |
| Mastery 45–75 with ≥ 3 questions | `practice` | 0.6 + (75−mastery)/400 |
| Mastery ≥ 85 with ≥ 4 questions | `advance` | 0.40 |
| Idle ≥ 14 days, mastery < 85 | `revise` (refresh) | 0.55 + idle/100 |
| Opened but never assessed | `resume` | 0.50 |
| Best-performing format on the weakest topic | `format` | 0.65 |

Candidates are ranked by `RecommendationRanker` (swap-in point for a learned
ranker), de-duplicated per topic, and the top 8 are stored with their reason,
estimated minutes and an action URL. Completed/dismissed rows are kept.

## 6. RAG pipeline — `ai/rag.py`, `ai/tutor.py`

```
question
 → intent detection (explain | example | simplify | practice | revision | weakness | next)
 → embedding        (TF-IDF+SVD by default, MiniLM when installed)
 → vector search    (Chroma → in-memory fallback; keyword search if empty)
 → top-k syllabus passages (topics + resources, 530 documents when seeded)
 → student context  (mastery, weak topics, learning profile, recommendations)
 → Ollama           (system prompt forbids inventing performance data)
 → answer + sources → chat_messages + activity events → learning profile refresh
```

If Ollama is unavailable, `ai/offline.py` composes the answer from the same
retrieved content, the topic's key concepts and examples, the stored question
bank and the recommendation engine, and labels itself as offline mode.

## 7. ML service layer — `app/ml`

Interfaces: `WeaknessPredictor`, `MasteryPredictor`, `ResourceEffectivenessModel`,
`RecommendationRanker`. Rule-based implementations ship by default;
`SklearnWeaknessPredictor` loads `data/models/weakness_logreg.joblib` when it
exists. Train it once there is enough real data:

```bash
cd backend && python -m app.ml.train
```

It builds features (mastery, average score, trend, repeated mistakes, questions
answered, idle days) from `student_topic_mastery`, cross-validates a logistic
regression and saves the model. No LLM is trained anywhere in this project.

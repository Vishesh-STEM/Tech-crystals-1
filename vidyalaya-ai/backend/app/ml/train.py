"""Train the optional weak-topic classifier from real student data.

    python -m app.ml.train

Reads student_topic_mastery rows, builds a feature matrix and fits a logistic
regression that estimates "is this topic a genuine weakness?". The model is
saved to ``$ML_MODEL_DIR/weakness_logreg.joblib`` and picked up automatically
on the next start (see ``SklearnWeaknessPredictor``). If there is not enough
data the rule-based predictor simply stays in place.
"""
from __future__ import annotations

import os
from typing import List

from sqlalchemy import select

from app.db.base_class import utcnow
from app.db.session import SessionLocal
from app.ml.predictors import MODEL_DIR, SklearnWeaknessPredictor
from app.models import StudentTopicMastery

MIN_ROWS = 40


def build_dataset() -> tuple[List[List[float]], List[int]]:
    features: List[List[float]] = []
    labels: List[int] = []
    with SessionLocal() as db:
        for row in db.scalars(select(StudentTopicMastery)):
            if (row.questions_answered or 0) < 3:
                continue
            idle_days = (utcnow() - row.last_activity_at).days if row.last_activity_at else 30
            features.append(
                [
                    float(row.mastery or 0.0),
                    float(row.average_score or 0.0),
                    float(row.trend or 0.0),
                    float(len(row.repeated_mistake_concepts or [])),
                    float(row.questions_answered or 0),
                    float(idle_days),
                ]
            )
            labels.append(1 if row.is_weak else 0)
    return features, labels


def main() -> None:
    features, labels = build_dataset()
    print(f"rows={len(features)} positives={sum(labels)}")
    if len(features) < MIN_ROWS or len(set(labels)) < 2:
        print("Not enough labelled data yet - keeping the rule-based predictor.")
        return
    from sklearn.linear_model import LogisticRegression
    from sklearn.model_selection import cross_val_score
    from sklearn.pipeline import make_pipeline
    from sklearn.preprocessing import StandardScaler
    import joblib

    pipeline = make_pipeline(StandardScaler(), LogisticRegression(max_iter=1000))
    scores = cross_val_score(pipeline, features, labels, cv=min(5, sum(labels)), scoring="f1")
    pipeline.fit(features, labels)
    os.makedirs(MODEL_DIR, exist_ok=True)
    path = os.path.join(MODEL_DIR, "weakness_logreg.joblib")
    joblib.dump(pipeline, path)
    print(f"cv f1={scores.mean():.3f} saved -> {path}")
    print("features:", SklearnWeaknessPredictor.FEATURES)


if __name__ == "__main__":
    main()

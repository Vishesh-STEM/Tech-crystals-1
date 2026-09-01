"""ML service layer.

The MVP ships transparent rule-based implementations behind small interfaces.
A trained scikit-learn model (see ``app/ml/train.py``) can be dropped in later
without changing any caller: the API, recommendation engine and analytics all
talk to these interfaces only.
"""
from __future__ import annotations

import os
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

MODEL_DIR = os.environ.get("ML_MODEL_DIR", "./data/models")


class WeaknessPredictor(ABC):
    """Predict the probability that a topic is a genuine weakness (0..1)."""

    name = "abstract"

    @abstractmethod
    def predict(self, features: Dict[str, float]) -> float: ...


class MasteryPredictor(ABC):
    """Predict the mastery a student would show on the next assessment."""

    name = "abstract"

    @abstractmethod
    def predict(self, features: Dict[str, float]) -> float: ...


class ResourceEffectivenessModel(ABC):
    """Score how effective each resource format is for a student."""

    name = "abstract"

    @abstractmethod
    def score(self, profile: Dict[str, Any], topic_features: Dict[str, float]) -> Dict[str, float]: ...


class RecommendationRanker(ABC):
    name = "abstract"

    @abstractmethod
    def rank(self, candidates: List[Dict[str, Any]]) -> List[Dict[str, Any]]: ...


# --------------------------------------------------------------------------
# Rule-based (MVP) implementations
# --------------------------------------------------------------------------
class RuleBasedWeaknessPredictor(WeaknessPredictor):
    name = "rules-v1"

    def predict(self, features: Dict[str, float]) -> float:
        mastery = features.get("mastery", 50.0)
        average = features.get("average_score", mastery)
        trend = features.get("trend", 0.0)
        repeated = features.get("repeated_mistakes", 0.0)
        answered = features.get("questions_answered", 0.0)
        if answered < 3:
            return 0.0
        score = 0.0
        score += max(0.0, (65 - mastery) / 65) * 0.45
        score += max(0.0, (60 - average) / 60) * 0.3
        score += min(0.15, max(0.0, -trend) / 100)
        score += min(0.2, repeated * 0.08)
        return round(min(1.0, score), 3)


class RuleBasedMasteryPredictor(MasteryPredictor):
    name = "rules-v1"

    def predict(self, features: Dict[str, float]) -> float:
        mastery = features.get("mastery", 0.0)
        trend = features.get("trend", 0.0)
        idle_days = features.get("idle_days", 0.0)
        projected = mastery + 0.4 * trend - min(10.0, max(0.0, idle_days - 14) * 0.3)
        return round(max(0.0, min(100.0, projected)), 1)


class RuleBasedResourceEffectiveness(ResourceEffectivenessModel):
    name = "rules-v1"

    def score(self, profile: Dict[str, Any], topic_features: Dict[str, float]) -> Dict[str, float]:
        return {
            "text": profile.get("text_effectiveness", 0.5),
            "visual": profile.get("visual_effectiveness", 0.5),
            "audio": profile.get("audio_effectiveness", 0.5),
            "practice": profile.get("practice_effectiveness", 0.5),
        }


class PriorityRanker(RecommendationRanker):
    name = "priority-v1"

    def rank(self, candidates: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        return sorted(candidates, key=lambda c: float(c.get("priority", 0.0)), reverse=True)


# --------------------------------------------------------------------------
# Optional trained model (scikit-learn); falls back to rules automatically
# --------------------------------------------------------------------------
class SklearnWeaknessPredictor(WeaknessPredictor):
    name = "sklearn-logreg"
    FEATURES = ("mastery", "average_score", "trend", "repeated_mistakes", "questions_answered", "idle_days")

    def __init__(self, model: Any):
        self.model = model

    @classmethod
    def load(cls, path: Optional[str] = None) -> Optional["SklearnWeaknessPredictor"]:
        path = path or os.path.join(MODEL_DIR, "weakness_logreg.joblib")
        if not os.path.exists(path):
            return None
        try:  # pragma: no cover - optional dependency
            import joblib

            return cls(joblib.load(path))
        except Exception:
            return None

    def predict(self, features: Dict[str, float]) -> float:
        vector = [[float(features.get(name, 0.0)) for name in self.FEATURES]]
        try:
            return round(float(self.model.predict_proba(vector)[0][1]), 3)
        except Exception:  # pragma: no cover - defensive
            return RuleBasedWeaknessPredictor().predict(features)


_weakness: Optional[WeaknessPredictor] = None
_mastery: Optional[MasteryPredictor] = None
_effectiveness: Optional[ResourceEffectivenessModel] = None
_ranker: Optional[RecommendationRanker] = None


def get_weakness_predictor() -> WeaknessPredictor:
    global _weakness
    if _weakness is None:
        _weakness = SklearnWeaknessPredictor.load() or RuleBasedWeaknessPredictor()
    return _weakness


def get_mastery_predictor() -> MasteryPredictor:
    global _mastery
    if _mastery is None:
        _mastery = RuleBasedMasteryPredictor()
    return _mastery


def get_resource_effectiveness_model() -> ResourceEffectivenessModel:
    global _effectiveness
    if _effectiveness is None:
        _effectiveness = RuleBasedResourceEffectiveness()
    return _effectiveness


def get_recommendation_ranker() -> RecommendationRanker:
    global _ranker
    if _ranker is None:
        _ranker = PriorityRanker()
    return _ranker


def active_models() -> Dict[str, str]:
    return {
        "weakness": get_weakness_predictor().name,
        "mastery": get_mastery_predictor().name,
        "resource_effectiveness": get_resource_effectiveness_model().name,
        "ranker": get_recommendation_ranker().name,
    }

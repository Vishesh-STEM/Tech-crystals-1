"""Deterministic question generation for topics without a hand-written bank.

Auto-generated items are honest recall/association questions built from the
topic's own concept statements and summaries, and every one of them stores an
explanation. Teachers can replace them from the admin question bank.
"""
from __future__ import annotations

import random
from typing import Any, Dict, List

MAX_OPTION_LENGTH = 160


def _shorten(text: str) -> str:
    text = " ".join((text or "").split())
    if len(text) <= MAX_OPTION_LENGTH:
        return text
    return text[: MAX_OPTION_LENGTH - 3].rstrip() + "..."


def _label(options: List[str]) -> List[str]:
    return [f"{chr(65 + index)}. {option}" for index, option in enumerate(options)]


def generate_for_topic(
    topic: Dict[str, Any],
    chapter_name: str,
    subject_name: str,
    sibling_topic_names: List[str],
    foreign_concepts: List[str],
    seed: int,
) -> List[Dict[str, Any]]:
    rng = random.Random(seed)
    concepts = [c for c in (topic.get("concepts") or []) if c]
    summary = topic.get("summary") or ""
    name = topic["name"]
    questions: List[Dict[str, Any]] = []

    # 1) association: which idea belongs to this topic
    if concepts and len(foreign_concepts) >= 3:
        correct = _shorten(rng.choice(concepts))
        distractors = [_shorten(c) for c in rng.sample(foreign_concepts, 3)]
        options = distractors + [correct]
        rng.shuffle(options)
        labelled = _label(options)
        answer = labelled[options.index(correct)]
        questions.append(
            {
                "text": f"Which of the following is a key idea of {name} ({subject_name})?",
                "options": labelled,
                "answer": answer,
                "explanation": (
                    f"'{correct}' is one of the key concepts of {name} in the chapter "
                    f"{chapter_name}. The other options belong to different topics."
                ),
                "difficulty": "easy",
                "concept": name,
                "generated": True,
            }
        )

    # 2) identification: which topic covers this description
    if summary and len(sibling_topic_names) >= 3:
        distractors = rng.sample(sibling_topic_names, 3)
        options = distractors + [name]
        rng.shuffle(options)
        labelled = _label(options)
        answer = labelled[options.index(name)]
        questions.append(
            {
                "text": f"Which topic of {subject_name} deals with the following? \"{_shorten(summary)}\"",
                "options": labelled,
                "answer": answer,
                "explanation": f"This description matches {name} ({chapter_name}).",
                "difficulty": "medium",
                "concept": name,
                "generated": True,
            }
        )

    # 3) odd one out: which statement is NOT part of this topic
    if len(concepts) >= 3 and foreign_concepts:
        outsider = _shorten(rng.choice(foreign_concepts))
        insiders = [_shorten(c) for c in rng.sample(concepts, 3)]
        options = insiders + [outsider]
        rng.shuffle(options)
        labelled = _label(options)
        answer = labelled[options.index(outsider)]
        questions.append(
            {
                "text": f"Which of the following is NOT a part of {name}?",
                "options": labelled,
                "answer": answer,
                "explanation": (
                    f"The other three statements are key concepts of {name}; "
                    f"'{outsider}' belongs to a different topic."
                ),
                "difficulty": "hard",
                "concept": name,
                "generated": True,
            }
        )
    return questions

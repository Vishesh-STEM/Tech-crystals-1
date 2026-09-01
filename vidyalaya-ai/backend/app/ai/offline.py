"""Offline tutor: a real answer engine that needs no LLM at all.

Used when Ollama is not installed/reachable. It composes an answer from the
platform's own content (topic explanations, key concepts, examples, stored
question bank) plus the student's mastery data and the recommendation engine.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from app.ai.rag import practice_questions
from app.vector.base import SearchHit


def _bullets(items: List[str], limit: int = 5) -> str:
    return "\n".join(f"- {item}" for item in items[:limit] if item)


def compose_answer(
    db: Session,
    question: str,
    hits: List[SearchHit],
    student_context: Dict[str, Any],
    intent: str = "explain",
    topic: Optional[Any] = None,
) -> str:
    name = student_context.get("student_name", "there").split(" ")[0]
    if not hits and topic is None:
        return (
            f"I could not find anything in your Class 12 syllabus that matches "
            f"**{question.strip()}**.\n\n"
            "Try naming a chapter or topic - for example *\"Explain capacitors\"*, "
            "*\"Give me practice questions on Integration\"* or *\"What should I study today?\"*."
        )

    primary = hits[0].metadata if hits else {}
    subject = (primary.get("subject") or "") if primary else ""
    chapter = (primary.get("chapter") or "") if primary else ""
    topic_name = topic.name if topic is not None else (primary.get("topic") or "this topic")
    ncert_url = primary.get("ncert_url", "") if primary else ""

    summary = topic.summary if topic is not None else ""
    concepts = list(topic.key_concepts or []) if topic is not None else []
    examples = list(topic.examples or []) if topic is not None else []

    if not summary and hits:
        # fall back to the retrieved passage text
        summary = hits[0].text.split("\n", 1)[-1].strip()[:600]

    parts: List[str] = []
    header = f"### {topic_name}"
    if subject:
        header += f"\n*{subject}{' · ' + chapter if chapter else ''}*"
    parts.append(header)

    if intent == "practice":
        parts.append(f"Here are practice questions on **{topic_name}**, {name}:")
        questions = practice_questions(db, topic.id, limit=3) if topic is not None else []
        if questions:
            lines = []
            answers = []
            for index, item in enumerate(questions, start=1):
                lines.append(f"**Q{index}. ({item.difficulty})** {item.text}")
                if item.options:
                    lines.extend([f"   {option}" for option in item.options])
                answers.append(f"**Q{index}:** {item.correct_answer} - {item.explanation or ''}".strip())
            parts.append("\n".join(lines))
            parts.append("<details><summary>Show answers</summary>\n\n" + "\n\n".join(answers) + "\n\n</details>")
        else:
            parts.append(
                "I do not have stored questions for this topic yet - open the topic page and "
                "use the practice resource, or take the chapter quiz."
            )
    elif intent == "revision":
        parts.append(f"**Quick revision sheet**\n\n{summary}")
        if concepts:
            parts.append("**Must-remember points**\n" + _bullets(concepts, 6))
    elif intent == "simplify":
        first_sentence = summary.split(". ")[0] if summary else topic_name
        parts.append(f"In simple words: {first_sentence}.")
        if concepts:
            parts.append("Think of it in these pieces:\n" + _bullets(concepts, 4))
    else:
        if summary:
            parts.append(summary)
        if concepts:
            parts.append("**Key concepts**\n" + _bullets(concepts))
        if examples and intent in ("explain", "example"):
            parts.append("**Example**\n" + _bullets(examples, 2))

    # --- personalised, strictly data-backed note --------------------------
    topic_stats = student_context.get("topic_stats") or {}
    if topic_stats.get("questions_answered"):
        parts.append(
            f"**Your record here:** mastery {topic_stats['mastery']:.0f}/100 from "
            f"{topic_stats['attempts']} attempt(s), average {topic_stats.get('average_score') or 0:.0f}%. "
            + (topic_stats.get("weakness_reason") or "")
        )
    elif student_context.get("overall_mastery") is not None:
        parts.append(
            f"**Your record here:** you have not been assessed on {topic_name} yet - "
            "a short quiz will let me track your mastery."
        )

    next_steps = student_context.get("next_steps") or []
    if next_steps:
        parts.append("**What to do next**\n" + _bullets(next_steps, 3))

    if ncert_url:
        parts.append(f"NCERT reference: {ncert_url}")

    parts.append("_AI tutor is running in offline mode - answers are built from your syllabus content and your own performance data._")
    return "\n\n".join(part for part in parts if part)

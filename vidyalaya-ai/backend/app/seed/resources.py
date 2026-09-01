"""Representative study resources generated per topic.

Four formats are created for every topic so the platform can measure which
format works best for each student. No audio or video files are generated -
audio resources are revision scripts and visual resources are described
diagrams, exactly as the specification requires.
"""
from __future__ import annotations

from typing import Any, Dict, List


def build_resources(topic: Dict[str, Any], chapter_name: str, subject_name: str) -> List[Dict[str, Any]]:
    name = topic["name"]
    summary = topic.get("summary", "")
    concepts: List[str] = list(topic.get("concepts") or [])
    examples: List[str] = list(topic.get("examples") or [])
    ncert_url = topic.get("ncert_url", "")

    concept_lines = "\n".join(f"- {c}" for c in concepts)
    example_lines = "\n".join(f"- {e}" for e in examples) or "- Work through the NCERT in-text examples for this topic."

    text_body = (
        f"## {name}\n\n{summary}\n\n### Key concepts\n{concept_lines}\n\n"
        f"### Worked examples\n{example_lines}\n\n"
        f"### How this is asked in exams\nExpect one short-answer question on the definitions above and "
        f"one application question combining {name.lower()} with the rest of {chapter_name}."
    )

    visual_body = (
        f"## Visual walkthrough - {name}\n\n"
        f"Draw this on one page while you revise:\n\n"
        f"1. Centre box: **{name}**.\n"
        + "".join(
            f"{index + 2}. Branch {index + 1}: {concept}\n" for index, concept in enumerate(concepts[:4])
        )
        + f"\nConnect the branches with arrows showing cause -> effect, and mark the formula or key term on "
        f"each arrow. Colour the branch you find hardest in red and revisit it tomorrow.\n\n"
        f"Chapter map: {subject_name} > {chapter_name} > {name}."
    )

    audio_body = (
        f"## Audio revision script - {name}\n\n"
        f"(Read this aloud or record it in your own voice - 90 seconds.)\n\n"
        f"\"{summary}\"\n\n"
        + "".join(f"Point {index + 1}: {concept}.\n" for index, concept in enumerate(concepts[:4]))
        + "\nEnd by saying the one formula or definition you keep forgetting, three times."
    )

    practice_body = (
        f"## Practice set - {name}\n\n"
        f"1. State and explain: {concepts[0] if concepts else name}.\n"
        f"2. Give one example where {name.lower()} is applied, and one where it is not.\n"
        f"3. Solve the NCERT exercise questions for {chapter_name} that relate to this topic.\n"
        f"4. Write down the mistake you made most recently in this topic and correct it in full.\n"
        f"5. Attempt the topic quiz in Vidyalaya AI and target above 80 percent."
    )

    return [
        {
            "title": f"{name} - Concept Summary",
            "type": "text",
            "description": "Compact written explanation with key concepts and worked examples.",
            "body": text_body,
            "estimated_minutes": 12,
            "ncert_url": ncert_url,
        },
        {
            "title": f"{name} - Visual Walkthrough",
            "type": "visual",
            "description": "A diagram/mind-map you build yourself while revising.",
            "body": visual_body,
            "estimated_minutes": 10,
            "ncert_url": ncert_url,
        },
        {
            "title": f"{name} - Audio Revision Notes",
            "type": "audio",
            "description": "A 90 second revision script to read aloud or record.",
            "body": audio_body,
            "estimated_minutes": 6,
            "ncert_url": ncert_url,
        },
        {
            "title": f"{name} - Practice Set",
            "type": "practice",
            "description": "Five graded practice tasks including NCERT exercises.",
            "body": practice_body,
            "estimated_minutes": 20,
            "ncert_url": ncert_url,
        },
    ]

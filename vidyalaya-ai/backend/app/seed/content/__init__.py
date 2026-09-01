"""Editable Class 12 content packs.

Each module exports a SUBJECT dict:

    {"code", "name", "icon", "color", "description", "ncert_url",
     "chapters": [{"name", "number", "ncert_url", "description",
                   "topics": [{"name", "summary", "concepts", "examples",
                               "difficulty", "prerequisites", "questions"}]}]}

Add a new subject by creating a module here and appending it to SUBJECTS.
Run ``python -m app.seed.export_content`` to dump everything to JSON for
non-Python editing, and ``python -m app.seed.seed --reset`` to reload.
"""
from app.seed.content import biology, chemistry, computer_science, english, mathematics, physics

SUBJECTS = [
    mathematics.SUBJECT,
    english.SUBJECT,
    computer_science.SUBJECT,
    physics.SUBJECT,
    chemistry.SUBJECT,
    biology.SUBJECT,
]

__all__ = ["SUBJECTS"]

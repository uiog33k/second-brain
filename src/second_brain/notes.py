"""Business logic for note creation."""

from __future__ import annotations

import re
from datetime import date, datetime
from pathlib import Path


def slugify(title: str) -> str:
    """Convert a title string into a filename-safe slug."""
    slug = title.lower()
    slug = re.sub(r"[^a-z0-9\s-]", "", slug)
    slug = re.sub(r"[\s-]+", "-", slug)
    slug = slug.strip("-")
    return slug or "untitled"


def build_note_path(title: str, base_dir: Path, note_date: date) -> Path:
    """Build the full file path for a note, creating the directory if needed.

    If a file with the same name already exists, appends -1, -2, … to avoid
    overwriting.
    """
    base_dir.mkdir(parents=True, exist_ok=True)
    slug = slugify(title)
    stem = f"{note_date.isoformat()}-{slug}"
    candidate = base_dir / f"{stem}.md"
    counter = 1
    while candidate.exists():
        candidate = base_dir / f"{stem}-{counter}.md"
        counter += 1
    return candidate


def create_note(
    title: str,
    base_dir: Path,
    now: datetime | None = None,
) -> Path:
    """Create a markdown note file and return its absolute path."""
    now = now or datetime.now()
    path = build_note_path(title, base_dir, now.date())
    timestamp = now.replace(microsecond=0).isoformat()
    content = f"# {title}\n\n{timestamp}\n"
    path.write_text(content, encoding="utf-8")
    return path.resolve()

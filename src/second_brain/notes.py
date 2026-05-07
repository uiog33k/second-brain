"""Business logic for creating and managing notes."""

import os
import re
from datetime import date
from pathlib import Path


def slugify(title: str) -> str:
    """Convert a title string into a URL-safe slug.

    Args:
        title: The note title to slugify.

    Returns:
        Lowercase hyphen-separated alphanumeric string.
    """
    slug = title.lower()
    slug = re.sub(r"[^a-z0-9]+", "-", slug)
    return slug.strip("-")


def build_filename(title: str) -> str:
    """Build a date-prefixed markdown filename from a title.

    Args:
        title: The note title.

    Returns:
        Filename in the form ``YYYY-MM-DD-slug.md``.
    """
    return f"{date.today().isoformat()}-{slugify(title)}.md"


def create_note(title: str, directory: Path) -> Path:
    """Create a markdown note file in the given directory.

    The file contains a level-1 heading matching the title followed by a
    blank line.  The target directory is created if it does not exist.

    Args:
        title: The note title used for both the heading and filename.
        directory: The directory in which to write the file.

    Returns:
        The :class:`~pathlib.Path` of the created file.
    """
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    base = directory / build_filename(title)
    path = base
    counter = 2
    while path.exists():
        path = base.with_stem(f"{base.stem}-{counter}")
        counter += 1
    path.write_text(f"# {title}\n\n", encoding="utf-8")
    return path


def get_notes_dir() -> Path:
    """Resolve the notes storage directory.

    Reads ``SECOND_BRAIN_DIR`` from the environment; falls back to
    ``~/second_brain``.

    Returns:
        The resolved :class:`~pathlib.Path` for notes storage.
    """
    env = os.environ.get("SECOND_BRAIN_DIR")
    return Path(env) if env else Path.home() / "second_brain"

"""Business logic for note creation."""

from __future__ import annotations

import re
from datetime import date, datetime
from pathlib import Path
from typing import Literal

SortMode = Literal["mtime", "name"]


def slugify(title: str) -> str:
    """Convert a title string into a filename-safe slug."""
    slug = title.lower()
    slug = re.sub(r"[^a-z0-9\s-]", "", slug)
    slug = re.sub(r"[\s-]+", "-", slug)
    slug = slug.strip("-")
    return slug or "untitled"


_TAG_UNSAFE_RE = re.compile(r"""[\s,:\[\]{}"']+""")


def normalize_tag(tag: str) -> str:
    """Normalize a raw tag string into an Obsidian/YAML-safe tag value.

    Steps:
        1. Strip leading/trailing whitespace, then leading ``#``.
        2. Replace runs of whitespace or YAML-flow-unsafe characters
           (``, : [ ] { } " '``) with ``-``.
        3. Collapse runs of ``-`` and trim leading/trailing ``-``.
        4. Lower-case.

    Returns:
        Normalized tag, or empty string if nothing meaningful remains.
    """
    s = tag.strip().lstrip("#").strip()
    s = _TAG_UNSAFE_RE.sub("-", s)
    s = re.sub(r"-+", "-", s).strip("-")
    return s.lower()


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
    body: str | None = None,
    tags: list[str] | None = None,
) -> Path:
    """Create a markdown note file and return its absolute path.

    The note opens with an Obsidian-compatible YAML frontmatter block. A
    ``created:`` field is always emitted; a ``tags:`` field is included
    only when at least one non-empty tag survives normalization.

    Args:
        title: Note title used for the heading and slugged filename.
        base_dir: Directory where the note is written (created if missing).
        now: Optional fixed timestamp; defaults to ``datetime.now()``.
        body: Optional body text appended below the heading, separated by
            a blank line. Newlines are preserved verbatim. Empty/``None``
            leaves the stub note unchanged.
        tags: Optional list of raw tag strings. Each is passed through
            :func:`normalize_tag` (leading ``#`` stripped, whitespace and
            YAML-unsafe characters replaced with ``-``, lower-cased).
            ``None`` and ``[]`` are treated identically.

    Returns:
        Absolute path to the newly created note file.
    """
    now = now or datetime.now()
    path = build_note_path(title, base_dir, now.date())
    timestamp = now.replace(microsecond=0).isoformat()

    fm_lines = [f"created: {timestamp}"]
    if tags:
        clean = [t for t in (normalize_tag(t) for t in tags) if t]
        if clean:
            fm_lines.append(f"tags: [{', '.join(clean)}]")
    content = "---\n" + "\n".join(fm_lines) + "\n---\n\n# " + title + "\n"
    if body:
        content = f"{content}\n{body}\n"
    path.write_text(content, encoding="utf-8")
    return path.resolve()


_MODIFIED_LINE_RE = re.compile(r"^modified:.*$", re.MULTILINE)
_CREATION_TS_RE = re.compile(
    r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}[ \t]*$", re.MULTILINE
)
_FRONTMATTER_RE = re.compile(r"\A---\r?\n(.*?)\r?\n---\r?\n", re.DOTALL)


def update_note(path: Path, content: str, now: datetime | None = None) -> Path:
    """Rewrite ``path`` with ``content`` and stamp a ``modified:`` line.

    The filename is preserved. If ``content`` already contains a
    ``modified: <iso>`` line, its timestamp is replaced; otherwise a new
    line is inserted right after the first ISO creation-timestamp line
    found, or appended at the end if no such line exists.

    Args:
        path: Existing note file to overwrite.
        content: Full file contents to write back. Heading and creation
            timestamp are part of this string — the caller controls them.
        now: Optional fixed timestamp for the ``modified`` field; defaults
            to ``datetime.now()``.

    Returns:
        Absolute path to the updated note file.
    """
    now = now or datetime.now()
    iso = now.replace(microsecond=0).isoformat()
    modified_line = f"modified: {iso}"

    if _MODIFIED_LINE_RE.search(content):
        new_content = _MODIFIED_LINE_RE.sub(modified_line, content, count=1)
    else:
        fm = _FRONTMATTER_RE.match(content)
        if fm:
            inner_end = fm.end(1)
            new_content = (
                content[:inner_end] + "\n" + modified_line + content[inner_end:]
            )
        else:
            match = _CREATION_TS_RE.search(content)
            if match:
                insert_at = match.end()
                new_content = (
                    content[:insert_at] + "\n" + modified_line + content[insert_at:]
                )
            else:
                trimmed = content.rstrip("\n")
                new_content = f"{trimmed}\n\n{modified_line}\n"

    path.write_text(new_content, encoding="utf-8")
    return path.resolve()


def delete_note(path: Path) -> None:
    """Delete a note file.

    Args:
        path: Path to the note file to delete.

    Raises:
        FileNotFoundError: If ``path`` does not exist.
        OSError: If the file cannot be removed.
    """
    path.unlink()


def list_notes(base_dir: Path, sort: SortMode = "mtime") -> list[Path]:
    """Return markdown notes in ``base_dir`` ordered by ``sort``.

    Args:
        base_dir: Directory to scan for ``*.md`` files. Missing directory
            yields an empty list.
        sort: ``"mtime"`` orders newest-first by file modification time
            (with filename as a deterministic tiebreaker). ``"name"``
            orders ascending by filename.

    Returns:
        List of absolute paths to markdown notes, possibly empty.
    """
    if not base_dir.is_dir():
        return []
    files = list(base_dir.glob("*.md"))
    if sort == "mtime":
        files.sort(key=lambda p: (-p.stat().st_mtime, p.name))
    else:
        files.sort(key=lambda p: p.name)
    return files

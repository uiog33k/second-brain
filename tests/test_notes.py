import datetime
from pathlib import Path
from unittest.mock import patch

import pytest

from second_brain.notes import (
    build_filename,
    create_note,
    get_notes_dir,
    list_notes,
    slugify,
)

# --- slugify ---


def test_slugify_spaces_to_hyphens():
    assert slugify("My brilliant idea") == "my-brilliant-idea"


def test_slugify_lowercase():
    assert slugify("Hello World") == "hello-world"


def test_slugify_strips_non_alphanum():
    assert slugify("Hello, World!") == "hello-world"


def test_slugify_collapses_hyphens():
    assert slugify("hello---world") == "hello-world"


def test_slugify_leading_trailing_whitespace():
    assert slugify("  hello world  ") == "hello-world"


# --- build_filename ---


def test_build_filename_format():
    fixed = datetime.date(2026, 5, 7)
    with patch("second_brain.notes.date") as mock_date:
        mock_date.today.return_value = fixed
        result = build_filename("My brilliant idea about caching")
    assert result == "2026-05-07-my-brilliant-idea-about-caching.md"


# --- create_note ---


def test_create_note_returns_path(tmp_path):
    p = create_note("My Idea", tmp_path)
    assert isinstance(p, Path)


def test_create_note_file_exists(tmp_path):
    p = create_note("My Idea", tmp_path)
    assert p.exists()


def test_create_note_filename_convention(tmp_path):
    p = create_note("My Idea", tmp_path)
    assert p.name.endswith("-my-idea.md")


def test_create_note_content_heading(tmp_path):
    p = create_note("My Idea", tmp_path)
    lines = p.read_text().splitlines()
    assert lines[0] == "# My Idea"
    assert lines[1] == ""


def test_create_note_autocreates_directory(tmp_path):
    target = tmp_path / "nested" / "notes"
    create_note("Test", target)
    assert target.exists()


def test_create_note_no_overwrite_on_duplicate(tmp_path):
    p1 = create_note("My Idea", tmp_path)
    p2 = create_note("My Idea", tmp_path)
    assert p1 != p2
    assert p1.exists()
    assert p2.exists()


def test_create_note_duplicate_suffix(tmp_path):
    p1 = create_note("My Idea", tmp_path)
    p2 = create_note("My Idea", tmp_path)
    assert p2.name == p1.stem + "-2.md"


def test_create_note_triple_duplicate_suffix(tmp_path):
    create_note("My Idea", tmp_path)
    create_note("My Idea", tmp_path)
    p3 = create_note("My Idea", tmp_path)
    assert p3.name.endswith("-3.md")


def test_create_note_utf8_encoding(tmp_path):
    p = create_note("Ünïcödé títlé", tmp_path)
    assert p.read_text(encoding="utf-8").startswith("# Ünïcödé títlé")


def test_create_note_limit_raises_after_9(tmp_path):
    for _ in range(9):
        create_note("My Idea", tmp_path)
    with pytest.raises(FileExistsError, match="9"):
        create_note("My Idea", tmp_path)


# --- get_notes_dir ---


def test_get_notes_dir_env_override(monkeypatch, tmp_path):
    monkeypatch.setenv("SECOND_BRAIN_DIR", str(tmp_path))
    assert get_notes_dir() == tmp_path


def test_get_notes_dir_default(monkeypatch):
    monkeypatch.delenv("SECOND_BRAIN_DIR", raising=False)
    assert get_notes_dir() == Path.home() / "second_brain"


# --- list_notes ---


def test_list_notes_missing_directory(tmp_path):
    assert list_notes(tmp_path / "nonexistent") == []


def test_list_notes_empty_directory(tmp_path):
    assert list_notes(tmp_path) == []


def test_list_notes_returns_md_filenames(tmp_path):
    (tmp_path / "2026-05-01-alpha.md").write_text("")
    (tmp_path / "2026-05-07-beta.md").write_text("")
    assert list_notes(tmp_path) == ["2026-05-01-alpha.md", "2026-05-07-beta.md"]


def test_list_notes_ignores_non_md_files(tmp_path):
    (tmp_path / "note.md").write_text("")
    (tmp_path / "image.png").write_text("")
    (tmp_path / "data.txt").write_text("")
    assert list_notes(tmp_path) == ["note.md"]


def test_list_notes_sorted_alphabetically(tmp_path):
    (tmp_path / "2026-05-07-zebra.md").write_text("")
    (tmp_path / "2026-04-01-alpha.md").write_text("")
    (tmp_path / "2026-05-01-middle.md").write_text("")
    assert list_notes(tmp_path) == [
        "2026-04-01-alpha.md",
        "2026-05-01-middle.md",
        "2026-05-07-zebra.md",
    ]

"""Tests for the notes module (slugify, build_note_path, create_note)."""

from datetime import date, datetime

import pytest

from second_brain.notes import build_note_path, create_note, list_notes, slugify

# ---------------------------------------------------------------------------
# slugify
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("title", "expected"),
    [
        ("My brilliant idea about caching", "my-brilliant-idea-about-caching"),
        ("Hello, World! @#$%", "hello-world"),
        ("too---many  spaces", "too-many-spaces"),
        ("--leading and trailing--", "leading-and-trailing"),
        ("", "untitled"),
        ("@#$%^&", "untitled"),
        ("cafe latte", "cafe-latte"),
        ("idea 42 is great", "idea-42-is-great"),
    ],
    ids=[
        "basic",
        "special_chars",
        "collapsed_hyphens",
        "leading_trailing",
        "empty",
        "only_special",
        "unicode_ascii",
        "numbers_preserved",
    ],
)
def test_slugify(title, expected):
    assert slugify(title) == expected


# ---------------------------------------------------------------------------
# build_note_path
# ---------------------------------------------------------------------------


def test_build_note_path_basic(tmp_path):
    result = build_note_path("My idea", tmp_path, date(2026, 3, 22))
    assert result == tmp_path / "2026-03-22-my-idea.md"


def test_build_note_path_creates_dir(tmp_path):
    nested = tmp_path / "sub" / "dir"
    result = build_note_path("Test", nested, date(2026, 1, 1))
    assert nested.is_dir()
    assert result == nested / "2026-01-01-test.md"


# ---------------------------------------------------------------------------
# create_note
# ---------------------------------------------------------------------------

FIXED_NOW = datetime(2026, 3, 22, 14, 30, 0)


def test_create_note_file_exists(tmp_path):
    path = create_note("Test idea", tmp_path, now=FIXED_NOW)
    assert path.is_file()


def test_create_note_content_heading(tmp_path):
    path = create_note("Test idea", tmp_path, now=FIXED_NOW)
    lines = path.read_text().splitlines()
    assert lines[0] == "# Test idea"


def test_create_note_content_timestamp(tmp_path):
    path = create_note("Test idea", tmp_path, now=FIXED_NOW)
    text = path.read_text()
    assert "2026-03-22T14:30:00" in text


def test_create_note_no_yaml_frontmatter(tmp_path):
    path = create_note("Test idea", tmp_path, now=FIXED_NOW)
    text = path.read_text()
    assert not text.startswith("---")


def test_create_note_returns_absolute_path(tmp_path):
    path = create_note("Test idea", tmp_path, now=FIXED_NOW)
    assert path.is_absolute()


def test_create_note_creates_directory(tmp_path):
    nested = tmp_path / "deep" / "dir"
    path = create_note("Test idea", nested, now=FIXED_NOW)
    assert nested.is_dir()
    assert path.is_file()


# ---------------------------------------------------------------------------
# duplicate-title handling
# ---------------------------------------------------------------------------


def test_build_note_path_appends_suffix_when_file_exists(tmp_path):
    original = build_note_path("idea", tmp_path, date(2026, 3, 22))
    original.write_text("first")
    second = build_note_path("idea", tmp_path, date(2026, 3, 22))
    assert second == tmp_path / "2026-03-22-idea-1.md"


def test_create_note_no_overwrite(tmp_path):
    path1 = create_note("My idea", tmp_path, now=FIXED_NOW)
    path2 = create_note("My idea", tmp_path, now=FIXED_NOW)
    assert path1 != path2
    assert path1.is_file()
    assert path2.is_file()
    assert path2.name.endswith("-1.md")


def test_create_note_multiple_duplicates(tmp_path):
    path1 = create_note("Dup", tmp_path, now=FIXED_NOW)
    path2 = create_note("Dup", tmp_path, now=FIXED_NOW)
    path3 = create_note("Dup", tmp_path, now=FIXED_NOW)
    assert len({path1, path2, path3}) == 3
    assert path1.is_file() and path2.is_file() and path3.is_file()
    assert path2.name.endswith("-1.md")
    assert path3.name.endswith("-2.md")


# ---------------------------------------------------------------------------
# body content
# ---------------------------------------------------------------------------


def test_create_note_with_body_appends_after_header(tmp_path):
    path = create_note("Test idea", tmp_path, now=FIXED_NOW, body="hello world")
    text = path.read_text(encoding="utf-8")
    assert text == "# Test idea\n\n2026-03-22T14:30:00\n\nhello world\n"


def test_create_note_body_preserves_newlines(tmp_path):
    body = "line one\nline two\n\nparagraph two"
    path = create_note("Multi", tmp_path, now=FIXED_NOW, body=body)
    text = path.read_text(encoding="utf-8")
    assert text.endswith("\nline one\nline two\n\nparagraph two\n")


def test_create_note_body_none_leaves_stub(tmp_path):
    path = create_note("Stub", tmp_path, now=FIXED_NOW, body=None)
    text = path.read_text(encoding="utf-8")
    assert text == "# Stub\n\n2026-03-22T14:30:00\n"


def test_create_note_body_empty_string_leaves_stub(tmp_path):
    path = create_note("Stub", tmp_path, now=FIXED_NOW, body="")
    text = path.read_text(encoding="utf-8")
    assert text == "# Stub\n\n2026-03-22T14:30:00\n"


# ---------------------------------------------------------------------------
# list_notes
# ---------------------------------------------------------------------------


def test_list_notes_missing_dir_returns_empty(tmp_path):
    assert list_notes(tmp_path / "nope") == []


def test_list_notes_empty_dir(tmp_path):
    assert list_notes(tmp_path) == []


def test_list_notes_ignores_non_md(tmp_path):
    (tmp_path / "a.md").write_text("# a\n")
    (tmp_path / "b.txt").write_text("nope")
    result = list_notes(tmp_path)
    assert [p.name for p in result] == ["a.md"]


def test_list_notes_alpha_sort(tmp_path):
    (tmp_path / "2026-03-22-c.md").write_text("# c\n")
    (tmp_path / "2026-03-20-a.md").write_text("# a\n")
    (tmp_path / "2026-03-21-b.md").write_text("# b\n")
    result = list_notes(tmp_path, sort="name")
    assert [p.name for p in result] == [
        "2026-03-20-a.md",
        "2026-03-21-b.md",
        "2026-03-22-c.md",
    ]


def test_list_notes_mtime_sort_newest_first(tmp_path):
    import os
    import time

    old = tmp_path / "old.md"
    new = tmp_path / "new.md"
    old.write_text("# old\n")
    time.sleep(0.01)
    new.write_text("# new\n")
    # Ensure mtimes are distinct even on coarse-grained filesystems.
    os.utime(old, (old.stat().st_atime, old.stat().st_mtime - 5))
    result = list_notes(tmp_path, sort="mtime")
    assert [p.name for p in result] == ["new.md", "old.md"]

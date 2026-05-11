"""Tests for the notes module (slugify, build_note_path, create_note)."""

from datetime import date, datetime

import pytest

from second_brain.notes import (
    build_note_path,
    create_note,
    delete_note,
    list_notes,
    normalize_tag,
    slugify,
    update_note,
)

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
# normalize_tag
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("work", "work"),
        ("#work", "work"),
        ("  #work  ", "work"),
        ("MyTag", "mytag"),
        ("my project", "my-project"),
        ("work,planning", "work-planning"),
        ("a:b", "a-b"),
        ("#", ""),
        ("   ", ""),
        ("--leading--", "leading"),
        # additional YAML-indicator characters
        ("foo#bar", "foo-bar"),
        ("foo&bar", "foo-bar"),
        ("foo*bar", "foo-bar"),
        ("foo!bar", "foo-bar"),
        ("foo|bar", "foo-bar"),
        ("foo>bar", "foo-bar"),
        ("foo%bar", "foo-bar"),
        ("foo@bar", "foo-bar"),
        ("foo`bar", "foo-bar"),
    ],
)
def test_normalize_tag(raw, expected):
    assert normalize_tag(raw) == expected


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
    text = path.read_text()
    assert "\n# Test idea\n" in text


def test_create_note_content_timestamp(tmp_path):
    path = create_note("Test idea", tmp_path, now=FIXED_NOW)
    text = path.read_text()
    assert "2026-03-22T14:30:00" in text


def test_create_note_emits_yaml_frontmatter(tmp_path):
    path = create_note("Test idea", tmp_path, now=FIXED_NOW)
    text = path.read_text()
    assert text.startswith("---\n")


def test_create_note_frontmatter_contains_created(tmp_path):
    path = create_note("Test idea", tmp_path, now=FIXED_NOW)
    text = path.read_text()
    fm_end = text.index("\n---\n", 4)
    block = text[:fm_end]
    assert "created: 2026-03-22T14:30:00" in block


def test_create_note_no_tags_omits_tags_key(tmp_path):
    path = create_note("Test idea", tmp_path, now=FIXED_NOW)
    text = path.read_text()
    fm_end = text.index("\n---\n", 4)
    block = text[:fm_end]
    assert "tags:" not in block


def test_create_note_single_tag(tmp_path):
    path = create_note("T", tmp_path, now=FIXED_NOW, tags=["work"])
    text = path.read_text()
    assert "tags:\n  - work\n" in text


def test_create_note_multiple_tags_preserve_order(tmp_path):
    path = create_note("T", tmp_path, now=FIXED_NOW, tags=["work", "planning"])
    text = path.read_text()
    assert "tags:\n  - work\n  - planning\n" in text


def test_create_note_tags_normalized(tmp_path):
    path = create_note("T", tmp_path, now=FIXED_NOW, tags=["#Work", "my project"])
    text = path.read_text()
    assert "tags:\n  - work\n  - my-project\n" in text


def test_create_note_all_empty_tags_dropped(tmp_path):
    path = create_note("T", tmp_path, now=FIXED_NOW, tags=["#", "   "])
    text = path.read_text()
    assert "tags:" not in text


def test_create_note_dedupes_tags_preserve_first_occurrence(tmp_path):
    path = create_note(
        "T", tmp_path, now=FIXED_NOW, tags=["work", "Work", "planning", "work"]
    )
    text = path.read_text()
    assert "tags:\n  - work\n  - planning\n" in text
    assert text.count("- work") == 1


def test_create_note_heading_follows_frontmatter(tmp_path):
    path = create_note("Project kickoff", tmp_path, now=FIXED_NOW)
    text = path.read_text()
    assert "\n---\n\n# Project kickoff\n" in text


def test_create_note_body_appended_after_heading(tmp_path):
    path = create_note("Title", tmp_path, now=FIXED_NOW, body="paragraph")
    text = path.read_text()
    assert "\n# Title\n\nparagraph\n" in text


def test_create_note_stub_exact_shape(tmp_path):
    path = create_note("Stub", tmp_path, now=FIXED_NOW)
    text = path.read_text(encoding="utf-8")
    assert text == "---\ncreated: 2026-03-22T14:30:00\n---\n\n# Stub\n"


def test_create_note_with_tags_exact_shape(tmp_path):
    path = create_note("T", tmp_path, now=FIXED_NOW, tags=["work", "planning"])
    text = path.read_text(encoding="utf-8")
    assert text == (
        "---\n"
        "created: 2026-03-22T14:30:00\n"
        "tags:\n"
        "  - work\n"
        "  - planning\n"
        "---\n"
        "\n"
        "# T\n"
    )


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
    assert (
        text
        == "---\ncreated: 2026-03-22T14:30:00\n---\n\n# Test idea\n\nhello world\n"
    )


def test_create_note_body_preserves_newlines(tmp_path):
    body = "line one\nline two\n\nparagraph two"
    path = create_note("Multi", tmp_path, now=FIXED_NOW, body=body)
    text = path.read_text(encoding="utf-8")
    assert text.endswith("\nline one\nline two\n\nparagraph two\n")


def test_create_note_body_none_leaves_stub(tmp_path):
    path = create_note("Stub", tmp_path, now=FIXED_NOW, body=None)
    text = path.read_text(encoding="utf-8")
    assert text == "---\ncreated: 2026-03-22T14:30:00\n---\n\n# Stub\n"


def test_create_note_body_empty_string_leaves_stub(tmp_path):
    path = create_note("Stub", tmp_path, now=FIXED_NOW, body="")
    text = path.read_text(encoding="utf-8")
    assert text == "---\ncreated: 2026-03-22T14:30:00\n---\n\n# Stub\n"


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


# ---------------------------------------------------------------------------
# update_note
# ---------------------------------------------------------------------------


EDIT_NOW = datetime(2026, 5, 10, 9, 15, 0)


def test_update_note_returns_same_path(tmp_path):
    """The filename must not change on update."""
    original = create_note("Test idea", tmp_path, now=FIXED_NOW)
    new_content = original.read_text(encoding="utf-8") + "\nadded line\n"
    result = update_note(original, new_content, now=EDIT_NOW)
    assert result == original.resolve()


def test_update_note_preserves_creation_timestamp(tmp_path):
    """The original ISO timestamp must remain in the file after update."""
    original = create_note("Test idea", tmp_path, now=FIXED_NOW)
    content = original.read_text(encoding="utf-8")
    update_note(original, content, now=EDIT_NOW)
    text = original.read_text(encoding="utf-8")
    assert "2026-03-22T14:30:00" in text


def test_update_note_inserts_modified_line_when_absent(tmp_path):
    """First save adds a 'modified: <iso>' line right after the creation timestamp."""
    original = create_note("Test idea", tmp_path, now=FIXED_NOW)
    content = original.read_text(encoding="utf-8")
    update_note(original, content, now=EDIT_NOW)
    text = original.read_text(encoding="utf-8")
    assert "modified: 2026-05-10T09:15:00" in text
    # creation timestamp line precedes the modified line
    creation_idx = text.index("2026-03-22T14:30:00")
    modified_idx = text.index("modified: 2026-05-10T09:15:00")
    assert creation_idx < modified_idx


def test_update_note_replaces_existing_modified_line(tmp_path):
    """Subsequent saves replace the existing 'modified: …' line (not duplicate)."""
    original = create_note("Test idea", tmp_path, now=FIXED_NOW)
    content = original.read_text(encoding="utf-8")
    update_note(original, content, now=EDIT_NOW)
    later = datetime(2026, 5, 11, 10, 0, 0)
    update_note(original, original.read_text(encoding="utf-8"), now=later)
    text = original.read_text(encoding="utf-8")
    assert text.count("modified:") == 1
    assert "modified: 2026-05-11T10:00:00" in text
    assert "modified: 2026-05-10T09:15:00" not in text


def test_update_note_writes_supplied_body(tmp_path):
    """Edits to the body must be reflected in the file."""
    original = create_note("Test idea", tmp_path, now=FIXED_NOW, body="old body")
    new = "# Test idea\n\n2026-03-22T14:30:00\n\nbrand new body line\n"
    update_note(original, new, now=EDIT_NOW)
    text = original.read_text(encoding="utf-8")
    assert "brand new body line" in text
    assert "old body" not in text


def test_update_note_writes_edited_title(tmp_path):
    """Editing the heading inside the body editor is persisted."""
    original = create_note("Old title", tmp_path, now=FIXED_NOW)
    new = "# New title\n\n2026-03-22T14:30:00\n"
    update_note(original, new, now=EDIT_NOW)
    text = original.read_text(encoding="utf-8")
    assert "# New title" in text
    assert "# Old title" not in text


def test_update_note_returns_absolute_path(tmp_path):
    original = create_note("Test", tmp_path, now=FIXED_NOW)
    result = update_note(original, original.read_text(encoding="utf-8"), now=EDIT_NOW)
    assert result.is_absolute()


def test_update_note_round_trip(tmp_path):
    """Read → update with same content → read is a stable round trip apart from modified line."""
    original = create_note("Stable", tmp_path, now=FIXED_NOW)
    before = original.read_text(encoding="utf-8")
    update_note(original, before, now=EDIT_NOW)
    after = original.read_text(encoding="utf-8")
    # everything from the original is still there
    for line in before.splitlines():
        assert line in after


def test_update_note_appends_modified_when_no_timestamp_line(tmp_path):
    """If the body has no recognizable creation-timestamp line, append the modified line."""
    p = tmp_path / "freeform.md"
    p.write_text("# Freeform\n\nno timestamp here\n", encoding="utf-8")
    update_note(p, p.read_text(encoding="utf-8"), now=EDIT_NOW)
    text = p.read_text(encoding="utf-8")
    assert "modified: 2026-05-10T09:15:00" in text
    assert "no timestamp here" in text


def test_update_note_preserves_trailing_newline(tmp_path):
    """Updated file must still end with a newline (POSIX text-file convention)."""
    original = create_note("Stub", tmp_path, now=FIXED_NOW)
    update_note(original, original.read_text(encoding="utf-8"), now=EDIT_NOW)
    text = original.read_text(encoding="utf-8")
    assert text.endswith("\n")


def test_update_note_preserves_blank_line_before_body(tmp_path):
    """The blank line between the header block and the body must remain intact."""
    original = create_note("Test", tmp_path, now=FIXED_NOW, body="paragraph one")
    update_note(original, original.read_text(encoding="utf-8"), now=EDIT_NOW)
    text = original.read_text(encoding="utf-8")
    # body line is preceded by a blank line, not glued to the modified line
    assert "\n\nparagraph one\n" in text


def test_update_note_modified_inserted_inside_frontmatter(tmp_path):
    original = create_note("Fm", tmp_path, now=FIXED_NOW)
    update_note(original, original.read_text(encoding="utf-8"), now=EDIT_NOW)
    text = original.read_text(encoding="utf-8")
    fm_end = text.index("\n---\n", 4)
    block = text[: fm_end + len("\n---\n")]
    assert "created: 2026-03-22T14:30:00" in block
    assert "modified: 2026-05-10T09:15:00" in block


def test_update_note_preserves_created_field(tmp_path):
    original = create_note("Fm", tmp_path, now=FIXED_NOW)
    update_note(original, original.read_text(encoding="utf-8"), now=EDIT_NOW)
    text = original.read_text(encoding="utf-8")
    assert "created: 2026-03-22T14:30:00" in text


def test_update_note_replaces_modified_inside_frontmatter(tmp_path):
    original = create_note("Fm", tmp_path, now=FIXED_NOW)
    update_note(original, original.read_text(encoding="utf-8"), now=EDIT_NOW)
    later = datetime(2026, 5, 11, 10, 0, 0)
    update_note(original, original.read_text(encoding="utf-8"), now=later)
    text = original.read_text(encoding="utf-8")
    assert text.count("modified:") == 1
    assert "modified: 2026-05-11T10:00:00" in text


def test_update_note_preserves_tags_across_update(tmp_path):
    original = create_note(
        "Fm", tmp_path, now=FIXED_NOW, tags=["work", "planning"]
    )
    update_note(original, original.read_text(encoding="utf-8"), now=EDIT_NOW)
    text = original.read_text(encoding="utf-8")
    assert "tags:\n  - work\n  - planning\n" in text


def test_update_note_legacy_file_no_frontmatter_unchanged_shape(tmp_path):
    p = tmp_path / "legacy.md"
    p.write_text(
        "# Legacy\n\n2026-01-01T00:00:00\n\nbody\n", encoding="utf-8"
    )
    update_note(p, p.read_text(encoding="utf-8"), now=EDIT_NOW)
    text = p.read_text(encoding="utf-8")
    assert not text.startswith("---")
    assert "modified: 2026-05-10T09:15:00" in text


def test_update_note_replaces_modified_line_with_multi_token_value(tmp_path):
    """A pre-existing modified line with extra tokens must still be replaced (not duplicated)."""
    p = tmp_path / "freeform.md"
    p.write_text(
        "# Manual\n\n2026-01-01T00:00:00\nmodified: 2026-01-02T00:00:00 (manual edit)\n\nbody\n",
        encoding="utf-8",
    )
    update_note(p, p.read_text(encoding="utf-8"), now=EDIT_NOW)
    text = p.read_text(encoding="utf-8")
    assert text.count("modified:") == 1
    assert "modified: 2026-05-10T09:15:00" in text
    assert "(manual edit)" not in text


# ---------------------------------------------------------------------------
# delete_note
# ---------------------------------------------------------------------------


def test_delete_note_removes_file(tmp_path):
    path = create_note("Doomed", tmp_path, now=FIXED_NOW)
    assert path.exists()
    delete_note(path)
    assert not path.exists()


def test_delete_note_missing_path_raises(tmp_path):
    missing = tmp_path / "nope.md"
    with pytest.raises(FileNotFoundError):
        delete_note(missing)


def test_delete_note_does_not_touch_siblings(tmp_path):
    keep = create_note("Keep", tmp_path, now=FIXED_NOW)
    remove = create_note("Remove", tmp_path, now=FIXED_NOW)
    delete_note(remove)
    assert keep.exists()
    assert not remove.exists()


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

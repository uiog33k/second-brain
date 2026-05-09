"""Tests for the Textual TUI (`second_brain.tui`)."""

from __future__ import annotations

import os
import time
from pathlib import Path

import pytest
from textual.widgets import Input, ListView, MarkdownViewer, TextArea

from second_brain.tui import NoteListItem, SecondBrainApp

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _write_note(dir_: Path, name: str, body: str = "") -> Path:
    dir_.mkdir(parents=True, exist_ok=True)
    p = dir_ / name
    p.write_text(body or f"# {name}\n", encoding="utf-8")
    return p


# ---------------------------------------------------------------------------
# Mount / list
# ---------------------------------------------------------------------------


async def test_tui_mounts_with_empty_dir(tmp_path):
    app = SecondBrainApp(base_dir=tmp_path / "missing")
    async with app.run_test() as pilot:
        await pilot.pause()
        list_view = app.query_one("#notes-list", ListView)
        assert len(list_view) == 0


async def test_tui_lists_notes_on_mount(tmp_path):
    _write_note(tmp_path, "2026-03-22-a.md", "# A\nbody-a\n")
    _write_note(tmp_path, "2026-03-21-b.md", "# B\nbody-b\n")

    app = SecondBrainApp(base_dir=tmp_path)
    async with app.run_test() as pilot:
        await pilot.pause()
        list_view = app.query_one("#notes-list", ListView)
        assert len(list_view) == 2
        names = {
            child.path.name
            for child in list_view.children
            if isinstance(child, NoteListItem)
        }
        assert names == {"2026-03-22-a.md", "2026-03-21-b.md"}


async def test_tui_initial_selection_loads_into_raw_view(tmp_path):
    _write_note(tmp_path, "2026-03-22-a.md", "# A\nbody-a\n")

    app = SecondBrainApp(base_dir=tmp_path)
    async with app.run_test() as pilot:
        await pilot.pause()
        raw = app.query_one("#raw-view", TextArea)
        assert "body-a" in raw.text


async def test_tui_initial_selection_loads_into_markdown_view(tmp_path):
    """Rendered pane must actually receive the note body, not just the raw view."""
    _write_note(tmp_path, "2026-03-22-a.md", "# A\nbody-a\n")

    app = SecondBrainApp(base_dir=tmp_path)
    async with app.run_test() as pilot:
        await pilot.pause()
        md = app.query_one("#markdown-view", MarkdownViewer)
        assert "body-a" in md.document.source


# ---------------------------------------------------------------------------
# Sort toggle
# ---------------------------------------------------------------------------


async def test_tui_sort_toggle_switches_to_alpha(tmp_path):
    # mtime newest-first should put zzz first; alpha should put aaa first.
    aaa = _write_note(tmp_path, "aaa.md", "# aaa\n")
    time.sleep(0.01)
    zzz = _write_note(tmp_path, "zzz.md", "# zzz\n")
    # Make zzz newer than aaa for deterministic mtime ordering.
    os.utime(aaa, (aaa.stat().st_atime, zzz.stat().st_mtime - 5))

    app = SecondBrainApp(base_dir=tmp_path)
    async with app.run_test() as pilot:
        await pilot.pause()
        list_view = app.query_one("#notes-list", ListView)
        first = list_view.children[0]
        assert isinstance(first, NoteListItem)
        assert first.path.name == "zzz.md"

        await pilot.press("s")
        await pilot.pause()
        list_view = app.query_one("#notes-list", ListView)
        first = list_view.children[0]
        assert isinstance(first, NoteListItem)
        assert first.path.name == "aaa.md"


# ---------------------------------------------------------------------------
# Render toggle
# ---------------------------------------------------------------------------


async def test_tui_render_toggle_hides_markdown_and_shows_raw(tmp_path):
    _write_note(tmp_path, "2026-03-22-a.md", "# A\n")

    app = SecondBrainApp(base_dir=tmp_path)
    async with app.run_test() as pilot:
        await pilot.pause()
        md = app.query_one("#markdown-view", MarkdownViewer)
        raw = app.query_one("#raw-view", TextArea)
        assert not md.has_class("hidden")
        assert raw.has_class("hidden")

        await pilot.press("r")
        await pilot.pause()
        assert md.has_class("hidden")
        assert not raw.has_class("hidden")

        await pilot.press("r")
        await pilot.pause()
        assert not md.has_class("hidden")
        assert raw.has_class("hidden")


# ---------------------------------------------------------------------------
# Create flow
# ---------------------------------------------------------------------------


async def test_tui_create_and_save_round_trip(tmp_path):
    app = SecondBrainApp(base_dir=tmp_path)
    async with app.run_test() as pilot:
        await pilot.pause()
        await pilot.press("n")
        await pilot.pause()

        title_input = app.query_one("#title-input", Input)
        body_editor = app.query_one("#body-editor", TextArea)
        edit_form = app.query_one("#edit-form")
        assert not edit_form.has_class("hidden")

        title_input.value = "My new note"
        body_editor.text = "this is the body"

        await pilot.click("#save-btn")
        await pilot.pause()

        files = sorted(tmp_path.glob("*.md"))
        assert len(files) == 1
        text = files[0].read_text(encoding="utf-8")
        assert text.startswith("# My new note")
        assert "this is the body" in text

        # edit form hidden, list shows the new note and selects it
        assert app.query_one("#edit-form").has_class("hidden")
        list_view = app.query_one("#notes-list", ListView)
        assert len(list_view) == 1
        first = list_view.children[0]
        assert isinstance(first, NoteListItem)
        assert first.path == files[0]


async def test_tui_cancel_does_not_create_file(tmp_path):
    app = SecondBrainApp(base_dir=tmp_path)
    async with app.run_test() as pilot:
        await pilot.pause()
        await pilot.press("n")
        await pilot.pause()
        app.query_one("#title-input", Input).value = "Discarded"
        app.query_one("#body-editor", TextArea).text = "should not be saved"

        await pilot.click("#cancel-btn")
        await pilot.pause()

        assert list(tmp_path.glob("*.md")) == []
        assert app.query_one("#edit-form").has_class("hidden")


async def test_tui_save_with_empty_title_warns_and_skips(tmp_path):
    app = SecondBrainApp(base_dir=tmp_path)
    async with app.run_test() as pilot:
        await pilot.pause()
        await pilot.press("n")
        await pilot.pause()
        app.query_one("#title-input", Input).value = "   "
        app.query_one("#body-editor", TextArea).text = "body without title"

        await pilot.click("#save-btn")
        await pilot.pause()

        assert list(tmp_path.glob("*.md")) == []
        # still in edit mode
        assert not app.query_one("#edit-form").has_class("hidden")


async def test_tui_save_handles_oserror_and_keeps_form(tmp_path, monkeypatch):
    """If create_note raises OSError, the form should stay open and the user keeps their draft."""
    app = SecondBrainApp(base_dir=tmp_path)
    async with app.run_test() as pilot:
        await pilot.pause()
        await pilot.press("n")
        await pilot.pause()
        app.query_one("#title-input", Input).value = "My note"
        app.query_one("#body-editor", TextArea).text = "important draft"

        def boom(*args, **kwargs):
            raise PermissionError("disk full")

        monkeypatch.setattr("second_brain.tui.create_note", boom)

        await pilot.click("#save-btn")
        await pilot.pause()

        assert list(tmp_path.glob("*.md")) == []
        # form is still visible so the draft is preserved
        assert not app.query_one("#edit-form").has_class("hidden")
        assert app.query_one("#title-input", Input).value == "My note"
        assert app.query_one("#body-editor", TextArea).text == "important draft"


async def test_tui_create_button_enters_edit_mode(tmp_path):
    app = SecondBrainApp(base_dir=tmp_path)
    async with app.run_test() as pilot:
        await pilot.pause()
        await pilot.click("#create-btn")
        await pilot.pause()
        assert not app.query_one("#edit-form").has_class("hidden")


# ---------------------------------------------------------------------------
# Sort/render toggles disabled while editing
# ---------------------------------------------------------------------------


async def test_tui_sort_toggle_ignored_while_editing(tmp_path):
    _write_note(tmp_path, "a.md", "# a\n")
    app = SecondBrainApp(base_dir=tmp_path)
    async with app.run_test() as pilot:
        await pilot.pause()
        await pilot.press("n")
        await pilot.pause()
        before = app.sort_mode
        # 's' should be swallowed by the Input, but action_toggle_sort is also
        # guarded — invoke it directly to verify the guard.
        await app.action_toggle_sort()
        assert app.sort_mode == before


# ---------------------------------------------------------------------------
# Resolves SECOND_BRAIN_DIR when base_dir is None
# ---------------------------------------------------------------------------


async def test_tui_resolves_base_dir_from_env(tmp_path, monkeypatch):
    monkeypatch.setenv("SECOND_BRAIN_DIR", str(tmp_path))
    _write_note(tmp_path, "from-env.md", "# from-env\n")
    app = SecondBrainApp()  # base_dir=None
    async with app.run_test() as pilot:
        await pilot.pause()
        list_view = app.query_one("#notes-list", ListView)
        assert len(list_view) == 1


# ---------------------------------------------------------------------------
# CLI integration
# ---------------------------------------------------------------------------


def test_cli_invokes_tui_when_no_subcommand(tmp_note_dir, monkeypatch):
    """`second_brain` with no args should launch the TUI."""
    from click.testing import CliRunner

    from second_brain import cli as cli_module

    captured: dict = {}

    def fake_run_tui(base_dir=None):
        captured["base_dir"] = base_dir

    monkeypatch.setattr("second_brain.tui.run_tui", fake_run_tui)
    runner = CliRunner()
    result = runner.invoke(cli_module.cli, [])
    assert result.exit_code == 0
    assert captured["base_dir"] == tmp_note_dir


@pytest.mark.parametrize("subcommand", ["new", "list", "show"])
def test_cli_subcommands_still_work(subcommand, tmp_note_dir):
    """Existing subcommands must keep working."""
    from click.testing import CliRunner

    from second_brain.cli import cli

    runner = CliRunner()
    result = runner.invoke(cli, [subcommand, "--help"])
    assert result.exit_code == 0

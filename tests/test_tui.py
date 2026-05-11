"""Tests for the Textual TUI (`second_brain.tui`)."""

from __future__ import annotations

import os
import time
from pathlib import Path

import pytest
from textual.widgets import Button, Input, ListView, MarkdownViewer, TextArea

from second_brain.tui import (
    ConfirmDeleteScreen,
    ConfirmDiscardScreen,
    NoteListItem,
    SecondBrainApp,
)

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
        assert text.startswith("---\n")
        assert "\n# My new note\n" in text
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
# Edit flow (issue #16)
# ---------------------------------------------------------------------------


async def test_tui_edit_button_present_in_viewer_mode(tmp_path):
    _write_note(tmp_path, "a.md", "# A\n\n2026-01-01T00:00:00\n\nbody-a\n")
    app = SecondBrainApp(base_dir=tmp_path)
    async with app.run_test() as pilot:
        await pilot.pause()
        edit_btn = app.query_one("#edit-btn", Button)
        assert not edit_btn.has_class("hidden")


async def test_tui_pressing_e_enters_edit_mode_with_full_file(tmp_path):
    p = _write_note(tmp_path, "a.md", "# A\n\n2026-01-01T00:00:00\n\nbody-a\n")
    app = SecondBrainApp(base_dir=tmp_path)
    async with app.run_test() as pilot:
        await pilot.pause()
        await pilot.press("e")
        await pilot.pause()
        assert not app.query_one("#edit-form").has_class("hidden")
        assert app.query_one("#title-input", Input).has_class("hidden")
        body_editor = app.query_one("#body-editor", TextArea)
        assert body_editor.text == p.read_text(encoding="utf-8")


async def test_tui_edit_button_enters_edit_mode(tmp_path):
    _write_note(tmp_path, "a.md", "# A\n\n2026-01-01T00:00:00\n")
    app = SecondBrainApp(base_dir=tmp_path)
    async with app.run_test() as pilot:
        await pilot.pause()
        await pilot.click("#edit-btn")
        await pilot.pause()
        assert not app.query_one("#edit-form").has_class("hidden")


async def test_tui_edit_e_does_nothing_on_empty_list(tmp_path):
    app = SecondBrainApp(base_dir=tmp_path)
    async with app.run_test() as pilot:
        await pilot.pause()
        await pilot.press("e")
        await pilot.pause()
        assert app.query_one("#edit-form").has_class("hidden")


async def test_tui_edit_save_writes_back_to_same_file(tmp_path):
    p = _write_note(tmp_path, "a.md", "# A\n\n2026-01-01T00:00:00\n\nbody-a\n")
    app = SecondBrainApp(base_dir=tmp_path)
    async with app.run_test() as pilot:
        await pilot.pause()
        await pilot.press("e")
        await pilot.pause()
        body_editor = app.query_one("#body-editor", TextArea)
        body_editor.text = "# A\n\n2026-01-01T00:00:00\n\nedited body\n"
        await pilot.click("#save-btn")
        await pilot.pause()

        files = sorted(tmp_path.glob("*.md"))
        assert len(files) == 1
        assert files[0] == p
        text = p.read_text(encoding="utf-8")
        assert "edited body" in text
        assert "modified:" in text
        assert app.query_one("#edit-form").has_class("hidden")


async def test_tui_edit_cancel_discards_changes_silently(tmp_path):
    """Per issue: Cancel and escape discard the edit (existing behavior)."""
    p = _write_note(tmp_path, "a.md", "# A\n\n2026-01-01T00:00:00\n\nbody-a\n")
    original = p.read_text(encoding="utf-8")
    app = SecondBrainApp(base_dir=tmp_path)
    async with app.run_test() as pilot:
        await pilot.pause()
        await pilot.press("e")
        await pilot.pause()
        body_editor = app.query_one("#body-editor", TextArea)
        body_editor.text = "completely changed contents"

        await pilot.click("#cancel-btn")
        await pilot.pause()

        assert p.read_text(encoding="utf-8") == original
        assert app.query_one("#edit-form").has_class("hidden")
        # modal should NOT have been pushed
        assert len(app.screen_stack) == 1


async def test_tui_edit_then_create_keeps_title_input_visible_again(tmp_path):
    """After editing and exiting, starting a new note must show the title input again."""
    _write_note(tmp_path, "a.md", "# A\n\n2026-01-01T00:00:00\n")
    app = SecondBrainApp(base_dir=tmp_path)
    async with app.run_test() as pilot:
        await pilot.pause()
        await pilot.press("e")
        await pilot.pause()
        await pilot.click("#cancel-btn")
        await pilot.pause()
        await pilot.press("n")
        await pilot.pause()
        assert not app.query_one("#title-input", Input).has_class("hidden")


async def test_tui_quit_while_dirty_shows_confirm_modal(tmp_path):
    _write_note(tmp_path, "a.md", "# A\n\n2026-01-01T00:00:00\n\nbody-a\n")
    app = SecondBrainApp(base_dir=tmp_path)
    async with app.run_test() as pilot:
        await pilot.pause()
        await pilot.press("e")
        await pilot.pause()
        body_editor = app.query_one("#body-editor", TextArea)
        body_editor.text = body_editor.text + "dirty edits"

        # Invoke quit action directly to bypass focus complications
        await app.action_quit()
        await pilot.pause()

        assert len(app.screen_stack) == 2
        assert isinstance(app.screen_stack[-1], ConfirmDiscardScreen)


async def test_tui_quit_clean_does_not_show_modal(tmp_path):
    _write_note(tmp_path, "a.md", "# A\n\n2026-01-01T00:00:00\n\nbody-a\n")
    app = SecondBrainApp(base_dir=tmp_path)
    async with app.run_test() as pilot:
        await pilot.pause()
        await pilot.press("e")
        await pilot.pause()
        # do NOT modify body_editor — clean edit
        await app.action_quit()
        await pilot.pause()
        # app exited without modal (no screen pushed)
        # screen_stack may be empty after exit; check no ConfirmDiscardScreen surfaced
        for screen in app.screen_stack:
            assert not isinstance(screen, ConfirmDiscardScreen)


async def test_tui_switch_note_while_dirty_shows_modal(tmp_path):
    _write_note(tmp_path, "a.md", "# A\n\n2026-01-01T00:00:00\n\nbody-a\n")
    _write_note(tmp_path, "b.md", "# B\n\n2026-01-01T00:00:00\n\nbody-b\n")
    app = SecondBrainApp(base_dir=tmp_path)
    async with app.run_test() as pilot:
        await pilot.pause()
        list_view = app.query_one("#notes-list", ListView)
        await pilot.press("e")
        await pilot.pause()
        body_editor = app.query_one("#body-editor", TextArea)
        body_editor.text = body_editor.text + "dirty edit"

        original_idx = list_view.index
        target_idx = 1 if original_idx == 0 else 0
        list_view.index = target_idx
        await pilot.pause()

        assert len(app.screen_stack) == 2
        assert isinstance(app.screen_stack[-1], ConfirmDiscardScreen)


async def test_tui_switch_note_while_dirty_keep_restores_index(tmp_path):
    _write_note(tmp_path, "a.md", "# A\n\n2026-01-01T00:00:00\n\nbody-a\n")
    _write_note(tmp_path, "b.md", "# B\n\n2026-01-01T00:00:00\n\nbody-b\n")
    app = SecondBrainApp(base_dir=tmp_path)
    async with app.run_test() as pilot:
        await pilot.pause()
        list_view = app.query_one("#notes-list", ListView)
        await pilot.press("e")
        await pilot.pause()
        original_idx = list_view.index
        body_editor = app.query_one("#body-editor", TextArea)
        body_editor.text = body_editor.text + "dirty"

        target_idx = 1 if original_idx == 0 else 0
        list_view.index = target_idx
        await pilot.pause()

        await pilot.click("#keep-btn")
        await pilot.pause()

        assert not app.query_one("#edit-form").has_class("hidden")
        assert list_view.index == original_idx
        assert "dirty" in app.query_one("#body-editor", TextArea).text


async def test_tui_switch_note_while_dirty_discard_loads_new_note(tmp_path):
    _write_note(tmp_path, "a.md", "# A\n\n2026-01-01T00:00:00\n\nbody-a\n")
    _write_note(tmp_path, "b.md", "# B\n\n2026-01-01T00:00:00\n\nbody-b\n")
    app = SecondBrainApp(base_dir=tmp_path)
    async with app.run_test() as pilot:
        await pilot.pause()
        list_view = app.query_one("#notes-list", ListView)
        await pilot.press("e")
        await pilot.pause()
        original_idx = list_view.index
        body_editor = app.query_one("#body-editor", TextArea)
        body_editor.text = body_editor.text + "dirty"

        target_idx = 1 if original_idx == 0 else 0
        list_view.index = target_idx
        await pilot.pause()

        await pilot.click("#discard-btn")
        await pilot.pause()

        assert app.query_one("#edit-form").has_class("hidden")
        assert list_view.index == target_idx


async def test_tui_new_note_while_dirty_shows_modal(tmp_path):
    _write_note(tmp_path, "a.md", "# A\n\n2026-01-01T00:00:00\n\nbody-a\n")
    app = SecondBrainApp(base_dir=tmp_path)
    async with app.run_test() as pilot:
        await pilot.pause()
        await pilot.press("e")
        await pilot.pause()
        body_editor = app.query_one("#body-editor", TextArea)
        body_editor.text = body_editor.text + "dirty"

        app.action_new_note()
        await pilot.pause()

        assert len(app.screen_stack) == 2
        assert isinstance(app.screen_stack[-1], ConfirmDiscardScreen)


async def test_tui_new_note_while_dirty_keep_preserves_draft(tmp_path):
    _write_note(tmp_path, "a.md", "# A\n\n2026-01-01T00:00:00\n\nbody-a\n")
    app = SecondBrainApp(base_dir=tmp_path)
    async with app.run_test() as pilot:
        await pilot.pause()
        await pilot.press("e")
        await pilot.pause()
        body_editor = app.query_one("#body-editor", TextArea)
        before = body_editor.text + "dirty"
        body_editor.text = before

        app.action_new_note()
        await pilot.pause()
        await pilot.click("#keep-btn")
        await pilot.pause()

        assert not app.query_one("#edit-form").has_class("hidden")
        assert app.query_one("#title-input", Input).has_class("hidden")
        assert app.query_one("#body-editor", TextArea).text == before


async def test_tui_new_note_while_dirty_discard_clears_form(tmp_path):
    _write_note(tmp_path, "a.md", "# A\n\n2026-01-01T00:00:00\n\nbody-a\n")
    app = SecondBrainApp(base_dir=tmp_path)
    async with app.run_test() as pilot:
        await pilot.pause()
        await pilot.press("e")
        await pilot.pause()
        body_editor = app.query_one("#body-editor", TextArea)
        body_editor.text = body_editor.text + "dirty"

        app.action_new_note()
        await pilot.pause()
        await pilot.click("#discard-btn")
        await pilot.pause()

        assert not app.query_one("#title-input", Input).has_class("hidden")
        assert app.query_one("#body-editor", TextArea).text == ""


async def test_confirm_discard_screen_buttons_dismiss_with_value(tmp_path):
    """The modal returns True for Discard, False for Keep editing."""
    _write_note(tmp_path, "a.md", "# A\n\n2026-01-01T00:00:00\n")
    app = SecondBrainApp(base_dir=tmp_path)
    async with app.run_test() as pilot:
        await pilot.pause()

        # Push the modal manually and capture result via callback
        results: list[bool] = []
        app.push_screen(ConfirmDiscardScreen(), callback=results.append)
        await pilot.pause()

        await pilot.click("#discard-btn")
        await pilot.pause()
        assert results == [True]

        # Push again and click keep
        app.push_screen(ConfirmDiscardScreen(), callback=results.append)
        await pilot.pause()
        await pilot.click("#keep-btn")
        await pilot.pause()
        assert results == [True, False]


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


# ---------------------------------------------------------------------------
# Delete note
# ---------------------------------------------------------------------------


async def test_tui_delete_button_present_in_viewer(tmp_path):
    _write_note(tmp_path, "a.md", "# a\n")
    app = SecondBrainApp(base_dir=tmp_path)
    async with app.run_test() as pilot:
        await pilot.pause()
        btn = app.query_one("#delete-btn", Button)
        assert btn.variant == "error"
        # The whole viewer-buttons row is visible in viewer mode.
        assert not app.query_one("#viewer-buttons").has_class("hidden")


async def test_tui_delete_button_hidden_while_editing(tmp_path):
    _write_note(tmp_path, "a.md", "# a\n")
    app = SecondBrainApp(base_dir=tmp_path)
    async with app.run_test() as pilot:
        await pilot.pause()
        await pilot.press("e")
        await pilot.pause()
        assert app.query_one("#viewer-buttons").has_class("hidden")


async def test_tui_d_press_opens_confirm_delete_modal(tmp_path):
    _write_note(tmp_path, "a.md", "# a\n")
    app = SecondBrainApp(base_dir=tmp_path)
    async with app.run_test() as pilot:
        await pilot.pause()
        await pilot.press("d")
        await pilot.pause()
        assert len(app.screen_stack) == 2
        assert isinstance(app.screen, ConfirmDeleteScreen)


async def test_tui_d_press_noop_on_empty_list(tmp_path):
    app = SecondBrainApp(base_dir=tmp_path)
    async with app.run_test() as pilot:
        await pilot.pause()
        await pilot.press("d")
        await pilot.pause()
        # No modal should be pushed.
        assert len(app.screen_stack) == 1


async def test_tui_d_press_noop_while_editing(tmp_path):
    _write_note(tmp_path, "a.md", "# a\n")
    app = SecondBrainApp(base_dir=tmp_path)
    async with app.run_test() as pilot:
        await pilot.pause()
        await pilot.press("e")
        await pilot.pause()
        screens_before = len(app.screen_stack)
        # Invoke action directly — 'd' is captured by the body editor.
        app.action_delete_note()
        await pilot.pause()
        assert len(app.screen_stack) == screens_before


async def test_tui_delete_cancel_keeps_file(tmp_path):
    p = _write_note(tmp_path, "a.md", "# a\n")
    app = SecondBrainApp(base_dir=tmp_path)
    async with app.run_test() as pilot:
        await pilot.pause()
        await pilot.press("d")
        await pilot.pause()
        await pilot.click("#cancel-delete-btn")
        await pilot.pause()
        assert p.exists()
        list_view = app.query_one("#notes-list", ListView)
        assert len(list_view) == 1


async def test_tui_delete_confirm_removes_file_and_refreshes(tmp_path):
    a = _write_note(tmp_path, "a.md", "# a\n")
    time.sleep(0.01)
    b = _write_note(tmp_path, "b.md", "# b\n")
    # Make b newer for deterministic mtime sort (b is selected initially).
    os.utime(a, (a.stat().st_atime, b.stat().st_mtime - 5))

    app = SecondBrainApp(base_dir=tmp_path)
    async with app.run_test() as pilot:
        await pilot.pause()
        # Currently-selected note is b (newest first under mtime sort).
        assert app._current_path is not None
        assert app._current_path.name == "b.md"

        await pilot.press("d")
        await pilot.pause()
        await pilot.click("#confirm-delete-btn")
        await pilot.pause()

        assert not b.exists()
        assert a.exists()
        list_view = app.query_one("#notes-list", ListView)
        assert len(list_view) == 1
        # Preview falls back to the remaining note.
        assert app._current_path is not None
        assert app._current_path.name == "a.md"


async def test_tui_delete_last_note_clears_preview(tmp_path):
    p = _write_note(tmp_path, "only.md", "# only\nbody-only\n")
    app = SecondBrainApp(base_dir=tmp_path)
    async with app.run_test() as pilot:
        await pilot.pause()
        await pilot.press("d")
        await pilot.pause()
        await pilot.click("#confirm-delete-btn")
        await pilot.pause()

        assert not p.exists()
        list_view = app.query_one("#notes-list", ListView)
        assert len(list_view) == 0
        assert app._current_path is None
        assert app.query_one("#raw-view", TextArea).text == ""


async def test_tui_delete_failure_notifies_and_keeps_file(tmp_path, monkeypatch):
    p = _write_note(tmp_path, "a.md", "# a\n")

    def _boom(_path):
        raise OSError("disk gone")

    monkeypatch.setattr("second_brain.tui.delete_note", _boom)

    app = SecondBrainApp(base_dir=tmp_path)
    async with app.run_test() as pilot:
        await pilot.pause()
        await pilot.press("d")
        await pilot.pause()
        await pilot.click("#confirm-delete-btn")
        await pilot.pause()

        assert p.exists()
        list_view = app.query_one("#notes-list", ListView)
        assert len(list_view) == 1


async def test_confirm_delete_screen_buttons_dismiss_with_value(tmp_path):
    """The modal returns True for Delete, False for Cancel."""
    _write_note(tmp_path, "a.md", "# a\n")
    app = SecondBrainApp(base_dir=tmp_path)
    async with app.run_test() as pilot:
        await pilot.pause()

        results: list[bool] = []
        app.push_screen(ConfirmDeleteScreen("a.md"), callback=results.append)
        await pilot.pause()
        await pilot.click("#confirm-delete-btn")
        await pilot.pause()
        assert results == [True]

        app.push_screen(ConfirmDeleteScreen("a.md"), callback=results.append)
        await pilot.pause()
        await pilot.click("#cancel-delete-btn")
        await pilot.pause()
        assert results == [True, False]

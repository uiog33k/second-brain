"""Textual-based TUI for second_brain.

The TUI is a thin presentation layer; all filesystem and slug logic lives
in :mod:`second_brain.notes`.
"""

from __future__ import annotations

import os
from pathlib import Path

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.screen import ModalScreen
from textual.widgets import (
    Button,
    Footer,
    Header,
    Input,
    Label,
    ListItem,
    ListView,
    MarkdownViewer,
    Static,
    TextArea,
)

from second_brain.notes import SortMode, create_note, list_notes, update_note


def _resolve_base_dir() -> Path:
    return Path(
        os.environ.get("SECOND_BRAIN_DIR", str(Path.home() / "second_brain"))
    ).expanduser()


class NoteListItem(ListItem):
    """ListItem that carries the path of the note it represents."""

    def __init__(self, path: Path) -> None:
        super().__init__(Label(path.name))
        self.path = path


class ConfirmDiscardScreen(ModalScreen[bool]):
    """Modal that asks the user whether to discard unsaved edits."""

    CSS = """
    ConfirmDiscardScreen {
        align: center middle;
    }
    #confirm-dialog {
        width: 60;
        height: auto;
        border: thick $primary;
        background: $surface;
        padding: 1 2;
    }
    #confirm-message { padding-bottom: 1; }
    #confirm-buttons { height: 3; align-horizontal: right; }
    #confirm-buttons Button { margin: 0 1; }
    """

    BINDINGS = [
        Binding("escape", "keep", "Keep editing", show=False),
    ]

    def compose(self) -> ComposeResult:
        with Vertical(id="confirm-dialog"):
            yield Static(
                "Discard unsaved changes?",
                id="confirm-message",
            )
            with Horizontal(id="confirm-buttons"):
                yield Button("Discard", id="discard-btn", variant="error")
                yield Button("Keep editing", id="keep-btn", variant="primary")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "discard-btn":
            self.dismiss(True)
        elif event.button.id == "keep-btn":
            self.dismiss(False)

    def action_keep(self) -> None:
        self.dismiss(False)


class SecondBrainApp(App):
    """Two-pane TUI: note list on the left, viewer/editor on the right."""

    CSS = """
    Screen { layout: vertical; }
    #body { layout: horizontal; height: 1fr; }
    #sidebar {
        width: 30%;
        min-width: 24;
        height: 1fr;
        border-right: solid $primary;
    }
    #notes-list { height: 1fr; }
    #create-btn { width: 100%; height: 3; }
    #right-pane { width: 1fr; height: 1fr; }
    #viewer-buttons { height: 3; align-horizontal: right; }
    #viewer-buttons Button { margin: 0 1; }
    #raw-view { height: 1fr; }
    #edit-form { height: 1fr; }
    #title-input { height: 3; }
    #body-editor { height: 1fr; }
    #edit-buttons { height: 3; align-horizontal: right; }
    #edit-buttons Button { margin: 0 1; }
    .hidden { display: none; }
    """

    BINDINGS = [
        Binding("s", "toggle_sort", "Sort"),
        Binding("r", "toggle_render", "Raw/Rendered"),
        Binding("n", "new_note", "New"),
        Binding("e", "edit_note", "Edit"),
        Binding("escape", "cancel_edit", "Cancel", show=False),
        Binding("q", "quit", "Quit"),
    ]

    def __init__(self, base_dir: Path | None = None) -> None:
        super().__init__()
        self.base_dir = base_dir if base_dir is not None else _resolve_base_dir()
        self.sort_mode: SortMode = "mtime"
        self.render_markdown = True
        self._current_path: Path | None = None
        self._editing_path: Path | None = None
        self._dirty_baseline: str | None = None
        self._suppress_highlight_guard = False

    # ------------------------------------------------------------------
    # Composition
    # ------------------------------------------------------------------
    def compose(self) -> ComposeResult:
        yield Header()
        with Horizontal(id="body"):
            with Vertical(id="sidebar"):
                yield ListView(id="notes-list")
                yield Button("Create", id="create-btn", variant="primary")
            with Vertical(id="right-pane"):
                with Horizontal(id="viewer-buttons"):
                    yield Button("Edit", id="edit-btn")
                yield MarkdownViewer(
                    "",
                    id="markdown-view",
                    show_table_of_contents=False,
                )
                yield TextArea(
                    "",
                    id="raw-view",
                    read_only=True,
                    classes="hidden",
                )
                with Vertical(id="edit-form", classes="hidden"):
                    yield Input(placeholder="Title", id="title-input")
                    yield TextArea("", id="body-editor")
                    with Horizontal(id="edit-buttons"):
                        yield Button("Save", id="save-btn", variant="success")
                        yield Button("Cancel", id="cancel-btn")
        yield Footer()

    async def on_mount(self) -> None:
        await self._refresh_list()

    # ------------------------------------------------------------------
    # Note list / preview
    # ------------------------------------------------------------------
    async def _refresh_list(self, select_path: Path | None = None) -> None:
        list_view = self.query_one("#notes-list", ListView)
        list_view.clear()
        notes = list_notes(self.base_dir, sort=self.sort_mode)
        target_idx = 0
        for i, p in enumerate(notes):
            list_view.append(NoteListItem(p))
            if select_path is not None and p == select_path:
                target_idx = i
        if notes:
            list_view.index = target_idx
            await self._show_note(notes[target_idx])
        else:
            self._current_path = None
            await self._update_preview("")

    async def _show_note(self, path: Path) -> None:
        self._current_path = path
        try:
            text = path.read_text(encoding="utf-8")
        except OSError:
            text = ""
        await self._update_preview(text)

    async def _update_preview(self, text: str) -> None:
        await self.query_one("#markdown-view", MarkdownViewer).document.update(text)
        self.query_one("#raw-view", TextArea).text = text

    # ------------------------------------------------------------------
    # Events
    # ------------------------------------------------------------------
    async def on_list_view_highlighted(self, event: ListView.Highlighted) -> None:
        item = event.item
        if not isinstance(item, NoteListItem):
            return
        if self._guard_navigation(item.path):
            return
        await self._show_note(item.path)

    async def on_list_view_selected(self, event: ListView.Selected) -> None:
        item = event.item
        if not isinstance(item, NoteListItem):
            return
        if self._guard_navigation(item.path):
            return
        await self._show_note(item.path)

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        bid = event.button.id
        if bid == "create-btn":
            self.action_new_note()
        elif bid == "edit-btn":
            self.action_edit_note()
        elif bid == "save-btn":
            await self._save_edit()
        elif bid == "cancel-btn":
            self.action_cancel_edit()

    # ------------------------------------------------------------------
    # Actions
    # ------------------------------------------------------------------
    async def action_toggle_sort(self) -> None:
        if self._is_editing():
            return
        self.sort_mode = "name" if self.sort_mode == "mtime" else "mtime"
        await self._refresh_list(self._current_path)

    def action_toggle_render(self) -> None:
        if self._is_editing():
            return
        self.render_markdown = not self.render_markdown
        md = self.query_one("#markdown-view")
        raw = self.query_one("#raw-view")
        if self.render_markdown:
            md.remove_class("hidden")
            raw.add_class("hidden")
        else:
            md.add_class("hidden")
            raw.remove_class("hidden")

    def action_new_note(self) -> None:
        if self._is_editing() and self._is_dirty():

            def _on_choice(should_discard: bool | None) -> None:
                if should_discard:
                    self._enter_create_mode()

            self.push_screen(ConfirmDiscardScreen(), callback=_on_choice)
            return
        self._enter_create_mode()

    def action_edit_note(self) -> None:
        if self._current_path is None:
            return
        self._enter_edit_existing_mode(self._current_path)

    def action_cancel_edit(self) -> None:
        if self._is_editing():
            self._exit_edit_mode()

    async def action_quit(self) -> None:
        if self._is_editing() and self._is_dirty():

            def _on_choice(should_discard: bool | None) -> None:
                if should_discard:
                    self.exit()

            self.push_screen(ConfirmDiscardScreen(), callback=_on_choice)
            return
        self.exit()

    # ------------------------------------------------------------------
    # Edit mode
    # ------------------------------------------------------------------
    def _is_editing(self) -> bool:
        return not self.query_one("#edit-form").has_class("hidden")

    def _guard_navigation(self, path: Path) -> bool:
        """Intercept a list-view switch when editing.

        Returns True if the navigation was intercepted (caller should not
        proceed). The guard short-circuits when not editing, when the
        target is the note already being edited, or when the suppression
        flag is set (used while restoring the highlight).
        """
        if self._suppress_highlight_guard:
            return False
        if not self._is_editing():
            return False
        if self._editing_path is not None and self._editing_path == path:
            return False
        if not self._is_dirty():
            # Clean edit: silently leave edit mode and let caller load new note.
            self._exit_edit_mode()
            return False

        def _on_choice(should_discard: bool | None) -> None:
            if should_discard:
                self._exit_edit_mode()
                self.run_worker(self._show_note(path), exclusive=False)
            else:
                self._restore_editing_highlight()

        self.push_screen(ConfirmDiscardScreen(), callback=_on_choice)
        return True

    def _restore_editing_highlight(self) -> None:
        if self._editing_path is None:
            return
        list_view = self.query_one("#notes-list", ListView)
        for i, child in enumerate(list_view.children):
            if isinstance(child, NoteListItem) and child.path == self._editing_path:
                self._suppress_highlight_guard = True
                try:
                    list_view.index = i
                finally:
                    self._suppress_highlight_guard = False
                return

    def _is_dirty(self) -> bool:
        if self._dirty_baseline is None:
            return False
        body_editor = self.query_one("#body-editor", TextArea)
        title_input = self.query_one("#title-input", Input)
        current = body_editor.text
        if not title_input.has_class("hidden"):
            current = f"{title_input.value}\x00{current}"
        return current != self._dirty_baseline

    def _snapshot_baseline(self) -> None:
        body_editor = self.query_one("#body-editor", TextArea)
        title_input = self.query_one("#title-input", Input)
        baseline = body_editor.text
        if not title_input.has_class("hidden"):
            baseline = f"{title_input.value}\x00{baseline}"
        self._dirty_baseline = baseline

    def _enter_create_mode(self) -> None:
        self._editing_path = None
        title_input = self.query_one("#title-input", Input)
        body_editor = self.query_one("#body-editor", TextArea)
        title_input.value = ""
        title_input.remove_class("hidden")
        body_editor.text = ""
        self.query_one("#markdown-view").add_class("hidden")
        self.query_one("#raw-view").add_class("hidden")
        self.query_one("#viewer-buttons").add_class("hidden")
        self.query_one("#edit-form").remove_class("hidden")
        self._snapshot_baseline()
        title_input.focus()

    def _enter_edit_existing_mode(self, path: Path) -> None:
        try:
            text = path.read_text(encoding="utf-8")
        except OSError as exc:
            self.notify(f"Failed to open note: {exc}", severity="error")
            return
        self._editing_path = path
        title_input = self.query_one("#title-input", Input)
        body_editor = self.query_one("#body-editor", TextArea)
        title_input.value = ""
        title_input.add_class("hidden")
        body_editor.text = text
        self.query_one("#markdown-view").add_class("hidden")
        self.query_one("#raw-view").add_class("hidden")
        self.query_one("#viewer-buttons").add_class("hidden")
        self.query_one("#edit-form").remove_class("hidden")
        self._snapshot_baseline()
        body_editor.focus()

    def _exit_edit_mode(self) -> None:
        self._editing_path = None
        self._dirty_baseline = None
        self.query_one("#edit-form").add_class("hidden")
        self.query_one("#viewer-buttons").remove_class("hidden")
        if self.render_markdown:
            self.query_one("#markdown-view").remove_class("hidden")
        else:
            self.query_one("#raw-view").remove_class("hidden")

    async def _save_edit(self) -> None:
        if self._editing_path is not None:
            await self._save_existing_note()
        else:
            await self._save_new_note()

    async def _save_new_note(self) -> None:
        title = self.query_one("#title-input", Input).value.strip()
        body = self.query_one("#body-editor", TextArea).text
        if not title:
            self.notify("Title is required to save a note.", severity="warning")
            return
        try:
            path = create_note(title, self.base_dir, body=body or None)
        except OSError as exc:
            self.notify(f"Failed to save note: {exc}", severity="error")
            return
        self._exit_edit_mode()
        await self._refresh_list(select_path=path)

    async def _save_existing_note(self) -> None:
        assert self._editing_path is not None
        content = self.query_one("#body-editor", TextArea).text
        try:
            path = update_note(self._editing_path, content)
        except OSError as exc:
            self.notify(f"Failed to save note: {exc}", severity="error")
            return
        self._exit_edit_mode()
        await self._refresh_list(select_path=path)


def run_tui(base_dir: Path | None = None) -> None:
    """Launch the TUI. Used as the default ``second_brain`` command."""
    SecondBrainApp(base_dir=base_dir).run()

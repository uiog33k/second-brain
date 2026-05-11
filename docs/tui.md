# Interactive TUI

`second_brain` ships with a [Textual](https://textual.textualize.io/) TUI for
browsing notes and capturing new ones without re-running the CLI for each
operation.

Running `second_brain` with **no subcommand** launches the TUI:

```bash
uv run second_brain
```

All existing subcommands (`new`, `list`, `show`) keep working unchanged for
scripting and automation.

## Layout

```
┌─────────────────┬──────────────────────────────────┐
│ Notes list      │                [ Edit ] [ Delete ] │
│   ...           │ Markdown viewer / editor         │
│   ...           │                                  │
│   ...           │ (rendered markdown of the        │
│                 │  selected note by default)       │
│ [ Create ]      │                                  │
└─────────────────┴──────────────────────────────────┘
```

- **Left sidebar:** scrollable list of notes with a **Create** button pinned at
  the bottom.
- **Right pane:** rendered markdown view of the highlighted note, with
  **Edit** and **Delete** buttons at the top. **Edit** opens the highlighted
  note in the editor; **Delete** prompts for confirmation before removing the
  file from disk. A keybinding toggles to a raw text view that shows exactly
  what is on disk.

The TUI reads notes from `SECOND_BRAIN_DIR` (default `~/second_brain`), the
same directory used by the CLI.

## Keybindings

| Key       | Action                                                            |
|-----------|-------------------------------------------------------------------|
| `↑` / `↓` | Move highlight in the note list (preview updates as you move).    |
| `Enter`   | Select the highlighted note (also updates the preview).           |
| `s`       | Toggle sort order: newest-first by mtime ↔ alphabetical by name. |
| `r`       | Toggle preview: rendered markdown ↔ raw text.                    |
| `n`       | Start a new note (same as clicking **Create**).                   |
| `e`       | Edit the highlighted note (same as clicking **Edit**).            |
| `d`       | Delete the highlighted note after a confirmation modal.           |
| `Escape`  | Cancel the current edit and return to the previous selection.     |
| `q`       | Quit the TUI (prompts to confirm if there are unsaved edits).     |

## Creating a note

Pressing `n` (or clicking **Create**) replaces the right pane with an edit
form:

- A **Title** input at the top.
- A **Body** editor below.
- **Save** and **Cancel** buttons.

`Save` reuses the same logic as the `new` subcommand — the title is slugged
(`notes.slugify`) and the file is created via `notes.create_note`. After
saving, the new note appears in the sidebar and is selected automatically.

`Cancel` (or pressing `Escape`) discards the draft and returns to the previous
view without writing anything to disk.

## Editing an existing note

Pressing `e` (or clicking **Edit**) loads the highlighted note's full file
contents into the body editor. The title input is hidden in this mode — the
heading is part of the file contents you are editing, so you can change it
directly. The filename is **not** renamed even if you change the heading.

`Save` rewrites the same file in place via `notes.update_note` and stamps a
`modified: <iso-timestamp>` line right after the creation timestamp (or
replaces the existing one on subsequent saves). The original creation
timestamp is preserved.

`Cancel` (or `Escape`) discards the edit silently and returns to the viewer.

If you press `q` while you have unsaved edits, a **Discard unsaved changes?**
modal appears so you do not accidentally lose work.

## Deleting a note

Pressing `d` (or clicking **Delete**) opens a confirmation modal showing the
filename: **Delete `<filename>`? This cannot be undone.** Confirming removes
the file from disk via `notes.delete_note` (a hard `Path.unlink` — there is no
trash directory), refreshes the list, and falls back to the next note (or
clears the preview if it was the last one). Cancelling leaves the file
untouched. `d` is a no-op while the editor is open or when the list is empty.

## Out of scope

The TUI currently supports view, create, edit, and delete. Renaming files,
search/filter, conflict detection (when files change on disk during editing),
and tag/folder navigation are all explicitly out of scope — use the
underlying markdown files directly if you need those operations.

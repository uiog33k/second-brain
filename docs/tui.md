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
│ Notes list      │ Markdown viewer / editor         │
│   ...           │                                  │
│   ...           │ (rendered markdown of the        │
│   ...           │  selected note by default)       │
│                 │                                  │
│ [ Create ]      │                                  │
└─────────────────┴──────────────────────────────────┘
```

- **Left sidebar:** scrollable list of notes with a **Create** button pinned at
  the bottom.
- **Right pane:** rendered markdown view of the highlighted note. A keybinding
  toggles to a raw text view that shows exactly what is on disk.

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
| `Escape`  | Cancel the current edit and return to the previous selection.     |
| `q`       | Quit the TUI.                                                     |

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

## Out of scope

The TUI is currently view + create only. Editing existing notes, deleting
notes, search/filter, and tag/folder navigation are all explicitly out of
scope for this version — use the underlying markdown files directly if you
need those operations.

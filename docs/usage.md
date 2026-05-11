# Usage

## Installation

Clone the repository and install dependencies:

```bash
uv sync
```

## Running

Running with no subcommand launches the [interactive TUI](tui.md):

```bash
uv run second_brain
```

The CLI also exposes three subcommands for scripting:

```bash
uv run second_brain new "My brilliant idea"   # create a note
uv run second_brain list                      # list notes (newest first)
uv run second_brain show 1                    # print the contents of note 1
```

With dev settings loaded:

```bash
uv run --env-file .env second_brain new "My brilliant idea"
```

Or as a Python module:

```bash
uv run python -m second_brain new "My brilliant idea"
```

## Passing body content to `new`

By default `new` writes a stub note: a YAML frontmatter block (with a
`created:` timestamp) followed by the heading. To capture body content in
one command, pass `--content` / `-c`:

```bash
uv run second_brain new "Quick capture" --content "the body text"
uv run second_brain new "Quick capture" -c "the body text"
```

Or read the body from a file with `--from-file`:

```bash
uv run second_brain new "Imported" --from-file path/to/source.md
```

The body is appended below the heading, separated by a blank line.
Newlines in the supplied content are preserved verbatim.

If both `--content` and `--from-file` are supplied, `--content` wins and a
warning is printed to stderr that `--from-file` was ignored.

## Tags (`-t` / `--tag`)

Tags are written into the YAML frontmatter so Obsidian indexes them
natively (tag pane, Properties UI, Dataview). The flag is repeatable:

```bash
uv run second_brain new "Project kickoff" -t work -t planning
```

Produces:

```markdown
---
created: 2026-05-11T10:30:00
tags:
  - work
  - planning
---

# Project kickoff
```

Tags are emitted in YAML block style — the same shape Obsidian's
"Add property" UI writes — so strict YAML consumers parse every value
as a string regardless of content (`2026`, `true`, `null`, …).

When no `-t` is given, the `tags:` key is omitted but the frontmatter
block (with `created:`) is still written.

### Normalization

Each tag is normalized so Obsidian and YAML can parse it cleanly:

1. Leading/trailing whitespace stripped, then leading `#` stripped.
2. Whitespace and YAML indicator characters
   (`, : [ ] { } " ' # & * ! | > % @ ` ``) replaced with `-`.
3. Runs of `-` collapsed; leading/trailing `-` trimmed.
4. Lower-cased.
5. Duplicates (after normalization) dropped, first occurrence wins.

So `-t '#My Project' -t '#work' -t Work` becomes:

```yaml
tags:
  - my-project
  - work
```

Tags that normalize to empty are dropped; if all of them drop, no
`tags:` key is emitted.

## Environment Variables

| Variable            | Default            | Description                          |
|---------------------|--------------------|--------------------------------------|
| `LOG_LEVEL`         | `INFO`             | Console log level (DEBUG, INFO, …)   |
| `LOG_FILE`          | `app.log`          | Path to the log file                 |
| `SECOND_BRAIN_DIR`  | `~/second_brain/`  | Directory where notes are stored     |

Copy `.env.example` to `.env` for development defaults, then run with `uv run --env-file .env`.

## Log Format

Stderr and the log file share the same compact, pipe-separated layout:

```
2026-05-06 14:32:01 | INF | second_brain.app:main:29 | Hello from second_brain!
```

Levels are abbreviated to three characters (`DBG`, `INF`, `WRN`, `ERR`, `CRT`) and the timestamp is seconds-precision.

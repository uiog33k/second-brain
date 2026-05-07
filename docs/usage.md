# Usage

## Installation

Clone the repository and install dependencies:

```bash
uv sync
```

## Running

The CLI exposes three subcommands:

```bash
uv run second_brain new "My brilliant idea"   # create a note
uv run second_brain list                      # list notes (newest first)
uv run second_brain show 1                    # print the contents of note 1
```

### Creating a note with body content

Pass `--content` (or `-c`) to write a fully populated note in one command:

```bash
uv run second_brain new "Standup notes" --content "Shipped X, blocked on Y."
uv run second_brain new "Idea" -c "$(pbpaste)"
```

Newlines in the value are preserved verbatim, so multi-line bodies work too:

```bash
uv run second_brain new "Outline" -c $'Section 1\nSection 2\nSection 3'
```

When `--content` is omitted, `new` creates the usual stub (heading + timestamp).

With dev settings loaded:

```bash
uv run --env-file .env second_brain new "My brilliant idea"
```

Or as a Python module:

```bash
uv run python -m second_brain new "My brilliant idea"
```

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

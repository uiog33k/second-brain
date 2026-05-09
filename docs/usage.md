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

With dev settings loaded:

```bash
uv run --env-file .env second_brain new "My brilliant idea"
```

Or as a Python module:

```bash
uv run python -m second_brain new "My brilliant idea"
```

## Passing body content to `new`

By default `new` writes a stub note (heading + ISO timestamp). To capture
body content in one command, pass `--content` / `-c`:

```bash
uv run second_brain new "Quick capture" --content "the body text"
uv run second_brain new "Quick capture" -c "the body text"
```

Or read the body from a file with `--from-file`:

```bash
uv run second_brain new "Imported" --from-file path/to/source.md
```

The body is appended below the timestamp, separated by a blank line.
Newlines in the supplied content are preserved verbatim.

If both `--content` and `--from-file` are supplied, `--content` wins and a
warning is printed to stderr that `--from-file` was ignored.

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

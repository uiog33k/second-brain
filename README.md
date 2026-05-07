# second-brain

## Installation

Clone the repository and install dependencies:

```bash
git clone <repo-url>
cd second-brain
uv sync
```

## Usage

The CLI exposes three subcommands:

```bash
uv run second_brain new "My brilliant idea"   # create a note
uv run second_brain list                      # list notes (newest first)
uv run second_brain show 1                    # print the contents of note 1
```

With dev environment variables loaded:

```bash
uv run --env-file .env second_brain new "My brilliant idea"
```

Via Python module:

```bash
uv run python -m second_brain new "My brilliant idea"
```

## Environment Variables

Copy `.env.example` to `.env` for development defaults:

```bash
cp .env.example .env
```

Note: `uv run --env-file .env` loads the dev environment explicitly — there is no auto-loading.

| Variable            | Default            | Description                                          |
|---------------------|--------------------|------------------------------------------------------|
| `LOG_LEVEL`         | `INFO`             | Console log level. Set to `DEBUG` in `.env` for verbose output. |
| `LOG_FILE`          | `app.log`          | Path to the log file.                                |
| `SECOND_BRAIN_DIR`  | `~/second_brain/`  | Directory where notes are stored.                    |

## Log Format

Stderr and the log file share the same compact, pipe-separated layout:

```
2026-05-06 14:32:01 | INF | second_brain.app:main:29 | Hello from second_brain!
```

Levels are abbreviated to three characters (`DBG`, `INF`, `WRN`, `ERR`, `CRT`) and the timestamp is seconds-precision.

## Testing

Run tests:

```bash
uv run pytest
```

Run tests with coverage:

```bash
uv run pytest --cov
```

## Documentation

Preview docs locally:

```bash
uv run python scripts/serve_docs.py
```

Build static docs:

```bash
uv run mkdocs build
```

# Usage

## Installation

Clone the repository and install dependencies:

```bash
uv sync
```

## Creating Notes

Capture a quick idea as a markdown file:

```bash
uv run second_brain new "My brilliant idea about caching"
```

The command prints the full path of the created file:

```
/home/user/second_brain/2026-05-07-my-brilliant-idea-about-caching.md
```

The file contains a level-1 heading followed by a blank line, ready to expand.

## Running

Via the CLI entrypoint:

```bash
uv run second_brain                          # production defaults
uv run --env-file .env second_brain          # dev settings
```

Or as a Python module:

```bash
uv run python -m second_brain
```

## Environment Variables

| Variable           | Default          | Description                          |
|--------------------|------------------|--------------------------------------|
| `LOG_LEVEL`        | `INFO`           | Console log level (DEBUG, INFO, …)   |
| `LOG_FILE`         | `app.log`        | Path to the log file                 |
| `SECOND_BRAIN_DIR` | `~/second_brain` | Directory where notes are stored     |

Copy `.env.example` to `.env` for development defaults, then run with `uv run --env-file .env`.

## Log Format

```
YYYY-MM-DD HH:mm:ss | LVL | module:function:line | message
```

Level abbreviations: `TRC` `DBG` `INF` `SUC` `WRN` `ERR` `CRT`

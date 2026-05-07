# second-brain

## Installation

Clone the repository and install dependencies:

```bash
git clone <repo-url>
cd second-brain
uv sync
```

## Usage

### Creating Notes

Capture a quick idea as a markdown file:

```bash
uv run second_brain new "My brilliant idea about caching"
```

The command prints the full path of the created file:

```
/home/user/second_brain/2026-05-07-my-brilliant-idea-about-caching.md
```

### Listing Notes

See all notes in your notes directory:

```bash
uv run second_brain list
```

```
Notes directory: /home/user/second_brain

1. 2026-04-01-project-ideas.md
2. 2026-05-07-new-feature-brainstorm.md
```

If no notes exist, prints `No notes found.` instead.

### Running

Via the CLI entrypoint:

```bash
uv run second_brain
```

With dev environment variables loaded:

```bash
uv run --env-file .env second_brain
```

Via Python module:

```bash
uv run python -m second_brain
```

## Environment Variables

Copy `.env.example` to `.env` for development defaults:

```bash
cp .env.example .env
```

Then run with `uv run --env-file .env second_brain` — uv does not auto-load `.env` files.

| Variable           | Default          | Description                                       |
|--------------------|------------------|---------------------------------------------------|
| `LOG_LEVEL`        | `INFO`           | Console log level. Set to `DEBUG` in `.env` for verbose output. |
| `LOG_FILE`         | `app.log`        | Path to the rotating log file.                    |
| `SECOND_BRAIN_DIR` | `~/second_brain` | Directory where notes are stored.                 |

### Log Format

```
YYYY-MM-DD HH:mm:ss | LVL | module:function:line | message
```

Level abbreviations: `TRC` `DBG` `INF` `SUC` `WRN` `ERR` `CRT`

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

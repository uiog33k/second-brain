# second-brain

## Installation

Clone the repository and install dependencies:

```bash
git clone <repo-url>
cd second-brain
uv sync
```

## Usage

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

| Variable    | Default   | Description                                       |
|-------------|-----------|---------------------------------------------------|
| `LOG_LEVEL` | `INFO`    | Console log level. Set to `DEBUG` in `.env` for verbose output. |
| `LOG_FILE`  | `app.log` | Path to the rotating log file.                    |

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

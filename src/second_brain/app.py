"""CLI entry point and logging configuration for second-brain."""

import sys

import click
from dotenv import load_dotenv
from loguru import logger

from second_brain.notes import create_note, get_notes_dir

LEVEL_SHORT = {
    "TRACE": "TRC",
    "DEBUG": "DBG",
    "INFO": "INF",
    "SUCCESS": "SUC",
    "WARNING": "WRN",
    "ERROR": "ERR",
    "CRITICAL": "CRT",
}


def _format(record):
    short = LEVEL_SHORT.get(record["level"].name, record["level"].name[:3])
    return (
        "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
        f"<level>{short}</level> | "
        "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
        "<level>{message}</level>\n{exception}"
    )


def configure_logging():
    """Configure loguru for console and file logging.

    Removes the default handler and sets up:

    - stderr handler at ``LOG_LEVEL`` (default: INFO)
    - File handler at DEBUG writing to ``LOG_FILE`` (default: app.log)
    """
    import os

    log_level = os.environ.get("LOG_LEVEL", "INFO")
    log_file = os.environ.get("LOG_FILE", "app.log")
    logger.remove()
    logger.add(sys.stderr, level=log_level, format=_format)
    logger.add(log_file, level="DEBUG", rotation="50 KB", retention=1, format=_format)


@click.group()
def cli():
    """second-brain — personal knowledge CLI."""
    load_dotenv()
    configure_logging()


@cli.command()
@click.argument("title")
def new(title: str):
    """Create a new note with TITLE."""
    path = create_note(title, get_notes_dir())
    click.echo(path)
    logger.info(f"Created note: {path}")


def main():
    """Run the CLI."""
    cli()

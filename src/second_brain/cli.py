"""CLI entry point using Click."""

from __future__ import annotations

import os
from pathlib import Path

import click
from loguru import logger

from second_brain.app import configure_logging
from second_brain.notes import create_note


@click.group(invoke_without_command=True)
@click.pass_context
def cli(ctx: click.Context):
    """second_brain -- capture and organise your thoughts.

    Running with no subcommand launches the interactive TUI.
    """
    configure_logging()
    if ctx.invoked_subcommand is None:
        from second_brain.tui import run_tui

        base_dir = Path(
            os.environ.get("SECOND_BRAIN_DIR", str(Path.home() / "second_brain"))
        ).expanduser()
        logger.debug("Launching TUI with base_dir={}", base_dir)
        run_tui(base_dir=base_dir)


@cli.command()
@click.argument("title")
@click.option(
    "-c",
    "--content",
    "content",
    default=None,
    help="Body text to write below the header. Newlines are preserved.",
)
@click.option(
    "--from-file",
    "from_file",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    default=None,
    help="Read body content from PATH. Ignored if --content is also given.",
)
@click.option(
    "-t",
    "--tag",
    "tags",
    multiple=True,
    help=(
        "Tag to attach (Obsidian YAML frontmatter). Repeatable. "
        "Leading '#' stripped; whitespace and YAML-unsafe characters "
        "become '-'; lower-cased."
    ),
)
def new(
    title: str,
    content: str | None,
    from_file: Path | None,
    tags: tuple[str, ...],
):
    """Create a new note with the given TITLE."""
    base_dir = Path(
        os.environ.get("SECOND_BRAIN_DIR", str(Path.home() / "second_brain"))
    ).expanduser()

    if content is not None and from_file is not None:
        click.echo(
            "warning: --from-file ignored because --content was provided",
            err=True,
        )
        body: str | None = content
    elif from_file is not None:
        body = from_file.read_text(encoding="utf-8")
    else:
        body = content

    logger.debug("Creating note in {} with tags={}", base_dir, list(tags))
    path = create_note(title, base_dir, body=body, tags=list(tags) or None)
    logger.info("Created note: {}", path)
    click.echo(path)


@cli.command("list")
def list_cmd():
    """List all notes in the notes directory."""
    base_dir = Path(
        os.environ.get("SECOND_BRAIN_DIR", str(Path.home() / "second_brain"))
    ).expanduser()

    if not base_dir.is_dir():
        logger.warning("Notes directory does not exist: {}", base_dir)
        click.echo(f"Notes directory does not exist: {base_dir}")
        return

    files = sorted(base_dir.glob("*.md"), reverse=True)

    click.echo(f"Notes: {base_dir}")

    if not files:
        logger.info("No notes found in {}", base_dir)
        click.echo("No notes found.")
        return

    logger.debug("Found {} note(s) in {}", len(files), base_dir)
    for i, f in enumerate(files, 1):
        click.echo(f"{i}. {f.name}")


@cli.command()
@click.argument("number", type=int)
def show(number: int):
    """Display the contents of note NUMBER."""
    base_dir = Path(
        os.environ.get("SECOND_BRAIN_DIR", str(Path.home() / "second_brain"))
    ).expanduser()

    if not base_dir.is_dir():
        logger.error("Notes directory does not exist: {}", base_dir)
        click.echo(f"Error: Notes directory does not exist: {base_dir}", err=True)
        raise SystemExit(1)

    files = sorted(base_dir.glob("*.md"), reverse=True)

    if not files:
        logger.error("No notes found in {}", base_dir)
        click.echo("Error: No notes found.", err=True)
        raise SystemExit(1)

    if number < 1 or number > len(files):
        logger.error("Note {} out of range ({}  available)", number, len(files))
        click.echo(
            f"Error: Note {number} not found. Only {len(files)} notes available.",
            err=True,
        )
        raise SystemExit(1)

    logger.debug("Showing note {}: {}", number, files[number - 1].name)
    click.echo(files[number - 1].read_text())

from click.testing import CliRunner

from second_brain.app import cli


def test_cli_new_creates_file(tmp_path, monkeypatch):
    monkeypatch.setenv("SECOND_BRAIN_DIR", str(tmp_path))
    runner = CliRunner()
    result = runner.invoke(cli, ["new", "My Idea"])
    assert result.exit_code == 0
    assert len(list(tmp_path.glob("*.md"))) == 1


def test_cli_new_prints_path(tmp_path, monkeypatch):
    monkeypatch.setenv("SECOND_BRAIN_DIR", str(tmp_path))
    runner = CliRunner()
    result = runner.invoke(cli, ["new", "My Idea"])
    assert str(tmp_path) in result.output


def test_cli_new_env_override(tmp_path, monkeypatch):
    monkeypatch.setenv("SECOND_BRAIN_DIR", str(tmp_path))
    runner = CliRunner()
    runner.invoke(cli, ["new", "Env Test"])
    assert any(tmp_path.glob("*.md"))


def test_cli_new_file_content(tmp_path, monkeypatch):
    monkeypatch.setenv("SECOND_BRAIN_DIR", str(tmp_path))
    runner = CliRunner()
    runner.invoke(cli, ["new", "Content Test"])
    f = next(tmp_path.glob("*.md"))
    assert f.read_text().startswith("# Content Test\n\n")


def test_cli_list_no_notes_prints_header(tmp_path, monkeypatch):
    monkeypatch.setenv("SECOND_BRAIN_DIR", str(tmp_path / "empty"))
    runner = CliRunner()
    result = runner.invoke(cli, ["list"])
    assert "Notes directory:" in result.output
    assert "No notes found." in result.output


def test_cli_list_no_notes_exit_code(tmp_path, monkeypatch):
    monkeypatch.setenv("SECOND_BRAIN_DIR", str(tmp_path / "empty"))
    runner = CliRunner()
    result = runner.invoke(cli, ["list"])
    assert result.exit_code == 0


def test_cli_list_with_notes_shows_numbered_list(tmp_path, monkeypatch):
    monkeypatch.setenv("SECOND_BRAIN_DIR", str(tmp_path))
    runner = CliRunner()
    runner.invoke(cli, ["new", "Alpha"])
    runner.invoke(cli, ["new", "Beta"])
    result = runner.invoke(cli, ["list"])
    assert "1." in result.output
    assert "2." in result.output
    assert result.exit_code == 0


def test_cli_list_output_contains_directory_path(tmp_path, monkeypatch):
    monkeypatch.setenv("SECOND_BRAIN_DIR", str(tmp_path))
    runner = CliRunner()
    result = runner.invoke(cli, ["list"])
    assert str(tmp_path) in result.output


def test_cli_show_prints_note_content(tmp_path, monkeypatch):
    monkeypatch.setenv("SECOND_BRAIN_DIR", str(tmp_path))
    runner = CliRunner()
    runner.invoke(cli, ["new", "My Note"])
    note = next(tmp_path.glob("*.md"))
    note.write_text("# My Note\n\nsome content", encoding="utf-8")
    result = runner.invoke(cli, ["show", "1"])
    assert result.exit_code == 0
    assert "# My Note" in result.output
    assert "some content" in result.output


def test_cli_show_out_of_range_exits_nonzero(tmp_path, monkeypatch):
    monkeypatch.setenv("SECOND_BRAIN_DIR", str(tmp_path))
    runner = CliRunner()
    runner.invoke(cli, ["new", "My Note"])
    result = runner.invoke(cli, ["show", "99"])
    assert result.exit_code != 0


def test_cli_show_out_of_range_prints_error(tmp_path, monkeypatch):
    monkeypatch.setenv("SECOND_BRAIN_DIR", str(tmp_path))
    runner = CliRunner()
    runner.invoke(cli, ["new", "My Note"])
    result = runner.invoke(cli, ["show", "99"])
    assert "Error" in result.output


def test_cli_show_no_notes_exits_nonzero(tmp_path, monkeypatch):
    monkeypatch.setenv("SECOND_BRAIN_DIR", str(tmp_path))
    runner = CliRunner()
    result = runner.invoke(cli, ["show", "1"])
    assert result.exit_code != 0


def test_cli_show_no_notes_prints_error(tmp_path, monkeypatch):
    monkeypatch.setenv("SECOND_BRAIN_DIR", str(tmp_path))
    runner = CliRunner()
    result = runner.invoke(cli, ["show", "1"])
    assert "Error" in result.output


def test_cli_show_empty_note_succeeds_silently(tmp_path, monkeypatch):
    monkeypatch.setenv("SECOND_BRAIN_DIR", str(tmp_path))
    (tmp_path / "2026-05-01-empty.md").write_text("", encoding="utf-8")
    runner = CliRunner()
    result = runner.invoke(cli, ["show", "1"])
    assert result.exit_code == 0
    assert "Error" not in result.output

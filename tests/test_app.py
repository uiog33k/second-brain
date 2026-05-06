import re

from second_brain.app import main


def test_main_logs_greeting(capfd):
    main()
    captured = capfd.readouterr()
    assert "Hello from second_brain!" in captured.err


def test_log_format_no_milliseconds(capfd):
    main()
    captured = capfd.readouterr()
    assert not re.search(r"\d{2}:\d{2}:\d{2}\.\d", captured.err)


def test_log_format_short_level_name(capfd):
    main()
    captured = capfd.readouterr()
    assert "INF" in captured.err
    assert "INFO" not in captured.err


def test_log_format_pipe_separator(capfd):
    main()
    captured = capfd.readouterr()
    assert "| Hello from second_brain!" in captured.err

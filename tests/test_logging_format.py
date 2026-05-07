"""Verify the tightened loguru log format (issue #1).

Format target:

    2026-05-06 14:32:01 | INF | second_brain.app:main:29 | Hello from second_brain!
"""
import os
import re

from loguru import logger

from second_brain.app import main

_TIMESTAMP_HEAD = re.compile(r"^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2} \|", re.MULTILINE)
_LOCATION = re.compile(r"second_brain\.app:main:\d+")


def _stderr_after_main(capfd):
    main()
    return capfd.readouterr().err


def test_stderr_timestamp_is_seconds_precision(capfd):
    err = _stderr_after_main(capfd)
    assert _TIMESTAMP_HEAD.search(err), f"no seconds-precision timestamp in: {err!r}"
    head = err.splitlines()[0]
    assert not re.search(r"\d{2}:\d{2}:\d{2}\.\d", head), (
        f"sub-second precision still present in: {head!r}"
    )


def test_stderr_uses_three_char_level_abbrev_for_info(capfd):
    err = _stderr_after_main(capfd)
    assert " | INF | " in err, f"expected ' | INF | ' in: {err!r}"
    assert "INFO    " not in err, f"old padded level still present in: {err!r}"


def test_stderr_uses_pipe_separator_before_message(capfd):
    err = _stderr_after_main(capfd)
    assert "| Hello from second_brain!" in err, (
        f"pipe separator missing before message in: {err!r}"
    )
    assert "- Hello from second_brain!" not in err, (
        f"old dash separator still present in: {err!r}"
    )


def test_stderr_includes_module_function_line(capfd):
    err = _stderr_after_main(capfd)
    assert _LOCATION.search(err), f"location component missing from: {err!r}"


def test_file_log_uses_same_format(capfd):
    main()
    capfd.readouterr()
    log_path = os.environ["LOG_FILE"]
    contents = open(log_path).read()
    assert _TIMESTAMP_HEAD.search(contents), (
        f"no seconds-precision timestamp in file: {contents!r}"
    )
    assert " | INF | " in contents, f"INF abbreviation missing from file: {contents!r}"
    assert "| Hello from second_brain!" in contents, (
        f"pipe separator missing before message in file: {contents!r}"
    )


def test_warning_level_abbreviates_to_wrn(capfd):
    main()
    logger.warning("warn-probe")
    err = capfd.readouterr().err
    assert " | WRN | " in err, f"WRN abbreviation missing from: {err!r}"
    assert "| warn-probe" in err, f"warn-probe message missing from: {err!r}"

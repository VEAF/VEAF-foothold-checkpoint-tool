"""Tests for file logging setup.

The tool used to write nothing to disk: when a restore misbehaved on a server,
the only trace was whatever happened to still be in a console buffer.
"""

import logging
from pathlib import Path

import pytest


@pytest.fixture(autouse=True)
def clean_package_logger():
    """Remove handlers these tests attach, so they do not leak into each other."""
    logger = logging.getLogger("foothold_checkpoint")
    original_handlers = logger.handlers[:]
    original_level = logger.level

    yield

    for handler in logger.handlers[:]:
        if handler not in original_handlers:
            handler.close()
            logger.removeHandler(handler)
    logger.setLevel(original_level)


class TestSetupFileLogging:
    """setup_file_logging() wires the package logger to a rotating file."""

    def test_creates_the_log_file_and_its_parent_directory(self, tmp_path):
        from foothold_checkpoint.core.logging_config import setup_file_logging

        log_file = tmp_path / "nested" / "foothold.log"

        setup_file_logging(log_file=log_file)

        assert log_file.parent.is_dir()
        assert log_file.exists()

    def test_writes_records_to_the_file(self, tmp_path):
        from foothold_checkpoint.core.logging_config import get_logger, setup_file_logging

        log_file = tmp_path / "foothold.log"
        setup_file_logging(log_file=log_file)

        get_logger("foothold_checkpoint.core.storage").info("restoring to %s", "C:/Saves")

        assert "restoring to C:/Saves" in log_file.read_text(encoding="utf-8")

    def test_records_carry_a_timestamp_and_a_level(self, tmp_path):
        from foothold_checkpoint.core.logging_config import get_logger, setup_file_logging

        log_file = tmp_path / "foothold.log"
        setup_file_logging(log_file=log_file)

        get_logger("foothold_checkpoint.core.storage").warning("something odd")

        contents = log_file.read_text(encoding="utf-8")
        assert "WARNING" in contents
        assert "foothold_checkpoint.core.storage" in contents

    def test_writes_tracebacks_when_logging_an_exception(self, tmp_path):
        from foothold_checkpoint.core.logging_config import get_logger, setup_file_logging

        log_file = tmp_path / "foothold.log"
        setup_file_logging(log_file=log_file)

        try:
            raise ValueError("checksum mismatch")
        except ValueError:
            get_logger("foothold_checkpoint.core.storage").error("save failed", exc_info=True)

        contents = log_file.read_text(encoding="utf-8")
        assert "Traceback (most recent call last)" in contents
        assert "checksum mismatch" in contents

    def test_calling_it_twice_does_not_duplicate_handlers(self, tmp_path):
        from foothold_checkpoint.core.logging_config import get_logger, setup_file_logging

        log_file = tmp_path / "foothold.log"

        setup_file_logging(log_file=log_file)
        setup_file_logging(log_file=log_file)

        get_logger("foothold_checkpoint.core.storage").info("only once please")

        contents = log_file.read_text(encoding="utf-8")
        assert contents.count("only once please") == 1

    def test_debug_records_are_dropped_at_the_default_level(self, tmp_path):
        from foothold_checkpoint.core.logging_config import get_logger, setup_file_logging

        log_file = tmp_path / "foothold.log"
        setup_file_logging(log_file=log_file)

        get_logger("foothold_checkpoint.core.storage").debug("chatty detail")

        assert "chatty detail" not in log_file.read_text(encoding="utf-8")

    def test_debug_records_are_kept_when_asked(self, tmp_path):
        from foothold_checkpoint.core.logging_config import get_logger, setup_file_logging

        log_file = tmp_path / "foothold.log"
        setup_file_logging(log_file=log_file, level=logging.DEBUG)

        get_logger("foothold_checkpoint.core.storage").debug("chatty detail")

        assert "chatty detail" in log_file.read_text(encoding="utf-8")

    def test_returns_the_log_file_it_used(self, tmp_path):
        from foothold_checkpoint.core.logging_config import setup_file_logging

        log_file = tmp_path / "foothold.log"

        assert setup_file_logging(log_file=log_file) == log_file

    def test_default_log_file_lives_under_the_user_configuration_directory(self):
        from foothold_checkpoint.core.logging_config import DEFAULT_LOG_FILE

        assert DEFAULT_LOG_FILE.name == "foothold-checkpoint.log"
        assert DEFAULT_LOG_FILE.parent.name == "logs"
        assert ".foothold-checkpoint" in str(DEFAULT_LOG_FILE)

    def test_does_not_crash_when_the_log_file_cannot_be_opened(self, tmp_path):
        """A read-only or otherwise unusable log path must not kill the command."""
        from foothold_checkpoint.core.logging_config import setup_file_logging

        blocker = tmp_path / "blocker"
        blocker.write_text("I am a file, not a directory", encoding="utf-8")

        assert setup_file_logging(log_file=blocker / "foothold.log") is None

    def test_a_failed_reconfiguration_keeps_the_working_log(self, tmp_path):
        """Swapping to a bad path must not take the good handler down with it."""
        from foothold_checkpoint.core.logging_config import get_logger, setup_file_logging

        good_log = tmp_path / "good.log"
        setup_file_logging(log_file=good_log)

        blocker = tmp_path / "blocker"
        blocker.write_text("not a directory", encoding="utf-8")
        assert setup_file_logging(log_file=blocker / "bad.log") is None

        get_logger("foothold_checkpoint.core.storage").info("still recorded")

        assert "still recorded" in good_log.read_text(encoding="utf-8")


class TestGetLogger:
    """get_logger() hands out loggers under the package namespace."""

    def test_returns_a_logger_with_the_requested_name(self):
        from foothold_checkpoint.core.logging_config import get_logger

        assert get_logger("foothold_checkpoint.core.storage").name == (
            "foothold_checkpoint.core.storage"
        )

    def test_does_not_configure_anything_on_its_own(self):
        """Importing the plugin must not steal logging from the host bot."""
        from foothold_checkpoint.core.logging_config import get_logger

        logger = logging.getLogger("foothold_checkpoint")
        before = len(logger.handlers)

        get_logger("foothold_checkpoint.core.storage")

        assert len(logging.getLogger("foothold_checkpoint").handlers) == before


class TestLogFilePath:
    """The resolved log file is predictable."""

    def test_accepts_a_string_path(self, tmp_path):
        from foothold_checkpoint.core.logging_config import setup_file_logging

        log_file = tmp_path / "foothold.log"

        assert setup_file_logging(log_file=str(log_file)) == Path(log_file)

"""Tests for the --debug and --log-file options.

Without these, a user facing a failed command saw a single red line with no
cause and no file to look in, because every command catches exceptions and
prints only ``str(e)``.
"""

import yaml
from typer.testing import CliRunner

runner = CliRunner()


def write_config(tmp_path, checkpoints_dir=None):
    """Write a minimal valid config file and return its path."""
    checkpoints_dir = checkpoints_dir or tmp_path / "checkpoints"
    checkpoints_dir.mkdir(parents=True, exist_ok=True)
    (tmp_path / "Saves").mkdir(parents=True, exist_ok=True)
    config_file = tmp_path / "config.yaml"
    config_file.write_text(
        yaml.safe_dump(
            {
                "checkpoints_dir": str(checkpoints_dir),
                "servers": {
                    "foothold1": {
                        "path": str(tmp_path / "Saves"),
                        "description": "Test server",
                    }
                },
                "campaigns": {
                    "caucasus": {
                        "display_name": "Caucasus",
                        "files": {
                            "persistence": ["FootHold_CA_v0.2.lua"],
                            "ctld_save": {"files": [], "optional": True},
                            "ctld_farps": {"files": [], "optional": True},
                            "storage": {"files": [], "optional": True},
                        },
                    }
                },
            }
        ),
        encoding="utf-8",
    )
    return config_file


def write_corrupt_checkpoint(tmp_path):
    """Create a file that looks like a checkpoint but is not a valid ZIP."""
    corrupt = tmp_path / "checkpoints" / "caucasus_2026-04-30_22-18-58.zip"
    corrupt.parent.mkdir(parents=True, exist_ok=True)
    corrupt.write_text("this is not a zip archive", encoding="utf-8")
    return corrupt


class TestDebugFlag:
    """--debug turns an opaque one-liner into something actionable."""

    def test_prints_a_traceback_when_a_command_fails(self, tmp_path):
        config_file = write_config(tmp_path)
        corrupt = write_corrupt_checkpoint(tmp_path)

        from foothold_checkpoint.cli import app

        result = runner.invoke(
            app,
            ["--config", str(config_file), "--debug", "restore", str(corrupt), "-s", "foothold1"],
            input="\n",
        )

        assert result.exit_code != 0
        assert "Traceback (most recent call last)" in result.stdout

    def test_stays_quiet_about_internals_without_the_flag(self, tmp_path):
        config_file = write_config(tmp_path)
        corrupt = write_corrupt_checkpoint(tmp_path)

        from foothold_checkpoint.cli import app

        result = runner.invoke(
            app,
            ["--config", str(config_file), "restore", str(corrupt), "-s", "foothold1"],
            input="\n",
        )

        assert result.exit_code != 0
        assert "Traceback (most recent call last)" not in result.stdout
        assert "--debug" in result.stdout, "the user must be told how to get more"

    def test_still_shows_the_error_message_itself(self, tmp_path):
        config_file = write_config(tmp_path)
        corrupt = write_corrupt_checkpoint(tmp_path)

        from foothold_checkpoint.cli import app

        result = runner.invoke(
            app,
            ["--config", str(config_file), "--debug", "restore", str(corrupt), "-s", "foothold1"],
            input="\n",
        )

        assert "not a valid ZIP archive" in result.stdout

    def test_a_deliberate_exit_is_not_reported_as_a_crash(self, tmp_path):
        """typer.Exit subclasses RuntimeError, so it must be let through."""
        config_file = write_config(tmp_path)

        from foothold_checkpoint.cli import app

        result = runner.invoke(
            app,
            ["--config", str(config_file), "restore", "no-such-checkpoint.zip"],
            input="\n",
        )

        assert result.exit_code == 1
        assert "Checkpoint file not found" in result.stdout
        assert "Error: 1" not in result.stdout
        assert "Warning: 1" not in result.stdout


class TestLogFileOption:
    """--log-file puts the operation trace where the user asks for it."""

    def test_writes_the_log_to_the_requested_file(self, tmp_path):
        config_file = write_config(tmp_path)
        log_file = tmp_path / "logs" / "run.log"

        from foothold_checkpoint.cli import app

        runner.invoke(
            app,
            ["--config", str(config_file), "--log-file", str(log_file), "list"],
        )

        assert log_file.exists()

    def test_records_a_failed_restore_with_its_traceback(self, tmp_path):
        config_file = write_config(tmp_path)
        corrupt = write_corrupt_checkpoint(tmp_path)
        log_file = tmp_path / "run.log"

        from foothold_checkpoint.cli import app

        runner.invoke(
            app,
            [
                "--config",
                str(config_file),
                "--log-file",
                str(log_file),
                "restore",
                str(corrupt),
                "-s",
                "foothold1",
            ],
            input="\n",
        )

        contents = log_file.read_text(encoding="utf-8")
        assert "restore failed" in contents
        assert "Traceback (most recent call last)" in contents

    def test_debug_level_reaches_the_file(self, tmp_path):
        config_file = write_config(tmp_path)
        log_file = tmp_path / "run.log"

        from foothold_checkpoint.cli import app

        result = runner.invoke(
            app,
            [
                "--config",
                str(config_file),
                "--log-file",
                str(log_file),
                "--debug",
                "list",
            ],
        )

        assert result.exit_code == 0
        assert "DEBUG" in log_file.read_text(encoding="utf-8")

    def test_an_unusable_log_path_does_not_break_the_command(self, tmp_path):
        config_file = write_config(tmp_path)
        blocker = tmp_path / "blocker"
        blocker.write_text("not a directory", encoding="utf-8")

        from foothold_checkpoint.cli import app

        result = runner.invoke(
            app,
            ["--config", str(config_file), "--log-file", str(blocker / "run.log"), "list"],
        )

        assert result.exit_code == 0

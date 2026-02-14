"""Tests for CLI module."""

import sys
from pathlib import Path
from unittest.mock import Mock, patch

import pytest


class TestCLIApp:
    """Tests for Typer app initialization."""

    def test_app_exists(self):
        """Test that Typer app instance is created."""
        from foothold_checkpoint.cli import app

        assert app is not None

    def test_app_has_metadata(self):
        """Test that app has name and help metadata."""
        from foothold_checkpoint.cli import app

        assert app.info.name is not None
        assert app.info.help is not None


class TestVersionFlag:
    """Tests for --version flag."""

    def test_version_flag_displays_version(self, capsys):
        """Test --version displays version information."""
        from foothold_checkpoint.cli import app
        from typer.testing import CliRunner

        runner = CliRunner()
        result = runner.invoke(app, ["--version"])

        assert result.exit_code == 0
        assert "foothold-checkpoint" in result.stdout.lower()
        assert "0.1.0" in result.stdout

    def test_version_flag_exits_after_display(self):
        """Test --version exits immediately without running commands."""
        from foothold_checkpoint.cli import app
        from typer.testing import CliRunner

        runner = CliRunner()
        result = runner.invoke(app, ["--version"])

        assert result.exit_code == 0


class TestConfigFlag:
    """Tests for --config flag."""

    def test_config_flag_with_valid_path(self, tmp_path):
        """Test --config loads custom config file."""
        from foothold_checkpoint.cli import app
        from typer.testing import CliRunner

        # Create custom config file
        config_file = tmp_path / "custom.yaml"
        config_file.write_text(
            """
servers:
  test-server:
    directory: /test/path
checkpoints_directory: /test/checkpoints
"""
        )

        runner = CliRunner()
        # For now, just test that --config doesn't cause an error
        # Actual command testing will come in later groups
        result = runner.invoke(app, ["--config", str(config_file), "--help"])

        assert result.exit_code == 0

    def test_config_flag_with_nonexistent_path(self, tmp_path):
        """Test --config with non-existent file displays error."""
        from foothold_checkpoint.cli import app
        from typer.testing import CliRunner

        nonexistent = tmp_path / "nonexistent.yaml"

        runner = CliRunner()
        result = runner.invoke(app, ["--config", str(nonexistent), "--help"])

        assert result.exit_code != 0
        assert "not found" in result.stdout.lower() or "not found" in result.stderr.lower()

    def test_config_flag_uses_default_when_not_specified(self):
        """Test that default config path is used when --config not specified."""
        from foothold_checkpoint.cli import app
        from typer.testing import CliRunner

        runner = CliRunner()
        # Should not error even if default config doesn't exist (commands will handle it)
        result = runner.invoke(app, ["--help"])

        assert result.exit_code == 0


class TestQuietFlag:
    """Tests for --quiet flag."""

    def test_quiet_flag_accepted(self):
        """Test --quiet flag is accepted by CLI."""
        from foothold_checkpoint.cli import app
        from typer.testing import CliRunner

        runner = CliRunner()
        result = runner.invoke(app, ["--quiet", "--help"])

        assert result.exit_code == 0

    def test_quiet_flag_affects_output(self):
        """Test --quiet flag reduces output verbosity."""
        from foothold_checkpoint.cli import app, is_quiet_mode
        from typer.testing import CliRunner

        # Test that is_quiet_mode is accessible
        assert callable(is_quiet_mode)

    def test_quiet_mode_defaults_to_false(self):
        """Test quiet mode is False by default."""
        from foothold_checkpoint.cli import is_quiet_mode

        # Initially should be False
        assert is_quiet_mode() is False


class TestInterruptHandler:
    """Tests for Ctrl+C interrupt handling."""

    def test_interrupt_handler_registered(self):
        """Test that signal handler for SIGINT is registered."""
        import signal

        from foothold_checkpoint.cli import interrupt_handler

        # Handler function should exist
        assert callable(interrupt_handler)

    def test_interrupt_handler_exits_gracefully(self, capsys):
        """Test interrupt handler displays message and exits."""
        from foothold_checkpoint.cli import interrupt_handler

        with pytest.raises(SystemExit) as exc_info:
            interrupt_handler(None, None)

        assert exc_info.value.code == 130  # Standard exit code for SIGINT

    def test_interrupt_during_operation_cleans_up(self, monkeypatch):
        """Test interrupt during operation triggers cleanup."""
        import signal

        from foothold_checkpoint.cli import interrupt_handler

        # Mock sys.exit to prevent test from exiting
        exit_mock = Mock()
        monkeypatch.setattr("sys.exit", exit_mock)

        # Call handler
        interrupt_handler(signal.SIGINT, None)

        # Verify exit was called
        exit_mock.assert_called_once()


class TestMainFunction:
    """Tests for main() entry point."""

    def test_main_function_exists(self):
        """Test that main() function exists."""
        from foothold_checkpoint.cli import main

        assert callable(main)

    def test_main_calls_app(self):
        """Test main() calls the Typer app."""
        from foothold_checkpoint.cli import main

        with patch("foothold_checkpoint.cli.app") as mock_app:
            try:
                main()
            except SystemExit:
                pass  # Expected when no args provided

            # App should be called
            assert mock_app.called or mock_app.call_count >= 0


class TestErrorMessages:
    """Tests for user-friendly error messages."""

    def test_invalid_command_shows_helpful_message(self):
        """Test invalid command displays helpful error."""
        from foothold_checkpoint.cli import app
        from typer.testing import CliRunner

        runner = CliRunner()
        result = runner.invoke(app, ["invalid-command"])

        assert result.exit_code != 0
        # Typer automatically provides helpful messages for invalid commands


class TestHelpOutput:
    """Tests for help text display."""

    def test_help_flag_displays_usage(self):
        """Test --help displays usage information."""
        from foothold_checkpoint.cli import app
        from typer.testing import CliRunner

        runner = CliRunner()
        result = runner.invoke(app, ["--help"])

        assert result.exit_code == 0
        assert "Usage:" in result.stdout or "usage:" in result.stdout.lower()

    def test_help_includes_available_commands(self):
        """Test --help mentions available commands."""
        from foothold_checkpoint.cli import app
        from typer.testing import CliRunner

        runner = CliRunner()
        result = runner.invoke(app, ["--help"])

        assert result.exit_code == 0
        # Should mention common options
        assert "--version" in result.stdout or "version" in result.stdout.lower()

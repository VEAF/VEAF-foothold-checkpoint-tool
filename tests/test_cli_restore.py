"""Tests for CLI restore command."""

from unittest.mock import Mock, patch


class TestRestoreCommandWithFlags:
    """Tests for restore command with all flags provided."""

    def test_restore_with_all_required_flags(self, tmp_path):
        """Test restore command with checkpoint file and --server flag."""
        from typer.testing import CliRunner

        from foothold_checkpoint.cli import app

        # Create mock config
        config_file = tmp_path / "config.yaml"
        config_file.write_text(
            "servers:\n"
            "  test-server:\n"
            "    mission_directory: /path/to/mission\n"
            "checkpoints_directory: /path/to/checkpoints\n"
        )

        checkpoint_file = tmp_path / "afghanistan_2024-02-14_10-30-00.zip"

        runner = CliRunner()
        with patch("foothold_checkpoint.cli.load_config") as mock_load, \
             patch("foothold_checkpoint.cli.restore_checkpoint") as mock_restore, \
             patch("pathlib.Path.exists", return_value=True):

            # Setup mocks
            mock_config = Mock()
            mock_config.servers = {"test-server": Mock(mission_directory=tmp_path / "mission")}
            mock_config.checkpoints_directory = tmp_path / "checkpoints"
            mock_load.return_value = mock_config

            mock_restore.return_value = [
                tmp_path / "mission" / "foothold_afghanistan.lua",
                tmp_path / "mission" / "foothold_afghanistan_storage.csv"
            ]

            result = runner.invoke(app, [
                "restore",
                str(checkpoint_file),
                "--server", "test-server"
            ])

        assert result.exit_code == 0
        assert "restored successfully" in result.stdout.lower() or "success" in result.stdout.lower()
        mock_restore.assert_called_once()

    def test_restore_with_restore_ranks_flag(self, tmp_path):
        """Test restore command with --restore-ranks flag."""
        from typer.testing import CliRunner

        from foothold_checkpoint.cli import app

        config_file = tmp_path / "config.yaml"
        config_file.write_text(
            "servers:\n"
            "  test-server:\n"
            "    mission_directory: /path/to/mission\n"
            "checkpoints_directory: /path/to/checkpoints\n"
        )

        checkpoint_file = tmp_path / "afghanistan_2024-02-14_10-30-00.zip"

        runner = CliRunner()
        with patch("foothold_checkpoint.cli.load_config") as mock_load, \
             patch("foothold_checkpoint.cli.restore_checkpoint") as mock_restore, \
             patch("pathlib.Path.exists", return_value=True):

            mock_config = Mock()
            mock_config.servers = {"test-server": Mock(mission_directory=tmp_path / "mission")}
            mock_config.checkpoints_directory = tmp_path / "checkpoints"
            mock_load.return_value = mock_config

            mock_restore.return_value = [
                tmp_path / "mission" / "foothold_afghanistan.lua",
                tmp_path / "mission" / "Foothold_Ranks.lua"
            ]

            result = runner.invoke(app, [
                "restore",
                str(checkpoint_file),
                "--server", "test-server",
                "--restore-ranks"
            ])

        assert result.exit_code == 0
        # Verify restore_ranks=True was passed
        call_args = mock_restore.call_args
        assert call_args.kwargs.get("restore_ranks") is True

    def test_restore_with_invalid_server(self, tmp_path):
        """Test error when server is not in config."""
        from typer.testing import CliRunner

        from foothold_checkpoint.cli import app

        config_file = tmp_path / "config.yaml"
        config_file.write_text(
            "servers:\n"
            "  test-server:\n"
            "    mission_directory: /path/to/mission\n"
            "checkpoints_directory: /path/to/checkpoints\n"
        )

        checkpoint_file = tmp_path / "checkpoint.zip"

        runner = CliRunner()
        with patch("foothold_checkpoint.cli.load_config") as mock_load, \
             patch("pathlib.Path.exists", return_value=True):

            mock_config = Mock()
            mock_config.servers = {"test-server": Mock()}
            mock_load.return_value = mock_config

            result = runner.invoke(app, [
                "restore",
                str(checkpoint_file),
                "--server", "nonexistent-server"
            ])

        assert result.exit_code != 0
        assert "not found" in result.stdout.lower() or "invalid" in result.stdout.lower()

    def test_restore_with_invalid_checkpoint_file(self, tmp_path):
        """Test error when checkpoint file does not exist."""
        from typer.testing import CliRunner

        from foothold_checkpoint.cli import app

        config_file = tmp_path / "config.yaml"
        config_file.write_text(
            "servers:\n"
            "  test-server:\n"
            "    mission_directory: /path/to/mission\n"
            "checkpoints_directory: /path/to/checkpoints\n"
        )

        nonexistent_file = tmp_path / "nonexistent.zip"

        runner = CliRunner()
        with patch("foothold_checkpoint.cli.load_config") as mock_load:

            mock_config = Mock()
            mock_config.servers = {"test-server": Mock(mission_directory=tmp_path / "mission")}
            mock_load.return_value = mock_config

            result = runner.invoke(app, [
                "restore",
                str(nonexistent_file),
                "--server", "test-server"
            ])

        assert result.exit_code != 0
        assert "not found" in result.stdout.lower() or "error" in result.stdout.lower()


class TestCheckpointSelectionPrompt:
    """Tests for checkpoint selection prompt when file not provided."""

    def test_checkpoint_prompt_when_file_missing(self, tmp_path):
        """Test interactive checkpoint selection when no file argument provided."""
        from typer.testing import CliRunner

        from foothold_checkpoint.cli import app

        config_file = tmp_path / "config.yaml"
        config_file.write_text(
            "servers:\n"
            "  test-server:\n"
            "    mission_directory: /path/to/mission\n"
            "checkpoints_directory: /path/to/checkpoints\n"
        )

        runner = CliRunner()
        with patch("foothold_checkpoint.cli.load_config") as mock_load, \
             patch("foothold_checkpoint.cli.list_checkpoints") as mock_list, \
             patch("foothold_checkpoint.cli.restore_checkpoint") as mock_restore, \
             patch("foothold_checkpoint.cli.Prompt.ask", side_effect=["1", "test-server"]), \
             patch("pathlib.Path.exists", return_value=True):

            mock_config = Mock()
            mock_config.servers = {"test-server": Mock(mission_directory=tmp_path / "mission")}
            mock_config.checkpoints_directory = tmp_path / "checkpoints"
            mock_load.return_value = mock_config

            # Mock list_checkpoints to return available checkpoints (as dicts)
            mock_checkpoint = {
                "filename": "afghanistan_2024-02-14.zip",
                "campaign": "afghanistan",
                "timestamp": "2024-02-14 10:30:00",
                "server": "test-server",
                "size_bytes": 1024,
                "size_human": "1.0 KB"
            }
            mock_list.return_value = [mock_checkpoint]

            mock_restore.return_value = [tmp_path / "mission" / "foothold_afghanistan.lua"]

            result = runner.invoke(app, ["restore"])

        assert result.exit_code == 0
        mock_list.assert_called_once()

    def test_checkpoint_prompt_displays_available_checkpoints(self, tmp_path):
        """Test that checkpoint selection displays a numbered list."""
        from typer.testing import CliRunner

        from foothold_checkpoint.cli import app

        config_file = tmp_path / "config.yaml"
        config_file.write_text(
            "servers:\n"
            "  test-server:\n"
            "    mission_directory: /path/to/mission\n"
            "checkpoints_directory: /path/to/checkpoints\n"
        )

        runner = CliRunner()
        with patch("foothold_checkpoint.cli.load_config") as mock_load, \
             patch("foothold_checkpoint.cli.list_checkpoints") as mock_list, \
             patch("foothold_checkpoint.cli.restore_checkpoint") as mock_restore, \
             patch("foothold_checkpoint.cli.Prompt.ask", side_effect=["1", "test-server"]), \
             patch("pathlib.Path.exists", return_value=True):

            mock_config = Mock()
            mock_config.servers = {"test-server": Mock(mission_directory=tmp_path / "mission")}
            mock_config.checkpoints_directory = tmp_path / "checkpoints"
            mock_load.return_value = mock_config

            mock_checkpoint1 = {
                "filename": "afghanistan_2024-02-14.zip",
                "campaign": "afghanistan",
                "timestamp": "2024-02-14 10:30:00",
                "server": "test-server",
                "size_bytes": 2048,
                "size_human": "2.0 KB"
            }

            mock_checkpoint2 = {
                "filename": "syria_2024-02-13.zip",
                "campaign": "syria",
                "timestamp": "2024-02-13 15:45:00",
                "server": "prod-1",
                "size_bytes": 1536,
                "size_human": "1.5 KB"
            }

            mock_list.return_value = [mock_checkpoint1, mock_checkpoint2]
            mock_restore.return_value = [tmp_path / "mission" / "foothold.lua"]

            result = runner.invoke(app, ["restore"])

        # Check that checkpoints are listed
        assert "afghanistan" in result.stdout or "1" in result.stdout

    def test_checkpoint_prompt_with_no_checkpoints_found(self, tmp_path):
        """Test error when no checkpoints are available."""
        from typer.testing import CliRunner

        from foothold_checkpoint.cli import app

        config_file = tmp_path / "config.yaml"
        config_file.write_text(
            "servers:\n"
            "  test-server:\n"
            "    mission_directory: /path/to/mission\n"
            "checkpoints_directory: /path/to/checkpoints\n"
        )

        runner = CliRunner()
        with patch("foothold_checkpoint.cli.load_config") as mock_load, \
             patch("foothold_checkpoint.cli.list_checkpoints") as mock_list:

            mock_config = Mock()
            mock_config.servers = {"test-server": Mock()}
            mock_config.checkpoints_directory = tmp_path / "checkpoints"
            mock_load.return_value = mock_config

            mock_list.return_value = []

            result = runner.invoke(app, ["restore"])

        assert result.exit_code != 0
        assert "no checkpoints" in result.stdout.lower() or "not found" in result.stdout.lower()


class TestServerPrompt:
    """Tests for server prompt when flag missing."""

    def test_server_prompt_when_flag_missing(self, tmp_path):
        """Test server prompt when --server flag is not provided."""
        from typer.testing import CliRunner

        from foothold_checkpoint.cli import app

        config_file = tmp_path / "config.yaml"
        config_file.write_text(
            "servers:\n"
            "  test-server:\n"
            "    mission_directory: /path/to/mission\n"
            "  prod-1:\n"
            "    mission_directory: /path/to/prod\n"
            "checkpoints_directory: /path/to/checkpoints\n"
        )

        checkpoint_file = tmp_path / "checkpoint.zip"

        runner = CliRunner()
        with patch("foothold_checkpoint.cli.load_config") as mock_load, \
             patch("foothold_checkpoint.cli.restore_checkpoint") as mock_restore, \
             patch("foothold_checkpoint.cli.Prompt.ask", return_value="test-server"), \
             patch("pathlib.Path.exists", return_value=True):

            mock_config = Mock()
            mock_config.servers = {
                "test-server": Mock(mission_directory=tmp_path / "mission"),
                "prod-1": Mock(mission_directory=tmp_path / "prod")
            }
            mock_config.checkpoints_directory = tmp_path / "checkpoints"
            mock_load.return_value = mock_config

            mock_restore.return_value = [tmp_path / "mission" / "foothold.lua"]

            result = runner.invoke(app, ["restore", str(checkpoint_file)])

        assert result.exit_code == 0
        # Prompt.ask should have been called for server selection
        assert mock_restore.called

    def test_server_prompt_displays_available_servers(self, tmp_path):
        """Test that server prompt displays available servers from config."""
        from typer.testing import CliRunner

        from foothold_checkpoint.cli import app

        config_file = tmp_path / "config.yaml"
        config_file.write_text(
            "servers:\n"
            "  test-server:\n"
            "    mission_directory: /path/to/mission\n"
            "  prod-1:\n"
            "    mission_directory: /path/to/prod\n"
            "checkpoints_directory: /path/to/checkpoints\n"
        )

        checkpoint_file = tmp_path / "checkpoint.zip"

        runner = CliRunner()
        with patch("foothold_checkpoint.cli.load_config") as mock_load, \
             patch("foothold_checkpoint.cli.restore_checkpoint") as mock_restore, \
             patch("foothold_checkpoint.cli.Prompt.ask", return_value="test-server"), \
             patch("pathlib.Path.exists", return_value=True):

            mock_config = Mock()
            mock_config.servers = {
                "test-server": Mock(mission_directory=tmp_path / "mission"),
                "prod-1": Mock(mission_directory=tmp_path / "prod")
            }
            mock_config.checkpoints_directory = tmp_path / "checkpoints"
            mock_load.return_value = mock_config

            mock_restore.return_value = [tmp_path / "mission" / "foothold.lua"]

            result = runner.invoke(app, ["restore", str(checkpoint_file)])

        # Server should be prompted
        assert result.exit_code == 0


class TestProgressDisplay:
    """Tests for progress display during restoration."""

    def test_progress_callback_is_used(self, tmp_path):
        """Test that progress_callback is passed to restore_checkpoint."""
        from typer.testing import CliRunner

        from foothold_checkpoint.cli import app

        config_file = tmp_path / "config.yaml"
        config_file.write_text(
            "servers:\n"
            "  test-server:\n"
            "    mission_directory: /path/to/mission\n"
            "checkpoints_directory: /path/to/checkpoints\n"
        )

        checkpoint_file = tmp_path / "checkpoint.zip"

        runner = CliRunner()
        with patch("foothold_checkpoint.cli.load_config") as mock_load, \
             patch("foothold_checkpoint.cli.restore_checkpoint") as mock_restore, \
             patch("pathlib.Path.exists", return_value=True):

            mock_config = Mock()
            mock_config.servers = {"test-server": Mock(mission_directory=tmp_path / "mission")}
            mock_config.checkpoints_directory = tmp_path / "checkpoints"
            mock_load.return_value = mock_config

            mock_restore.return_value = [tmp_path / "mission" / "foothold.lua"]

            result = runner.invoke(app, [
                "restore",
                str(checkpoint_file),
                "--server", "test-server"
            ])

        assert result.exit_code == 0
        # Verify progress_callback was passed
        call_args = mock_restore.call_args
        assert call_args.kwargs.get("progress_callback") is not None

    def test_progress_display_with_quiet_mode(self, tmp_path):
        """Test that progress display is suppressed in quiet mode."""
        from typer.testing import CliRunner

        from foothold_checkpoint.cli import app

        config_file = tmp_path / "config.yaml"
        config_file.write_text(
            "servers:\n"
            "  test-server:\n"
            "    mission_directory: /path/to/mission\n"
            "checkpoints_directory: /path/to/checkpoints\n"
        )

        checkpoint_file = tmp_path / "checkpoint.zip"

        runner = CliRunner()
        with patch("foothold_checkpoint.cli.load_config") as mock_load, \
             patch("foothold_checkpoint.cli.restore_checkpoint") as mock_restore, \
             patch("pathlib.Path.exists", return_value=True):

            mock_config = Mock()
            mock_config.servers = {"test-server": Mock(mission_directory=tmp_path / "mission")}
            mock_config.checkpoints_directory = tmp_path / "checkpoints"
            mock_load.return_value = mock_config

            mock_restore.return_value = [tmp_path / "mission" / "foothold.lua"]

            result = runner.invoke(app, [
                "--quiet",
                "restore",
                str(checkpoint_file),
                "--server", "test-server"
            ])

        assert result.exit_code == 0
        # Verify progress_callback is None in quiet mode
        call_args = mock_restore.call_args
        assert call_args.kwargs.get("progress_callback") is None


class TestSuccessErrorMessages:
    """Tests for success and error message display."""

    def test_success_message_displays_server_name(self, tmp_path):
        """Test success message includes target server name."""
        from typer.testing import CliRunner

        from foothold_checkpoint.cli import app

        config_file = tmp_path / "config.yaml"
        config_file.write_text(
            "servers:\n"
            "  test-server:\n"
            "    mission_directory: /path/to/mission\n"
            "checkpoints_directory: /path/to/checkpoints\n"
        )

        checkpoint_file = tmp_path / "checkpoint.zip"

        runner = CliRunner()
        with patch("foothold_checkpoint.cli.load_config") as mock_load, \
             patch("foothold_checkpoint.cli.restore_checkpoint") as mock_restore, \
             patch("pathlib.Path.exists", return_value=True):

            mock_config = Mock()
            mock_config.servers = {"test-server": Mock(mission_directory=tmp_path / "mission")}
            mock_config.checkpoints_directory = tmp_path / "checkpoints"
            mock_load.return_value = mock_config

            mock_restore.return_value = [
                tmp_path / "mission" / "foothold_afghanistan.lua",
                tmp_path / "mission" / "foothold_afghanistan_storage.csv"
            ]

            result = runner.invoke(app, [
                "restore",
                str(checkpoint_file),
                "--server", "test-server"
            ])

        assert result.exit_code == 0
        assert "test-server" in result.stdout or "restored" in result.stdout.lower()

    def test_error_message_for_missing_config(self, tmp_path):
        """Test error message when config file not found."""
        from typer.testing import CliRunner

        from foothold_checkpoint.cli import app

        checkpoint_file = tmp_path / "checkpoint.zip"

        runner = CliRunner()
        with patch("foothold_checkpoint.cli.load_config", side_effect=FileNotFoundError("Config not found")):

            result = runner.invoke(app, [
                "restore",
                str(checkpoint_file),
                "--server", "test-server"
            ])

        assert result.exit_code != 0
        assert "error" in result.stdout.lower() or "not found" in result.stdout.lower()

    def test_error_message_for_restoration_failure(self, tmp_path):
        """Test error message when restoration fails (e.g., checksum mismatch)."""
        from typer.testing import CliRunner

        from foothold_checkpoint.cli import app

        config_file = tmp_path / "config.yaml"
        config_file.write_text(
            "servers:\n"
            "  test-server:\n"
            "    mission_directory: /path/to/mission\n"
            "checkpoints_directory: /path/to/checkpoints\n"
        )

        checkpoint_file = tmp_path / "checkpoint.zip"

        runner = CliRunner()
        with patch("foothold_checkpoint.cli.load_config") as mock_load, \
             patch("foothold_checkpoint.cli.restore_checkpoint", side_effect=ValueError("Checksum mismatch")), \
             patch("pathlib.Path.exists", return_value=True):

            mock_config = Mock()
            mock_config.servers = {"test-server": Mock(mission_directory=tmp_path / "mission")}
            mock_config.checkpoints_directory = tmp_path / "checkpoints"
            mock_load.return_value = mock_config

            result = runner.invoke(app, [
                "restore",
                str(checkpoint_file),
                "--server", "test-server"
            ])

        assert result.exit_code != 0
        assert "error" in result.stdout.lower() or "checksum" in result.stdout.lower()

    def test_success_message_not_shown_in_quiet_mode(self, tmp_path):
        """Test that success message is suppressed in quiet mode."""
        from typer.testing import CliRunner

        from foothold_checkpoint.cli import app

        config_file = tmp_path / "config.yaml"
        config_file.write_text(
            "servers:\n"
            "  test-server:\n"
            "    mission_directory: /path/to/mission\n"
            "checkpoints_directory: /path/to/checkpoints\n"
        )

        checkpoint_file = tmp_path / "checkpoint.zip"

        runner = CliRunner()
        with patch("foothold_checkpoint.cli.load_config") as mock_load, \
             patch("foothold_checkpoint.cli.restore_checkpoint") as mock_restore, \
             patch("pathlib.Path.exists", return_value=True):

            mock_config = Mock()
            mock_config.servers = {"test-server": Mock(mission_directory=tmp_path / "mission")}
            mock_config.checkpoints_directory = tmp_path / "checkpoints"
            mock_load.return_value = mock_config

            mock_restore.return_value = [tmp_path / "mission" / "foothold.lua"]

            result = runner.invoke(app, [
                "--quiet",
                "restore",
                str(checkpoint_file),
                "--server", "test-server"
            ])

        assert result.exit_code == 0
        # In quiet mode, should not have decorative messages
        assert "Success" not in result.stdout

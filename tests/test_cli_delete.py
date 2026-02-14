"""Tests for CLI delete command."""

from unittest.mock import Mock, patch


class TestDeleteCommandBasic:
    """Tests for delete command basic functionality."""

    def test_delete_with_force_flag(self, tmp_path):
        """Test delete command with --force flag (no confirmation)."""
        from typer.testing import CliRunner

        from foothold_checkpoint.cli import app

        checkpoint_file = "afghanistan_2024-02-14_10-30-00.zip"

        runner = CliRunner()
        with (
            patch("foothold_checkpoint.cli.load_config") as mock_load,
            patch("foothold_checkpoint.cli.delete_checkpoint") as mock_delete,
        ):

            mock_config = Mock()
            mock_config.checkpoints_dir = tmp_path / "checkpoints"
            mock_load.return_value = mock_config

            # Mock deleted checkpoint metadata
            mock_delete.return_value = {
                "campaign_name": "afghanistan",
                "server_name": "test-server",
                "created_at": "2024-02-14T10:30:00",
            }

            result = runner.invoke(app, ["delete", checkpoint_file, "--force"])

        assert result.exit_code == 0
        assert "deleted" in result.stdout.lower() or "success" in result.stdout.lower()
        # Verify force=True was passed and confirm_callback=None
        call_args = mock_delete.call_args
        assert call_args.kwargs.get("force") is True
        assert call_args.kwargs.get("confirm_callback") is None

    def test_delete_with_confirmation_accept(self, tmp_path):
        """Test delete command with confirmation prompt (user accepts)."""
        from typer.testing import CliRunner

        from foothold_checkpoint.cli import app

        checkpoint_file = "afghanistan_2024-02-14_10-30-00.zip"

        runner = CliRunner()
        with (
            patch("foothold_checkpoint.cli.load_config") as mock_load,
            patch("foothold_checkpoint.cli.delete_checkpoint") as mock_delete,
        ):

            mock_config = Mock()
            mock_config.checkpoints_dir = tmp_path / "checkpoints"
            mock_load.return_value = mock_config

            # Mock metadata and deletion
            mock_delete.return_value = {
                "campaign_name": "afghanistan",
                "server_name": "test-server",
                "created_at": "2024-02-14T10:30:00",
            }

            # Simulate user accepting deletion
            result = runner.invoke(app, ["delete", checkpoint_file], input="y\n")

        assert result.exit_code == 0
        assert "deleted" in result.stdout.lower() or "success" in result.stdout.lower()
        # Verify confirm_callback was provided
        call_args = mock_delete.call_args
        assert call_args.kwargs.get("confirm_callback") is not None

    def test_delete_with_confirmation_cancel(self, tmp_path):
        """Test delete command with confirmation prompt (user cancels)."""
        from typer.testing import CliRunner

        from foothold_checkpoint.cli import app

        checkpoint_file = "afghanistan_2024-02-14_10-30-00.zip"

        runner = CliRunner()
        with (
            patch("foothold_checkpoint.cli.load_config") as mock_load,
            patch("foothold_checkpoint.cli.delete_checkpoint") as mock_delete,
        ):

            mock_config = Mock()
            mock_config.checkpoints_dir = tmp_path / "checkpoints"
            mock_load.return_value = mock_config

            # Mock delete returning None (user cancelled)
            mock_delete.return_value = None

            # Simulate user cancelling deletion
            result = runner.invoke(app, ["delete", checkpoint_file], input="n\n")

        assert result.exit_code == 0
        assert "cancel" in result.stdout.lower() or "aborted" in result.stdout.lower()


class TestDeleteCommandInteractive:
    """Tests for delete command interactive mode."""

    def test_delete_without_filename_prompts(self, tmp_path):
        """Test that omitting filename triggers interactive checkpoint selection."""
        from typer.testing import CliRunner

        from foothold_checkpoint.cli import app

        runner = CliRunner()
        with (
            patch("foothold_checkpoint.cli.load_config") as mock_load,
            patch("foothold_checkpoint.cli.list_checkpoints") as mock_list,
            patch("foothold_checkpoint.cli.delete_checkpoint") as mock_delete,
        ):

            mock_config = Mock()
            mock_config.checkpoints_dir = tmp_path / "checkpoints"
            mock_load.return_value = mock_config

            mock_list.return_value = [
                {
                    "filename": "afghanistan_2024-02-14_10-30-00.zip",
                    "campaign": "afghanistan",
                    "server": "test-server",
                    "timestamp": "2024-02-14T10:30:00",
                    "size_bytes": 1048576,
                    "size_human": "1.0 MB",
                    "name": None,
                    "comment": None,
                },
            ]

            mock_delete.return_value = {
                "campaign_name": "afghanistan",
                "server_name": "test-server",
                "created_at": "2024-02-14T10:30:00",
            }

            # Select checkpoint 1 and accept deletion
            result = runner.invoke(app, ["delete"], input="1\ny\n")

        assert result.exit_code == 0
        mock_list.assert_called_once()
        mock_delete.assert_called_once()

    def test_delete_interactive_no_checkpoints(self, tmp_path):
        """Test error when no checkpoints available in interactive mode."""
        from typer.testing import CliRunner

        from foothold_checkpoint.cli import app

        runner = CliRunner()
        with (
            patch("foothold_checkpoint.cli.load_config") as mock_load,
            patch("foothold_checkpoint.cli.list_checkpoints") as mock_list,
        ):

            mock_config = Mock()
            mock_config.checkpoints_dir = tmp_path / "checkpoints"
            mock_load.return_value = mock_config

            mock_list.return_value = []

            result = runner.invoke(app, ["delete"])

        assert result.exit_code != 0
        assert "no checkpoints" in result.stdout.lower()


class TestDeleteCommandMetadataDisplay:
    """Tests for checkpoint metadata display before confirmation."""

    def test_metadata_displayed_before_confirmation(self, tmp_path):
        """Test that checkpoint metadata is displayed before confirmation prompt."""
        from typer.testing import CliRunner

        from foothold_checkpoint.cli import app

        checkpoint_file = "afghanistan_2024-02-14_10-30-00.zip"

        runner = CliRunner()
        with (
            patch("foothold_checkpoint.cli.load_config") as mock_load,
            patch("foothold_checkpoint.cli.delete_checkpoint") as mock_delete,
            patch("pathlib.Path.exists", return_value=True),
            patch("zipfile.ZipFile") as mock_zipfile,
        ):

            mock_config = Mock()
            mock_config.checkpoints_dir = tmp_path / "checkpoints"
            mock_load.return_value = mock_config

            # Mock reading metadata from ZIP
            mock_zip_instance = Mock()
            mock_zipfile.return_value.__enter__.return_value = mock_zip_instance
            mock_zip_instance.read.return_value = b'{"campaign_name": "afghanistan", "server_name": "test-server", "created_at": "2024-02-14T10:30:00"}'

            mock_delete.return_value = {
                "campaign_name": "afghanistan",
                "server_name": "test-server",
                "created_at": "2024-02-14T10:30:00",
            }

            result = runner.invoke(app, ["delete", checkpoint_file], input="y\n")

        assert result.exit_code == 0
        # Output should contain metadata elements
        assert "afghanistan" in result.stdout


class TestDeleteCommandErrors:
    """Tests for error handling in delete command."""

    def test_delete_nonexistent_checkpoint(self, tmp_path):
        """Test error when checkpoint file doesn't exist."""
        from typer.testing import CliRunner

        from foothold_checkpoint.cli import app

        runner = CliRunner()
        with (
            patch("foothold_checkpoint.cli.load_config") as mock_load,
            patch("foothold_checkpoint.cli.delete_checkpoint") as mock_delete,
        ):

            mock_config = Mock()
            mock_config.checkpoints_dir = tmp_path / "checkpoints"
            mock_load.return_value = mock_config

            mock_delete.side_effect = FileNotFoundError("Checkpoint file not found")

            result = runner.invoke(app, ["delete", "nonexistent.zip", "--force"])

        assert result.exit_code != 0
        assert "not found" in result.stdout.lower() or "error" in result.stdout.lower()

    def test_delete_invalid_checkpoint(self, tmp_path):
        """Test error when file is not a valid checkpoint."""
        from typer.testing import CliRunner

        from foothold_checkpoint.cli import app

        runner = CliRunner()
        with (
            patch("foothold_checkpoint.cli.load_config") as mock_load,
            patch("foothold_checkpoint.cli.delete_checkpoint") as mock_delete,
        ):

            mock_config = Mock()
            mock_config.checkpoints_dir = tmp_path / "checkpoints"
            mock_load.return_value = mock_config

            mock_delete.side_effect = ValueError("Not a valid checkpoint file")

            result = runner.invoke(app, ["delete", "invalid.txt", "--force"])

        assert result.exit_code != 0
        assert "invalid" in result.stdout.lower() or "error" in result.stdout.lower()

    def test_delete_missing_config(self, tmp_path):
        """Test error when config file is not found."""
        from typer.testing import CliRunner

        from foothold_checkpoint.cli import app

        runner = CliRunner()
        with patch("foothold_checkpoint.cli.load_config") as mock_load:
            mock_load.side_effect = FileNotFoundError("Config file not found")

            result = runner.invoke(app, ["delete", "checkpoint.zip", "--force"])

        assert result.exit_code != 0
        assert "not found" in result.stdout.lower() or "error" in result.stdout.lower()


class TestDeleteCommandQuietMode:
    """Tests for quiet mode in delete command."""

    def test_quiet_mode_suppresses_confirmation(self, tmp_path):
        """Test that quiet mode acts like --force (no prompts)."""
        from typer.testing import CliRunner

        from foothold_checkpoint.cli import app

        checkpoint_file = "afghanistan_2024-02-14_10-30-00.zip"

        runner = CliRunner()
        with (
            patch("foothold_checkpoint.cli.load_config") as mock_load,
            patch("foothold_checkpoint.cli.delete_checkpoint") as mock_delete,
        ):

            mock_config = Mock()
            mock_config.checkpoints_dir = tmp_path / "checkpoints"
            mock_load.return_value = mock_config

            mock_delete.return_value = {
                "campaign_name": "afghanistan",
                "server_name": "test-server",
                "created_at": "2024-02-14T10:30:00",
            }

            result = runner.invoke(app, ["--quiet", "delete", checkpoint_file])

        assert result.exit_code == 0
        # In quiet mode, minimal output
        lines = [line for line in result.stdout.strip().split("\n") if line.strip()]
        assert len(lines) <= 2  # At most 1-2 lines of output

    def test_quiet_mode_still_shows_errors(self, tmp_path):
        """Test that errors are shown even in quiet mode."""
        from typer.testing import CliRunner

        from foothold_checkpoint.cli import app

        runner = CliRunner()
        with (
            patch("foothold_checkpoint.cli.load_config") as mock_load,
            patch("foothold_checkpoint.cli.delete_checkpoint") as mock_delete,
        ):

            mock_config = Mock()
            mock_config.checkpoints_dir = tmp_path / "checkpoints"
            mock_load.return_value = mock_config

            mock_delete.side_effect = FileNotFoundError("Checkpoint file not found")

            result = runner.invoke(app, ["--quiet", "delete", "nonexistent.zip"])

        assert result.exit_code != 0
        assert result.stdout.strip() != ""  # Error message should be present

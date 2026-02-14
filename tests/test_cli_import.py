"""Tests for CLI import command."""

from unittest.mock import Mock, patch


class TestImportCommandWithFlags:
    """Tests for import command with all flags provided."""

    def test_import_with_all_flags(self, tmp_path):
        """Test import command with all required flags."""
        from typer.testing import CliRunner

        from foothold_checkpoint.cli import app

        source_dir = tmp_path / "source"
        source_dir.mkdir()

        runner = CliRunner()
        with patch("foothold_checkpoint.cli.load_config") as mock_load, \
             patch("foothold_checkpoint.cli.import_checkpoint") as mock_import, \
             patch("foothold_checkpoint.cli.group_campaign_files") as mock_group:

            mock_config = Mock()
            mock_config.checkpoints_directory = tmp_path / "checkpoints"
            mock_config.servers = {"test-server": Mock()}
            mock_load.return_value = mock_config

            # Mock campaign detection
            mock_group.return_value = {"afghanistan": ["foothold_afghanistan.lua"]}

            checkpoint_path = tmp_path / "checkpoints" / "afghanistan_2024-02-14.zip"
            mock_import.return_value = checkpoint_path

            result = runner.invoke(app, [
                "import",
                str(source_dir),
                "--server", "test-server",
                "--campaign", "afghanistan"
            ], input="y\n")

        assert result.exit_code == 0
        assert "success" in result.stdout.lower() or "imported" in result.stdout.lower()
        mock_import.assert_called_once()
        call_args = mock_import.call_args
        assert call_args.kwargs["campaign_name"] == "afghanistan"
        assert call_args.kwargs["server_name"] == "test-server"

    def test_import_with_optional_metadata(self, tmp_path):
        """Test import with --name and --comment flags."""
        from typer.testing import CliRunner

        from foothold_checkpoint.cli import app

        source_dir = tmp_path / "source"
        source_dir.mkdir()

        runner = CliRunner()
        with patch("foothold_checkpoint.cli.load_config") as mock_load, \
             patch("foothold_checkpoint.cli.import_checkpoint") as mock_import, \
             patch("foothold_checkpoint.cli.group_campaign_files") as mock_group:

            mock_config = Mock()
            mock_config.checkpoints_directory = tmp_path / "checkpoints"
            mock_config.servers = {"test-server": Mock()}
            mock_load.return_value = mock_config

            # Mock campaign detection
            mock_group.return_value = {"afghanistan": ["foothold_afghanistan.lua"]}

            checkpoint_path = tmp_path / "checkpoints" / "afghanistan_2024-02-14.zip"
            mock_import.return_value = checkpoint_path

            result = runner.invoke(app, [
                "import",
                str(source_dir),
                "--server", "test-server",
                "--campaign", "afghanistan",
                "--name", "Test Import",
                "--comment", "Test comment"
            ], input="y\n")

        assert result.exit_code == 0
        call_args = mock_import.call_args
        assert call_args.kwargs["name"] == "Test Import"
        assert call_args.kwargs["comment"] == "Test comment"


class TestImportCommandPrompts:
    """Tests for prompting missing parameters."""

    def test_import_prompts_for_server_when_missing(self, tmp_path):
        """Test that missing --server triggers prompt."""
        from typer.testing import CliRunner

        from foothold_checkpoint.cli import app

        source_dir = tmp_path / "source"
        source_dir.mkdir()

        runner = CliRunner()
        with patch("foothold_checkpoint.cli.load_config") as mock_load, \
             patch("foothold_checkpoint.cli.import_checkpoint") as mock_import, \
             patch("foothold_checkpoint.cli.group_campaign_files") as mock_group:

            mock_config = Mock()
            mock_config.checkpoints_directory = tmp_path / "checkpoints"
            mock_config.servers = {"test-server": Mock(), "prod-1": Mock()}
            mock_load.return_value = mock_config

            # Mock campaign detection
            mock_group.return_value = {"afghanistan": ["foothold_afghanistan.lua"]}

            checkpoint_path = tmp_path / "checkpoints" / "afghanistan_2024-02-14.zip"
            mock_import.return_value = checkpoint_path

            # Provide server choice and accept import
            result = runner.invoke(app, [
                "import",
                str(source_dir),
                "--campaign", "afghanistan"
            ], input="test-server\ny\n")

        assert result.exit_code == 0

    def test_import_prompts_for_campaign_when_missing(self, tmp_path):
        """Test that missing --campaign triggers detection and prompt."""
        from typer.testing import CliRunner

        from foothold_checkpoint.cli import app

        source_dir = tmp_path / "source"
        source_dir.mkdir()

        runner = CliRunner()
        with patch("foothold_checkpoint.cli.load_config") as mock_load, \
             patch("foothold_checkpoint.cli.import_checkpoint") as mock_import, \
             patch("foothold_checkpoint.cli.group_campaign_files") as mock_group:

            mock_config = Mock()
            mock_config.checkpoints_directory = tmp_path / "checkpoints"
            mock_config.servers = {"test-server": Mock()}
            mock_load.return_value = mock_config

            # Mock multiple campaigns detected
            mock_group.return_value = {
                "afghanistan": ["foothold_afghanistan.lua"],
                "syria": ["foothold_syria.lua"]
            }

            checkpoint_path = tmp_path / "checkpoints" / "afghanistan_2024-02-14.zip"
            mock_import.return_value = checkpoint_path

            # Select campaign 1 (afghanistan), select server, accept import
            result = runner.invoke(app, [
                "import",
                str(source_dir),
                "--server", "test-server"
            ], input="1\ny\n")

        assert result.exit_code == 0

    def test_import_auto_detects_single_campaign(self, tmp_path):
        """Test that single campaign is auto-selected without prompt."""
        from typer.testing import CliRunner

        from foothold_checkpoint.cli import app

        source_dir = tmp_path / "source"
        source_dir.mkdir()

        runner = CliRunner()
        with patch("foothold_checkpoint.cli.load_config") as mock_load, \
             patch("foothold_checkpoint.cli.import_checkpoint") as mock_import, \
             patch("foothold_checkpoint.cli.group_campaign_files") as mock_group:

            mock_config = Mock()
            mock_config.checkpoints_directory = tmp_path / "checkpoints"
            mock_config.servers = {"test-server": Mock()}
            mock_load.return_value = mock_config

            # Mock single campaign detected
            mock_group.return_value = {"afghanistan": ["foothold_afghanistan.lua"]}

            checkpoint_path = tmp_path / "checkpoints" / "afghanistan_2024-02-14.zip"
            mock_import.return_value = checkpoint_path

            # Just confirm import (no campaign prompt expected)
            result = runner.invoke(app, [
                "import",
                str(source_dir),
                "--server", "test-server"
            ], input="y\n")

        assert result.exit_code == 0
        call_args = mock_import.call_args
        assert call_args.kwargs["campaign_name"] == "afghanistan"


class TestImportCommandConfirmation:
    """Tests for import confirmation flow."""

    def test_import_shows_summary_before_confirmation(self, tmp_path):
        """Test that import summary is displayed before confirmation."""
        from typer.testing import CliRunner

        from foothold_checkpoint.cli import app

        source_dir = tmp_path / "source"
        source_dir.mkdir()

        runner = CliRunner()
        with patch("foothold_checkpoint.cli.load_config") as mock_load, \
             patch("foothold_checkpoint.cli.import_checkpoint") as mock_import, \
             patch("foothold_checkpoint.cli.group_campaign_files") as mock_group:

            mock_config = Mock()
            mock_config.checkpoints_directory = tmp_path / "checkpoints"
            mock_config.servers = {"test-server": Mock()}
            mock_load.return_value = mock_config

            mock_group.return_value = {"afghanistan": ["foothold_afghanistan.lua"]}

            checkpoint_path = tmp_path / "checkpoints" / "afghanistan_2024-02-14.zip"
            mock_import.return_value = checkpoint_path

            result = runner.invoke(app, [
                "import",
                str(source_dir),
                "--server", "test-server",
                "--campaign", "afghanistan"
            ], input="y\n")

        assert result.exit_code == 0
        # Summary should show campaign and server
        assert "afghanistan" in result.stdout
        assert "test-server" in result.stdout

    def test_import_cancelled_by_user(self, tmp_path):
        """Test that user can cancel import at confirmation prompt."""
        from typer.testing import CliRunner

        from foothold_checkpoint.cli import app

        source_dir = tmp_path / "source"
        source_dir.mkdir()

        runner = CliRunner()
        with patch("foothold_checkpoint.cli.load_config") as mock_load, \
             patch("foothold_checkpoint.cli.import_checkpoint") as mock_import, \
             patch("foothold_checkpoint.cli.group_campaign_files") as mock_group:

            mock_config = Mock()
            mock_config.checkpoints_directory = tmp_path / "checkpoints"
            mock_config.servers = {"test-server": Mock()}
            mock_load.return_value = mock_config

            mock_group.return_value = {"afghanistan": ["foothold_afghanistan.lua"]}

            # User cancels
            result = runner.invoke(app, [
                "import",
                str(source_dir),
                "--server", "test-server",
                "--campaign", "afghanistan"
            ], input="n\n")

        assert result.exit_code == 0
        assert "cancel" in result.stdout.lower() or "aborted" in result.stdout.lower()
        mock_import.assert_not_called()


class TestImportCommandProgressAndWarnings:
    """Tests for progress display and warnings."""

    def test_import_with_warnings_displayed(self, tmp_path):
        """Test that warnings are displayed when files are missing."""
        from typer.testing import CliRunner

        from foothold_checkpoint.cli import app

        source_dir = tmp_path / "source"
        source_dir.mkdir()

        runner = CliRunner()
        with patch("foothold_checkpoint.cli.load_config") as mock_load, \
             patch("foothold_checkpoint.cli.import_checkpoint") as mock_import, \
             patch("foothold_checkpoint.cli.group_campaign_files") as mock_group:

            mock_config = Mock()
            mock_config.checkpoints_directory = tmp_path / "checkpoints"
            mock_config.servers = {"test-server": Mock()}
            mock_load.return_value = mock_config

            mock_group.return_value = {"afghanistan": ["foothold_afghanistan.lua"]}

            checkpoint_path = tmp_path / "checkpoints" / "afghanistan_2024-02-14.zip"
            warnings = [
                "Missing storage file: foothold_afghanistan_storage.csv",
                "Ranks file not found: Foothold_Ranks.lua"
            ]
            mock_import.return_value = (checkpoint_path, warnings)

            result = runner.invoke(app, [
                "import",
                str(source_dir),
                "--server", "test-server",
                "--campaign", "afghanistan"
            ], input="y\n")

        assert result.exit_code == 0
        # Warnings should be displayed in yellow
        assert "warning" in result.stdout.lower() or "missing" in result.stdout.lower()

    def test_import_without_warnings(self, tmp_path):
        """Test successful import without warnings."""
        from typer.testing import CliRunner

        from foothold_checkpoint.cli import app

        source_dir = tmp_path / "source"
        source_dir.mkdir()

        runner = CliRunner()
        with patch("foothold_checkpoint.cli.load_config") as mock_load, \
             patch("foothold_checkpoint.cli.import_checkpoint") as mock_import, \
             patch("foothold_checkpoint.cli.group_campaign_files") as mock_group:

            mock_config = Mock()
            mock_config.checkpoints_directory = tmp_path / "checkpoints"
            mock_config.servers = {"test-server": Mock()}
            mock_load.return_value = mock_config

            mock_group.return_value = {"afghanistan": ["foothold_afghanistan.lua"]}

            checkpoint_path = tmp_path / "checkpoints" / "afghanistan_2024-02-14.zip"
            # Return just path (no warnings)
            mock_import.return_value = checkpoint_path

            result = runner.invoke(app, [
                "import",
                str(source_dir),
                "--server", "test-server",
                "--campaign", "afghanistan"
            ], input="y\n")

        assert result.exit_code == 0
        assert "success" in result.stdout.lower()


class TestImportCommandErrors:
    """Tests for error handling in import command."""

    def test_import_nonexistent_directory(self, tmp_path):
        """Test error when source directory doesn't exist."""
        from typer.testing import CliRunner

        from foothold_checkpoint.cli import app

        runner = CliRunner()
        with patch("foothold_checkpoint.cli.load_config") as mock_load:
            mock_config = Mock()
            mock_config.checkpoints_directory = tmp_path / "checkpoints"
            mock_load.return_value = mock_config

            result = runner.invoke(app, [
                "import",
                str(tmp_path / "nonexistent"),
                "--server", "test-server",
                "--campaign", "afghanistan"
            ], input="y\n")

        assert result.exit_code != 0
        assert "not found" in result.stdout.lower() or "error" in result.stdout.lower()

    def test_import_no_campaigns_found(self, tmp_path):
        """Test error when no campaign files found in directory."""
        from typer.testing import CliRunner

        from foothold_checkpoint.cli import app

        source_dir = tmp_path / "source"
        source_dir.mkdir()

        runner = CliRunner()
        with patch("foothold_checkpoint.cli.load_config") as mock_load, \
             patch("foothold_checkpoint.cli.group_campaign_files") as mock_group:

            mock_config = Mock()
            mock_config.checkpoints_directory = tmp_path / "checkpoints"
            mock_config.servers = {"test-server": Mock()}
            mock_load.return_value = mock_config

            # No campaigns detected
            mock_group.return_value = {}

            result = runner.invoke(app, [
                "import",
                str(source_dir),
                "--server", "test-server"
            ])

        assert result.exit_code != 0
        assert "no campaign" in result.stdout.lower() or "not found" in result.stdout.lower()

    def test_import_invalid_campaign_name(self, tmp_path):
        """Test error when specified campaign not found in directory."""
        from typer.testing import CliRunner

        from foothold_checkpoint.cli import app

        source_dir = tmp_path / "source"
        source_dir.mkdir()

        runner = CliRunner()
        with patch("foothold_checkpoint.cli.load_config") as mock_load, \
             patch("foothold_checkpoint.cli.import_checkpoint") as mock_import:

            mock_config = Mock()
            mock_config.checkpoints_directory = tmp_path / "checkpoints"
            mock_config.servers = {"test-server": Mock()}
            mock_load.return_value = mock_config

            mock_import.side_effect = ValueError("No campaign files found for campaign 'invalid'")

            result = runner.invoke(app, [
                "import",
                str(source_dir),
                "--server", "test-server",
                "--campaign", "invalid"
            ], input="y\n")

        assert result.exit_code != 0
        assert "not found" in result.stdout.lower() or "error" in result.stdout.lower()


class TestImportCommandQuietMode:
    """Tests for quiet mode in import command."""

    def test_quiet_mode_skips_confirmation(self, tmp_path):
        """Test that quiet mode skips confirmation prompt."""
        from typer.testing import CliRunner

        from foothold_checkpoint.cli import app

        source_dir = tmp_path / "source"
        source_dir.mkdir()

        runner = CliRunner()
        with patch("foothold_checkpoint.cli.load_config") as mock_load, \
             patch("foothold_checkpoint.cli.import_checkpoint") as mock_import, \
             patch("foothold_checkpoint.cli.group_campaign_files") as mock_group:

            mock_config = Mock()
            mock_config.checkpoints_directory = tmp_path / "checkpoints"
            mock_config.servers = {"test-server": Mock()}
            mock_load.return_value = mock_config

            mock_group.return_value = {"afghanistan": ["foothold_afghanistan.lua"]}

            checkpoint_path = tmp_path / "checkpoints" / "afghanistan_2024-02-14.zip"
            mock_import.return_value = checkpoint_path

            # No input needed in quiet mode
            result = runner.invoke(app, [
                "--quiet",
                "import",
                str(source_dir),
                "--server", "test-server",
                "--campaign", "afghanistan"
            ])

        assert result.exit_code == 0
        mock_import.assert_called_once()

    def test_quiet_mode_outputs_checkpoint_path(self, tmp_path):
        """Test that quiet mode outputs only checkpoint path."""
        from typer.testing import CliRunner

        from foothold_checkpoint.cli import app

        source_dir = tmp_path / "source"
        source_dir.mkdir()

        runner = CliRunner()
        with patch("foothold_checkpoint.cli.load_config") as mock_load, \
             patch("foothold_checkpoint.cli.import_checkpoint") as mock_import, \
             patch("foothold_checkpoint.cli.group_campaign_files") as mock_group:

            mock_config = Mock()
            mock_config.checkpoints_directory = tmp_path / "checkpoints"
            mock_config.servers = {"test-server": Mock()}
            mock_load.return_value = mock_config

            mock_group.return_value = {"afghanistan": ["foothold_afghanistan.lua"]}

            checkpoint_path = tmp_path / "checkpoints" / "afghanistan_2024-02-14.zip"
            mock_import.return_value = checkpoint_path

            result = runner.invoke(app, [
                "--quiet",
                "import",
                str(source_dir),
                "--server", "test-server",
                "--campaign", "afghanistan"
            ])

        assert result.exit_code == 0
        assert checkpoint_path.name in result.stdout

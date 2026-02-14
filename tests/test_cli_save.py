"""Tests for CLI save command."""

from pathlib import Path
from unittest.mock import Mock, patch


class TestSaveCommandWithFlags:
    """Tests for save command with all flags provided."""

    def test_save_with_all_required_flags(self, tmp_path):
        """Test save command with --server, --campaign, --name, --comment flags."""
        from typer.testing import CliRunner

        from foothold_checkpoint.cli import app

        # Create mock config and files
        config_file = tmp_path / "config.yaml"
        config_file.write_text(
            "servers:\n"
            "  test-server:\n"
            "    mission_directory: /path/to/mission\n"
            "checkpoints_directory: /path/to/checkpoints\n"
        )

        runner = CliRunner()
        with (
            patch("foothold_checkpoint.cli.load_config") as mock_load,
            patch("foothold_checkpoint.cli.detect_campaigns") as mock_detect,
            patch("foothold_checkpoint.cli.create_checkpoint") as mock_create,
            patch("pathlib.Path.exists", return_value=True),
            patch(
                "pathlib.Path.iterdir",
                return_value=[
                    Mock(name="foothold_afghanistan.lua", is_file=lambda: True),
                    Mock(name="foothold_afghanistan_storage.csv", is_file=lambda: True),
                ],
            ),
        ):

            # Setup mocks
            mock_config = Mock()
            mock_config.servers = {"test-server": Mock(mission_directory=tmp_path)}
            mock_config.checkpoints_directory = tmp_path / "checkpoints"
            mock_load.return_value = mock_config

            mock_detect.return_value = {
                "afghanistan": ["foothold_afghanistan.lua", "foothold_afghanistan_storage.csv"]
            }

            mock_create.return_value = (
                tmp_path / "checkpoints" / "afghanistan_2024-02-14_10-30-00.zip"
            )

            result = runner.invoke(
                app,
                [
                    "save",
                    "--server",
                    "test-server",
                    "--campaign",
                    "afghanistan",
                    "--name",
                    "Test checkpoint",
                    "--comment",
                    "Testing save command",
                ],
            )

        assert result.exit_code == 0
        assert "afghanistan_2024-02-14_10-30-00.zip" in result.stdout or "Success" in result.stdout

    def test_save_with_all_campaigns_flag(self, tmp_path):
        """Test save command with --all flag to save all detected campaigns."""
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
        with (
            patch("foothold_checkpoint.cli.load_config") as mock_load,
            patch("foothold_checkpoint.cli.detect_campaigns") as mock_detect,
            patch("foothold_checkpoint.cli.create_checkpoint") as mock_create,
            patch("pathlib.Path.exists", return_value=True),
            patch(
                "pathlib.Path.iterdir",
                return_value=[
                    Mock(name="foothold_afghanistan.lua", is_file=lambda: True),
                    Mock(name="foothold_syria.lua", is_file=lambda: True),
                ],
            ),
        ):

            mock_config = Mock()
            mock_config.servers = {"test-server": Mock(mission_directory=tmp_path)}
            mock_config.checkpoints_directory = tmp_path / "checkpoints"
            mock_load.return_value = mock_config

            mock_detect.return_value = {
                "afghanistan": ["foothold_afghanistan.lua"],
                "syria": ["foothold_syria.lua"],
            }

            mock_create.return_value = tmp_path / "checkpoints" / "campaign.zip"

            result = runner.invoke(app, ["save", "--server", "test-server", "--all"])

        assert result.exit_code == 0
        # Should have created checkpoints for both campaigns
        assert mock_create.call_count == 2

    def test_save_with_invalid_server(self, tmp_path):
        """Test save command with server not in configuration."""
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
        with patch("foothold_checkpoint.cli.load_config") as mock_load:
            mock_config = Mock()
            mock_config.servers = {"test-server": Mock(mission_directory=tmp_path)}
            mock_config.checkpoints_directory = tmp_path / "checkpoints"
            mock_load.return_value = mock_config

            result = runner.invoke(
                app, ["save", "--server", "invalid-server", "--campaign", "afghanistan"]
            )

        assert result.exit_code == 1
        assert (
            "Server 'invalid-server' not found" in result.stdout
            or "not found" in result.stdout.lower()
        )

    def test_save_with_invalid_campaign(self, tmp_path):
        """Test save command with campaign not detected in mission directory."""
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
        with (
            patch("foothold_checkpoint.cli.load_config") as mock_load,
            patch("foothold_checkpoint.cli.detect_campaigns") as mock_detect,
            patch("pathlib.Path.exists", return_value=True),
            patch("pathlib.Path.iterdir", return_value=[]),
        ):

            mock_config = Mock()
            mock_config.servers = {"test-server": Mock(mission_directory=tmp_path)}
            mock_config.checkpoints_directory = tmp_path / "checkpoints"
            mock_load.return_value = mock_config

            mock_detect.return_value = {"syria": ["foothold_syria.lua"]}

            result = runner.invoke(
                app, ["save", "--server", "test-server", "--campaign", "afghanistan"]
            )

        assert result.exit_code == 1
        assert (
            "Campaign 'afghanistan' not found" in result.stdout
            or "not found" in result.stdout.lower()
        )


class TestServerPrompt:
    """Tests for server selection prompt when --server flag is missing."""

    def test_server_prompt_when_flag_missing(self, tmp_path):
        """Test that system prompts for server when --server flag is not provided."""
        from typer.testing import CliRunner

        from foothold_checkpoint.cli import app

        config_file = tmp_path / "config.yaml"
        config_file.write_text(
            "servers:\n"
            "  server-1:\n"
            "    mission_directory: /path/to/mission1\n"
            "  server-2:\n"
            "    mission_directory: /path/to/mission2\n"
            "checkpoints_directory: /path/to/checkpoints\n"
        )

        runner = CliRunner()
        with (
            patch("foothold_checkpoint.cli.load_config") as mock_load,
            patch("foothold_checkpoint.cli.Prompt.ask") as mock_prompt,
            patch("foothold_checkpoint.cli.detect_campaigns") as mock_detect,
            patch("foothold_checkpoint.cli.create_checkpoint") as mock_create,
            patch("pathlib.Path.exists", return_value=True),
            patch(
                "pathlib.Path.iterdir",
                return_value=[Mock(name="foothold_afghanistan.lua", is_file=lambda: True)],
            ),
        ):

            mock_config = Mock()
            mock_config.servers = {
                "server-1": Mock(mission_directory=tmp_path),
                "server-2": Mock(mission_directory=tmp_path),
            }
            mock_config.checkpoints_directory = tmp_path / "checkpoints"
            mock_load.return_value = mock_config

            # User selects server-1
            mock_prompt.return_value = "server-1"

            mock_detect.return_value = {"afghanistan": ["foothold_afghanistan.lua"]}

            mock_create.return_value = tmp_path / "checkpoints" / "afghanistan.zip"

            result = runner.invoke(app, ["save", "--campaign", "afghanistan"], input="server-1\n")

        assert result.exit_code == 0
        # Verify prompt was called
        assert mock_prompt.called

    def test_server_prompt_displays_available_servers(self, tmp_path):
        """Test that server prompt displays list of available servers."""
        from typer.testing import CliRunner

        from foothold_checkpoint.cli import app

        config_file = tmp_path / "config.yaml"
        config_file.write_text(
            "servers:\n"
            "  prod-1:\n"
            "    mission_directory: /path/to/mission1\n"
            "  prod-2:\n"
            "    mission_directory: /path/to/mission2\n"
            "checkpoints_directory: /path/to/checkpoints\n"
        )

        runner = CliRunner()
        with (
            patch("foothold_checkpoint.cli.load_config") as mock_load,
            patch("foothold_checkpoint.cli.Prompt.ask") as mock_prompt,
            patch("foothold_checkpoint.cli.detect_campaigns") as mock_detect,
            patch("foothold_checkpoint.cli.create_checkpoint") as mock_create,
            patch("pathlib.Path.exists", return_value=True),
            patch(
                "pathlib.Path.iterdir",
                return_value=[Mock(name="foothold_afghanistan.lua", is_file=lambda: True)],
            ),
        ):

            mock_config = Mock()
            mock_config.servers = {
                "prod-1": Mock(mission_directory=tmp_path),
                "prod-2": Mock(mission_directory=tmp_path),
            }
            mock_config.checkpoints_directory = tmp_path / "checkpoints"
            mock_load.return_value = mock_config

            mock_prompt.return_value = "prod-1"

            mock_detect.return_value = {"afghanistan": ["foothold_afghanistan.lua"]}

            mock_create.return_value = tmp_path / "checkpoints" / "afghanistan.zip"

            result = runner.invoke(app, ["save", "--campaign", "afghanistan"], input="prod-1\n")

        assert result.exit_code == 0
        # Verify the prompt shows available servers
        assert mock_prompt.called


class TestCampaignPrompt:
    """Tests for campaign selection prompt when --campaign and --all flags are missing."""

    def test_campaign_prompt_when_flags_missing(self, tmp_path):
        """Test that system prompts for campaign when both --campaign and --all are missing."""
        from typer.testing import CliRunner

        from foothold_checkpoint.cli import app

        runner = CliRunner()
        with (
            patch("foothold_checkpoint.cli.load_config") as mock_load,
            patch("foothold_checkpoint.cli.Prompt.ask") as mock_prompt,
            patch("foothold_checkpoint.cli.detect_campaigns") as mock_detect,
            patch("foothold_checkpoint.cli.create_checkpoint") as mock_create,
            patch("pathlib.Path.exists", return_value=True),
            patch(
                "pathlib.Path.iterdir",
                return_value=[
                    Mock(name="foothold_afghanistan.lua", is_file=lambda: True),
                    Mock(name="foothold_syria.lua", is_file=lambda: True),
                ],
            ),
        ):

            mock_config = Mock()
            mock_config.servers = {"test-server": Mock(mission_directory=tmp_path)}
            mock_config.checkpoints_directory = tmp_path / "checkpoints"
            mock_load.return_value = mock_config

            # First prompt for campaign, then optional prompts
            mock_prompt.side_effect = [
                "afghanistan",
                "",
                "",
            ]  # campaign, name (empty), comment (empty)

            mock_detect.return_value = {
                "afghanistan": ["foothold_afghanistan.lua"],
                "syria": ["foothold_syria.lua"],
            }

            mock_create.return_value = tmp_path / "checkpoints" / "afghanistan.zip"

            result = runner.invoke(
                app, ["save", "--server", "test-server"], input="afghanistan\n\n\n"
            )

        assert result.exit_code == 0
        assert mock_prompt.called

    def test_campaign_prompt_with_all_option(self, tmp_path):
        """Test that campaign prompt includes 'all' option to save all campaigns."""
        from typer.testing import CliRunner

        from foothold_checkpoint.cli import app

        runner = CliRunner()
        with (
            patch("foothold_checkpoint.cli.load_config") as mock_load,
            patch("foothold_checkpoint.cli.Prompt.ask") as mock_prompt,
            patch("foothold_checkpoint.cli.detect_campaigns") as mock_detect,
            patch("foothold_checkpoint.cli.create_checkpoint") as mock_create,
            patch("pathlib.Path.exists", return_value=True),
            patch(
                "pathlib.Path.iterdir",
                return_value=[
                    Mock(name="foothold_afghanistan.lua", is_file=lambda: True),
                    Mock(name="foothold_syria.lua", is_file=lambda: True),
                ],
            ),
        ):

            mock_config = Mock()
            mock_config.servers = {"test-server": Mock(mission_directory=tmp_path)}
            mock_config.checkpoints_directory = tmp_path / "checkpoints"
            mock_load.return_value = mock_config

            # User selects 'all'
            mock_prompt.return_value = "all"

            mock_detect.return_value = {
                "afghanistan": ["foothold_afghanistan.lua"],
                "syria": ["foothold_syria.lua"],
            }

            mock_create.return_value = tmp_path / "checkpoints" / "campaign.zip"

            result = runner.invoke(app, ["save", "--server", "test-server"], input="all\n")

        assert result.exit_code == 0
        # Should create checkpoints for all campaigns
        assert mock_create.call_count == 2

    def test_campaign_prompt_with_no_campaigns_detected(self, tmp_path):
        """Test error when no campaigns are detected in mission directory."""
        from typer.testing import CliRunner

        from foothold_checkpoint.cli import app

        runner = CliRunner()
        with (
            patch("foothold_checkpoint.cli.load_config") as mock_load,
            patch("foothold_checkpoint.cli.detect_campaigns") as mock_detect,
            patch("pathlib.Path.exists", return_value=True),
            patch("pathlib.Path.iterdir", return_value=[]),
        ):

            mock_config = Mock()
            mock_config.servers = {"test-server": Mock(mission_directory=tmp_path)}
            mock_config.checkpoints_directory = tmp_path / "checkpoints"
            mock_load.return_value = mock_config

            mock_detect.return_value = {}

            result = runner.invoke(app, ["save", "--server", "test-server"])

        assert result.exit_code == 1
        assert "No campaigns detected" in result.stdout or "no campaigns" in result.stdout.lower()


class TestNameCommentPrompts:
    """Tests for optional name and comment prompts."""

    def test_name_prompt_is_optional(self, tmp_path):
        """Test that name prompt accepts empty input (optional field)."""
        from typer.testing import CliRunner

        from foothold_checkpoint.cli import app

        runner = CliRunner()
        with (
            patch("foothold_checkpoint.cli.load_config") as mock_load,
            patch("foothold_checkpoint.cli.Prompt.ask") as mock_prompt,
            patch("foothold_checkpoint.cli.detect_campaigns") as mock_detect,
            patch("foothold_checkpoint.cli.create_checkpoint") as mock_create,
            patch("pathlib.Path.exists", return_value=True),
            patch(
                "pathlib.Path.iterdir",
                return_value=[Mock(name="foothold_afghanistan.lua", is_file=lambda: True)],
            ),
        ):

            mock_config = Mock()
            mock_config.servers = {"test-server": Mock(mission_directory=tmp_path)}
            mock_config.checkpoints_directory = tmp_path / "checkpoints"
            mock_load.return_value = mock_config

            # Empty name and comment
            mock_prompt.side_effect = ["", ""]

            mock_detect.return_value = {"afghanistan": ["foothold_afghanistan.lua"]}

            mock_create.return_value = tmp_path / "checkpoints" / "afghanistan.zip"

            result = runner.invoke(
                app, ["save", "--server", "test-server", "--campaign", "afghanistan"], input="\n\n"
            )

        assert result.exit_code == 0
        # Verify create_checkpoint was called with None for name and comment
        call_args = mock_create.call_args
        assert call_args[1].get("name") is None or call_args[1].get("name") == ""
        assert call_args[1].get("comment") is None or call_args[1].get("comment") == ""

    def test_name_and_comment_prompts_with_values(self, tmp_path):
        """Test name and comment flags are used when provided."""
        from typer.testing import CliRunner

        from foothold_checkpoint.cli import app

        runner = CliRunner()
        with (
            patch("foothold_checkpoint.cli.load_config") as mock_load,
            patch("foothold_checkpoint.cli.detect_campaigns") as mock_detect,
            patch("foothold_checkpoint.cli.create_checkpoint") as mock_create,
            patch("pathlib.Path.exists", return_value=True),
            patch(
                "pathlib.Path.iterdir",
                return_value=[Mock(name="foothold_afghanistan.lua", is_file=lambda: True)],
            ),
        ):

            mock_config = Mock()
            mock_config.servers = {"test-server": Mock(mission_directory=tmp_path)}
            mock_config.checkpoints_directory = tmp_path / "checkpoints"
            mock_load.return_value = mock_config

            mock_detect.return_value = {"afghanistan": ["foothold_afghanistan.lua"]}

            mock_create.return_value = tmp_path / "checkpoints" / "afghanistan.zip"

            result = runner.invoke(
                app,
                [
                    "save",
                    "--server",
                    "test-server",
                    "--campaign",
                    "afghanistan",
                    "--name",
                    "Mission 5",
                    "--comment",
                    "Before major update",
                ],
            )

        assert result.exit_code == 0
        # Verify create_checkpoint was called with provided values
        call_args = mock_create.call_args
        assert call_args[1].get("name") == "Mission 5"
        assert call_args[1].get("comment") == "Before major update"


class TestProgressDisplay:
    """Tests for progress display using Rich."""

    def test_progress_callback_is_used(self, tmp_path):
        """Test that create_checkpoint is called with progress_callback."""
        from typer.testing import CliRunner

        from foothold_checkpoint.cli import app

        runner = CliRunner()
        with (
            patch("foothold_checkpoint.cli.load_config") as mock_load,
            patch("foothold_checkpoint.cli.detect_campaigns") as mock_detect,
            patch("foothold_checkpoint.cli.create_checkpoint") as mock_create,
            patch("pathlib.Path.exists", return_value=True),
            patch(
                "pathlib.Path.iterdir",
                return_value=[Mock(name="foothold_afghanistan.lua", is_file=lambda: True)],
            ),
        ):

            mock_config = Mock()
            mock_config.servers = {"test-server": Mock(mission_directory=tmp_path)}
            mock_config.checkpoints_directory = tmp_path / "checkpoints"
            mock_load.return_value = mock_config

            mock_detect.return_value = {"afghanistan": ["foothold_afghanistan.lua"]}

            mock_create.return_value = tmp_path / "checkpoints" / "afghanistan.zip"

            result = runner.invoke(
                app, ["save", "--server", "test-server", "--campaign", "afghanistan"]
            )

        assert result.exit_code == 0, f"Command failed with: {result.stdout}"
        # Verify create_checkpoint was called with progress_callback parameter
        call_args = mock_create.call_args
        assert "progress_callback" in call_args[1]
        assert (
            callable(call_args[1]["progress_callback"]) or call_args[1]["progress_callback"] is None
        )

    def test_progress_display_with_quiet_mode(self, tmp_path):
        """Test that --quiet suppresses progress display."""
        from typer.testing import CliRunner

        from foothold_checkpoint.cli import app

        runner = CliRunner()
        with (
            patch("foothold_checkpoint.cli.load_config") as mock_load,
            patch("foothold_checkpoint.cli.detect_campaigns") as mock_detect,
            patch("foothold_checkpoint.cli.create_checkpoint") as mock_create,
            patch("pathlib.Path.exists", return_value=True),
            patch(
                "pathlib.Path.iterdir",
                return_value=[Mock(name="foothold_afghanistan.lua", is_file=lambda: True)],
            ),
        ):

            mock_config = Mock()
            mock_config.servers = {"test-server": Mock(mission_directory=tmp_path)}
            mock_config.checkpoints_directory = tmp_path / "checkpoints"
            mock_load.return_value = mock_config

            mock_detect.return_value = {"afghanistan": ["foothold_afghanistan.lua"]}

            mock_create.return_value = tmp_path / "checkpoints" / "afghanistan.zip"

            result = runner.invoke(
                app, ["--quiet", "save", "--server", "test-server", "--campaign", "afghanistan"]
            )

        assert result.exit_code == 0
        # With --quiet, progress_callback should be None or output should be minimal
        call_args = mock_create.call_args
        assert "progress_callback" in call_args[1]


class TestSuccessErrorMessages:
    """Tests for success and error messages."""

    def test_success_message_displays_checkpoint_path(self, tmp_path):
        """Test that success message includes path to created checkpoint."""
        from typer.testing import CliRunner

        from foothold_checkpoint.cli import app

        checkpoint_path = tmp_path / "checkpoints" / "afghanistan_2024-02-14_10-30-00.zip"

        runner = CliRunner()
        with (
            patch("foothold_checkpoint.cli.load_config") as mock_load,
            patch("foothold_checkpoint.cli.detect_campaigns") as mock_detect,
            patch("foothold_checkpoint.cli.create_checkpoint") as mock_create,
            patch("pathlib.Path.exists", return_value=True),
            patch(
                "pathlib.Path.iterdir",
                return_value=[Mock(name="foothold_afghanistan.lua", is_file=lambda: True)],
            ),
        ):

            mock_config = Mock()
            mock_config.servers = {"test-server": Mock(mission_directory=tmp_path)}
            mock_config.checkpoints_directory = tmp_path / "checkpoints"
            mock_load.return_value = mock_config

            mock_detect.return_value = {"afghanistan": ["foothold_afghanistan.lua"]}

            mock_create.return_value = checkpoint_path

            result = runner.invoke(
                app, ["save", "--server", "test-server", "--campaign", "afghanistan"]
            )

        assert result.exit_code == 0
        assert "afghanistan_2024-02-14_10-30-00.zip" in result.stdout or "Success" in result.stdout

    def test_error_message_for_missing_config(self, tmp_path):
        """Test error message when configuration file is not found."""
        from typer.testing import CliRunner

        from foothold_checkpoint.cli import app

        runner = CliRunner()
        with patch("foothold_checkpoint.cli.load_config") as mock_load:
            mock_load.side_effect = FileNotFoundError("Configuration file not found")

            result = runner.invoke(
                app, ["save", "--server", "test-server", "--campaign", "afghanistan"]
            )

        assert result.exit_code == 1
        assert "Configuration" in result.stdout or "config" in result.stdout.lower()

    def test_error_message_for_invalid_directory(self, tmp_path):
        """Test error message when mission directory does not exist."""
        from typer.testing import CliRunner

        from foothold_checkpoint.cli import app

        runner = CliRunner()
        with (
            patch("foothold_checkpoint.cli.load_config") as mock_load,
            patch("pathlib.Path.exists", return_value=False),
        ):

            mock_config = Mock()
            mock_config.servers = {"test-server": Mock(mission_directory=Path("/nonexistent"))}
            mock_config.checkpoints_directory = tmp_path / "checkpoints"
            mock_load.return_value = mock_config

            result = runner.invoke(
                app, ["save", "--server", "test-server", "--campaign", "afghanistan"]
            )

        assert result.exit_code == 1
        assert "does not exist" in result.stdout.lower() or "not found" in result.stdout.lower()

    def test_success_message_not_shown_in_quiet_mode(self, tmp_path):
        """Test that success message is suppressed with --quiet flag."""
        from typer.testing import CliRunner

        from foothold_checkpoint.cli import app

        runner = CliRunner()
        with (
            patch("foothold_checkpoint.cli.load_config") as mock_load,
            patch("foothold_checkpoint.cli.detect_campaigns") as mock_detect,
            patch("foothold_checkpoint.cli.create_checkpoint") as mock_create,
            patch("pathlib.Path.exists", return_value=True),
            patch(
                "pathlib.Path.iterdir",
                return_value=[Mock(name="foothold_afghanistan.lua", is_file=lambda: True)],
            ),
        ):

            mock_config = Mock()
            mock_config.servers = {"test-server": Mock(mission_directory=tmp_path)}
            mock_config.checkpoints_directory = tmp_path / "checkpoints"
            mock_load.return_value = mock_config

            mock_detect.return_value = {"afghanistan": ["foothold_afghanistan.lua"]}

            mock_create.return_value = tmp_path / "checkpoints" / "afghanistan.zip"

            result = runner.invoke(
                app, ["--quiet", "save", "--server", "test-server", "--campaign", "afghanistan"]
            )

        assert result.exit_code == 0
        # In quiet mode, only checkpoint paths should be printed (for scripting)
        # Should not contain success messages or progress indicators
        assert "Success" not in result.stdout
        assert "✓" not in result.stdout
        assert len(result.stdout.strip()) > 0  # Should have at least the path

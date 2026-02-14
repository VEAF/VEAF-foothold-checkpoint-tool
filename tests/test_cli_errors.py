"""Tests for CLI error handling.

This module tests user-friendly error messages and validation for common error scenarios:
- Server not found in configuration
- Campaign not found in mission directory
- File not found (config, mission directory, checkpoint files)
- Permission errors (directory, file access)
- Conflicting command-line flags
"""

from pathlib import Path
from unittest.mock import Mock, patch

from typer.testing import CliRunner


def test_save_server_not_found_error_message() -> None:
    """Test error message when server is not configured."""
    from foothold_checkpoint.cli import app

    runner = CliRunner()

    # Mock config with no servers matching the provided one
    mock_config = Mock()
    mock_config.servers = {"prod-1": Mock(), "prod-2": Mock()}

    with (
        patch("foothold_checkpoint.cli.load_config", return_value=mock_config),
        patch("foothold_checkpoint.cli._quiet_mode", True),
    ):
        result = runner.invoke(app, ["save", "--server", "nonexistent"])

    assert result.exit_code == 1
    assert "Server 'nonexistent' not found" in result.stdout
    assert "Available servers:" in result.stdout
    assert "prod-1" in result.stdout


def test_save_campaign_not_found_error_message() -> None:
    """Test error message when campaign is not in mission directory."""
    from foothold_checkpoint.cli import app

    runner = CliRunner(mix_stderr=False)

    # Mock config and server
    mission_dir = Path("/tmp/test/missions")
    mock_server_config = Mock()
    mock_server_config.path = str(mission_dir)

    mock_config = Mock()
    mock_config.servers = {"prod-1": mock_server_config}

    # Mock detect_campaigns to return specific campaigns
    detected_campaigns = {
        "afghanistan": ["Foothold_Afghan_v0.1.lua"],
        "syria": ["Foothold_Syria_v0.1.lua"],
    }

    with (
        patch("foothold_checkpoint.cli.load_config", return_value=mock_config),
        patch("foothold_checkpoint.cli.Path.exists", return_value=True),
        patch("foothold_checkpoint.cli.Path.iterdir", return_value=[]),
        patch("foothold_checkpoint.cli.detect_campaigns", return_value=detected_campaigns),
        patch("foothold_checkpoint.cli._quiet_mode", True),
    ):
        result = runner.invoke(app, ["save", "--server", "prod-1", "--campaign", "nonexistent"])

    assert result.exit_code == 1
    assert "Campaign 'nonexistent' not found" in result.stdout
    assert "Available campaigns:" in result.stdout
    assert "afghanistan" in result.stdout


def test_save_path_not_found_error() -> None:
    """Test error message when mission directory does not exist."""
    from foothold_checkpoint.cli import app

    runner = CliRunner()

    mission_dir = Path("/nonexistent/missions")
    mock_server_config = Mock()
    mock_server_config.path = str(mission_dir)

    mock_config = Mock()
    mock_config.servers = {"prod-1": mock_server_config}

    with (
        patch("foothold_checkpoint.cli.load_config", return_value=mock_config),
        patch("foothold_checkpoint.cli._quiet_mode", True),
    ):
        result = runner.invoke(app, ["save", "--server", "prod-1"])

    assert result.exit_code == 1
    assert "Mission saves directory does not exist" in result.stdout
    # Note: mission_dir in output now includes /Missions/Saves appended


def test_save_no_campaigns_detected_error() -> None:
    """Test error message when no campaigns are detected."""
    from foothold_checkpoint.cli import app

    runner = CliRunner()

    mission_dir = Path("/tmp/test/missions")
    mock_server_config = Mock()
    mock_server_config.path = str(mission_dir)

    mock_config = Mock()
    mock_config.servers = {"prod-1": mock_server_config}

    with (
        patch("foothold_checkpoint.cli.load_config", return_value=mock_config),
        patch("foothold_checkpoint.cli.Path.exists", return_value=True),
        patch("foothold_checkpoint.cli.Path.iterdir", return_value=[]),
        patch("foothold_checkpoint.cli.detect_campaigns", return_value={}),
        patch("foothold_checkpoint.cli._quiet_mode", True),
    ):
        result = runner.invoke(app, ["save", "--server", "prod-1"])

    assert result.exit_code == 1
    assert "No campaigns detected" in result.stdout


def test_config_file_not_found_error() -> None:
    """Test error message when custom config file does not exist."""
    from foothold_checkpoint.cli import app

    runner = CliRunner()

    result = runner.invoke(app, ["--config", "/nonexistent/config.yaml", "--version"])

    assert result.exit_code == 1
    assert "Config file not found" in result.stdout


def test_config_path_not_file_error() -> None:
    """Test error message when config path is a directory."""
    from foothold_checkpoint.cli import app

    runner = CliRunner()

    with (
        patch("foothold_checkpoint.cli.Path.exists", return_value=True),
        patch("foothold_checkpoint.cli.Path.is_file", return_value=False),
    ):
        result = runner.invoke(app, ["--config", "/tmp/", "--version"])

    assert result.exit_code == 1
    assert "Config path is not a file" in result.stdout


def test_restore_checkpoint_file_not_found_error() -> None:
    """Test error message when checkpoint file does not exist."""
    from foothold_checkpoint.cli import app

    runner = CliRunner()

    mock_config = Mock()
    mock_config.servers = {"prod-1": Mock()}
    mock_config.checkpoints_dir = "/tmp/checkpoints"

    with (
        patch("foothold_checkpoint.cli.load_config", return_value=mock_config),
        patch("foothold_checkpoint.cli.Path.exists", return_value=False),
        patch("foothold_checkpoint.cli._quiet_mode", True),
    ):
        result = runner.invoke(app, ["restore", "nonexistent.zip", "--server", "prod-1"])

    assert result.exit_code == 1
    assert "Checkpoint file not found" in result.stdout


def test_restore_server_not_found_error() -> None:
    """Test error message when server is not configured for restore."""
    from foothold_checkpoint.cli import app

    runner = CliRunner()

    mock_config = Mock()
    mock_config.servers = {"prod-1": Mock(), "prod-2": Mock()}
    mock_config.checkpoints_dir = "/tmp/checkpoints"

    with (
        patch("foothold_checkpoint.cli.load_config", return_value=mock_config),
        patch("foothold_checkpoint.cli.Path.exists", return_value=True),
        patch("foothold_checkpoint.cli._quiet_mode", True),
    ):
        result = runner.invoke(app, ["restore", "test.zip", "--server", "nonexistent"])

    assert result.exit_code == 1
    assert "Server 'nonexistent' not found" in result.stdout


def test_delete_checkpoint_file_not_found_error() -> None:
    """Test error message when checkpoint file to delete does not exist."""
    from foothold_checkpoint.cli import app

    runner = CliRunner()

    mock_config = Mock()
    mock_config.checkpoints_dir = "/tmp/checkpoints"

    with (
        patch("foothold_checkpoint.cli.load_config", return_value=mock_config),
        patch("foothold_checkpoint.cli.Path.exists", return_value=False),
        patch("foothold_checkpoint.cli._quiet_mode", True),
    ):
        result = runner.invoke(app, ["delete", "nonexistent.zip", "--force"])

    assert result.exit_code == 1
    assert "Checkpoint file not found" in result.stdout


def test_import_directory_not_found_error() -> None:
    """Test error message when import source directory does not exist."""
    from foothold_checkpoint.cli import app

    runner = CliRunner()

    mock_config = Mock()
    mock_config.checkpoints_dir = "/tmp/checkpoints"

    with (
        patch("foothold_checkpoint.cli.load_config", return_value=mock_config),
        patch("foothold_checkpoint.cli._quiet_mode", True),
    ):
        result = runner.invoke(
            app,
            [
                "import",
                "/nonexistent/dir",
                "--server",
                "prod-1",
                "--campaign",
                "test",
            ],
        )

    assert result.exit_code == 1
    assert "not found" in result.stdout.lower()


def test_import_path_not_directory_error() -> None:
    """Test error message when import path is not a directory."""
    from foothold_checkpoint.cli import app

    runner = CliRunner()

    mock_config = Mock()
    mock_config.checkpoints_dir = "/tmp/checkpoints"

    with (
        patch("foothold_checkpoint.cli.load_config", return_value=mock_config),
        patch("foothold_checkpoint.cli.Path.exists", return_value=True),
        patch("foothold_checkpoint.cli.Path.is_dir", return_value=False),
        patch("foothold_checkpoint.cli._quiet_mode", True),
    ):
        result = runner.invoke(
            app, ["import", "/tmp/file.txt", "--server", "prod-1", "--campaign", "test"]
        )

    assert result.exit_code == 1
    assert "not a directory" in result.stdout.lower()


def test_save_permission_error_on_checkpoint_directory() -> None:
    """Test error message when cannot create checkpoint directory due to permissions."""
    from foothold_checkpoint.cli import app

    runner = CliRunner()

    mission_dir = Path("/tmp/test/missions")
    mock_server_config = Mock()
    mock_server_config.path = str(mission_dir)

    mock_config = Mock()
    mock_config.servers = {"prod-1": mock_server_config}
    mock_config.checkpoints_dir = "/root/forbidden"

    detected_campaigns = {"afghanistan": ["Foothold_Afghan_v0.1.lua"]}

    with (
        patch("foothold_checkpoint.cli.load_config", return_value=mock_config),
        patch("foothold_checkpoint.cli.Path.exists", return_value=True),
        patch("foothold_checkpoint.cli.Path.iterdir", return_value=[]),
        patch("foothold_checkpoint.cli.detect_campaigns", return_value=detected_campaigns),
        patch("foothold_checkpoint.cli.Path.mkdir", side_effect=PermissionError("Access denied")),
        patch("foothold_checkpoint.cli._quiet_mode", True),
    ):
        result = runner.invoke(app, ["save", "--server", "prod-1", "--campaign", "afghanistan"])

    assert result.exit_code == 1
    assert "Permission denied" in result.stdout or "Access denied" in result.stdout


def test_save_conflicting_flags_campaign_and_all() -> None:
    """Test validation error when both --campaign and --all flags are provided."""
    from foothold_checkpoint.cli import app

    runner = CliRunner()

    # Mock config to allow test to proceed to flag validation
    mission_dir = Path("/tmp/test/missions")
    mock_server_config = Mock()
    mock_server_config.path = str(mission_dir)

    mock_config = Mock()
    mock_config.servers = {"prod-1": mock_server_config}
    mock_config.checkpoints_dir = "/tmp/checkpoints"

    with patch("foothold_checkpoint.cli.load_config", return_value=mock_config):
        result = runner.invoke(
            app, ["save", "--server", "prod-1", "--campaign", "afghanistan", "--all"]
        )

    # Should exit with error code 1
    assert result.exit_code == 1

    # Should display error message about conflicting flags
    assert "cannot use both" in result.stdout.lower() or "conflicting" in result.stdout.lower()


def test_save_flags_validation_accepts_campaign_only() -> None:
    """Test that --campaign flag works when --all is not provided."""
    from foothold_checkpoint.cli import app

    runner = CliRunner()

    mission_dir = Path("/tmp/test/missions")
    mock_server_config = Mock()
    mock_server_config.path = str(mission_dir)

    mock_config = Mock()
    mock_config.servers = {"prod-1": mock_server_config}
    mock_config.checkpoints_dir = "/tmp/checkpoints"

    detected_campaigns = {"afghanistan": ["Foothold_Afghan_v0.1.lua"]}

    with (
        patch("foothold_checkpoint.cli.load_config", return_value=mock_config),
        patch("foothold_checkpoint.cli.Path.exists", return_value=True),
        patch(
            "foothold_checkpoint.cli.Path.iterdir", return_value=[Path("Foothold_Afghan_v0.1.lua")]
        ),
        patch("foothold_checkpoint.cli.detect_campaigns", return_value=detected_campaigns),
        patch("foothold_checkpoint.cli.create_checkpoint"),
    ):
        result = runner.invoke(app, ["save", "--server", "prod-1", "--campaign", "afghanistan"])

    # Should succeed with only --campaign flag (no conflict)
    assert result.exit_code == 0


def test_save_flags_validation_accepts_all_only() -> None:
    """Test that --all flag works when --campaign is not provided."""
    from foothold_checkpoint.cli import app

    runner = CliRunner()

    mission_dir = Path("/tmp/test/missions")
    mock_server_config = Mock()
    mock_server_config.path = str(mission_dir)

    mock_config = Mock()
    mock_config.servers = {"prod-1": mock_server_config}
    mock_config.checkpoints_dir = "/tmp/checkpoints"

    detected_campaigns = {"afghanistan": ["Foothold_Afghan_v0.1.lua"]}

    with (
        patch("foothold_checkpoint.cli.load_config", return_value=mock_config),
        patch("foothold_checkpoint.cli.Path.exists", return_value=True),
        patch(
            "foothold_checkpoint.cli.Path.iterdir", return_value=[Path("Foothold_Afghan_v0.1.lua")]
        ),
        patch("foothold_checkpoint.cli.detect_campaigns", return_value=detected_campaigns),
        patch("foothold_checkpoint.cli.create_checkpoint"),
    ):
        result = runner.invoke(app, ["save", "--server", "prod-1", "--all"])

    # Should succeed with only --all flag (no conflict)
    assert result.exit_code == 0


def test_restore_permission_error_on_path() -> None:
    """Test error message when cannot write to mission directory due to permissions."""
    from foothold_checkpoint.cli import app

    runner = CliRunner()

    mission_dir = Path("/root/forbidden/missions")
    mock_server_config = Mock()
    mock_server_config.path = str(mission_dir)

    mock_config = Mock()
    mock_config.servers = {"prod-1": mock_server_config}
    mock_config.checkpoints_dir = "/tmp/checkpoints"

    # Mock restore_checkpoint to raise PermissionError
    mock_restore = Mock(side_effect=PermissionError("Access denied"))

    with (
        patch("foothold_checkpoint.cli.load_config", return_value=mock_config),
        patch("foothold_checkpoint.cli.Path.exists", return_value=True),
        patch("foothold_checkpoint.cli.restore_checkpoint", mock_restore),
        patch("foothold_checkpoint.cli._quiet_mode", True),
    ):
        result = runner.invoke(app, ["restore", "test.zip", "--server", "prod-1"])

    assert result.exit_code == 1
    assert "Permission" in result.stdout or "denied" in result.stdout


def test_list_no_checkpoints_found_message() -> None:
    """Test message when no checkpoints match the filters."""
    from foothold_checkpoint.cli import app

    runner = CliRunner()

    mock_config = Mock()
    mock_config.checkpoints_dir = "/tmp/checkpoints"

    # Mock list_checkpoints to return empty list
    with (
        patch("foothold_checkpoint.cli.load_config", return_value=mock_config),
        patch("foothold_checkpoint.cli.list_checkpoints", return_value=[]),
        patch("foothold_checkpoint.cli._quiet_mode", False),
    ):
        result = runner.invoke(app, ["list", "--server", "prod-1"])

    assert result.exit_code == 0
    assert "No checkpoints found" in result.stdout


def test_delete_permission_error_on_checkpoint_file() -> None:
    """Test error message when cannot delete checkpoint file due to permissions."""
    from foothold_checkpoint.cli import app

    runner = CliRunner()

    mock_config = Mock()
    mock_config.checkpoints_dir = "/tmp/checkpoints"

    # Mock delete_checkpoint to raise PermissionError
    mock_delete = Mock(side_effect=PermissionError("Access denied"))

    with (
        patch("foothold_checkpoint.cli.load_config", return_value=mock_config),
        patch("foothold_checkpoint.cli.Path.exists", return_value=True),
        patch("foothold_checkpoint.cli.delete_checkpoint", mock_delete),
        patch("foothold_checkpoint.cli._quiet_mode", True),
    ):
        result = runner.invoke(app, ["delete", "test.zip", "--force"])

    assert result.exit_code == 1
    assert "denied" in result.stdout.lower() or "permission" in result.stdout.lower()

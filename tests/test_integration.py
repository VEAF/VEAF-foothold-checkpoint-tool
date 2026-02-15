"""Integration tests for end-to-end workflows.

These tests verify complete workflows across multiple commands and verify
the interactions between CLI, core modules, and file system.

Uses real Foothold campaign files from tests/data/foothold/ directory.
"""

from pathlib import Path

import pytest


@pytest.fixture
def real_foothold_data() -> Path:
    """Path to real Foothold campaign test data."""
    return Path(__file__).parent / "data" / "foothold1_server" / "Missions" / "Saves"


@pytest.fixture
def temp_test_env(tmp_path: Path, real_foothold_data: Path) -> dict[str, Path]:
    """Create temporary test environment with real campaign files."""
    import shutil

    checkpoints_dir = tmp_path / "checkpoints"
    server1_saves = tmp_path / "servers" / "server1" / "Missions" / "Saves"
    server2_saves = tmp_path / "servers" / "server2" / "Missions" / "Saves"

    checkpoints_dir.mkdir(parents=True)
    server1_saves.mkdir(parents=True)
    server2_saves.mkdir(parents=True)

    # Copy real Foothold files to server1
    if real_foothold_data.exists():
        for file in real_foothold_data.glob("*"):
            if file.is_file():
                shutil.copy(file, server1_saves)

    return {
        "checkpoints_dir": checkpoints_dir,
        "server1_saves": server1_saves,
        "server2_saves": server2_saves,
        "tmp": tmp_path,
        "real_data": real_foothold_data,
    }


def test_real_foothold_data_exists(real_foothold_data: Path) -> None:
    """Verify real Foothold test data is available."""
    assert (
        real_foothold_data.exists()
    ), "tests/data/foothold1_server/Missions/Saves/ directory should exist"

    # Check for expected campaign files
    files = list(real_foothold_data.glob("*"))
    assert files, "tests/data/foothold1_server/Missions/Saves/ should contain campaign files"

    # Should have at least one .lua file
    lua_files = list(real_foothold_data.glob("*.lua"))
    assert lua_files, "Should have at least one .lua campaign file"

    # Should have Foothold_Ranks.lua
    assert (real_foothold_data / "Foothold_Ranks.lua").exists()


def test_campaign_detection_with_real_data(real_foothold_data: Path) -> None:
    """Test campaign detection with real Foothold files."""
    from foothold_checkpoint.core.campaign import detect_campaigns
    from tests.conftest import make_simple_campaign, make_test_config

    if not real_foothold_data.exists():
        pytest.skip("Real foothold data not available")

    # Create config with expected campaigns from test data
    config = make_test_config(
        campaigns={
            "ca": make_simple_campaign(
                "Caucasus",
                ["FootHold_CA_v0.2.lua", "FootHold_CA_v0.2_Coldwar.lua"],
            ),
            "germany": make_simple_campaign(
                "Germany",
                ["FootHold_Germany_Modern_V0.1.lua"],
            ),
            "si": make_simple_campaign(
                "South Island",
                ["FootHold_SI_v0.3.lua"],
            ),
        },
    )

    # Get list of files in the test data directory
    files: list[str | Path] = [f for f in real_foothold_data.glob("*") if f.is_file()]
    campaigns = detect_campaigns(files, config)

    # Should detect multiple campaigns
    assert campaigns, "Should detect at least one campaign"

    # Check for expected campaigns (based on test data files)
    campaign_names = set(campaigns.keys())

    # Should detect the campaigns we configured
    assert "ca" in campaign_names, "Should detect Caucasus campaign"
    assert "germany" in campaign_names, "Should detect Germany campaign"
    assert "si" in campaign_names, "Should detect South Island campaign"

    # Verify each campaign has files
    for campaign_name, campaign_files in campaigns.items():
        assert campaign_files, f"Campaign {campaign_name} should have files"


def test_integration_environment_setup(temp_test_env: dict[str, Path]) -> None:
    """Verify test environment is set up correctly with real data."""
    # Verify directories created
    assert temp_test_env["checkpoints_dir"].exists()
    assert temp_test_env["server1_saves"].exists()
    assert temp_test_env["server2_saves"].exists()

    # Verify real files were copied to server1
    if temp_test_env["real_data"].exists():
        server1_files = list(temp_test_env["server1_saves"].glob("*"))
        assert server1_files, "Should have copied files to server1"


# TODO: Implement full end-to-end workflow tests:
# - Save checkpoint → List checkpoints → Restore checkpoint (complete workflow)
# - Import existing backup directory to checkpoint format
# - Delete checkpoint with confirmation
# - Cross-server restoration (save from server1, restore to server2)
# - Save and restore all campaigns with --all flag
# - Error scenarios (corrupted checkpoint, missing files, permission errors)
# - Windows-specific path handling (backslashes, UNC paths)
#
# Note: Full workflow tests require proper parameter signatures in
# create_checkpoint, restore_checkpoint, import_checkpoint functions

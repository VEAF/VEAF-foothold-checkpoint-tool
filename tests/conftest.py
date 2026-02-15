"""Pytest fixtures and helpers for foothold-checkpoint tests."""

from pathlib import Path

import pytest


@pytest.fixture
def simple_config():
    """Create a simple test configuration with minimal campaigns."""
    from foothold_checkpoint.core.config import (
        CampaignConfig,
        CampaignFileList,
        CampaignFileType,
        Config,
        ServerConfig,
    )

    return Config(
        checkpoints_dir=Path("~/.foothold-checkpoints"),
        servers={
            "test-server": ServerConfig(
                path=Path("D:/Test/Server/Missions/Saves"),
                description="Test server",
            )
        },
        campaigns={
            "test_campaign": CampaignConfig(
                display_name="Test Campaign",
                files=CampaignFileList(
                    persistence=CampaignFileType(files=["foothold_test.lua"]),
                    ctld_save=CampaignFileType(files=[], optional=True),
                    ctld_farps=CampaignFileType(files=[], optional=True),
                    storage=CampaignFileType(files=[], optional=True),
                ),
            )
        },
    )


def make_test_config(**kwargs):
    """Helper to create test configs with custom values, using sensible defaults.

    Args:
        checkpoints_dir: Path to checkpoints directory (default: ~/.foothold-checkpoints)
        servers: Dict of server configs (default: single test server)
        campaigns: Dict of campaign configs (default: empty)

    Returns:
        Config object for testing

    Example:
        >>> config = make_test_config(
        ...     campaigns={
        ...         "ca": make_simple_campaign("Caucasus", ["FootHold_CA.lua"])
        ...     }
        ... )
    """
    from foothold_checkpoint.core.config import Config, ServerConfig

    defaults = {
        "checkpoints_dir": Path("~/.foothold-checkpoints"),
        "servers": {
            "test-server": ServerConfig(
                path=Path("D:/Test/Server/Missions/Saves"),
                description="Test server",
            )
        },
        "campaigns": {},
    }

    defaults.update(kwargs)
    return Config(**defaults)


def make_simple_campaign(display_name, persistence_files=None, **kwargs):
    """Helper to create a simple campaign configuration for tests.

    Args:
        display_name: Display name for the campaign
        persistence_files: List of .lua persistence files (default: empty list)
        **kwargs: Optional file lists for ctld_save, ctld_farps, storage

    Returns:
        CampaignConfig object

    Example:
        >>> campaign = make_simple_campaign(
        ...     "Caucasus",
        ...     persistence_files=["FootHold_CA.lua"],
        ...     ctld_save=["FootHold_CA_CTLD_Save.csv"]
        ... )
    """
    from foothold_checkpoint.core.config import (
        CampaignConfig,
        CampaignFileList,
        CampaignFileType,
    )

    return CampaignConfig(
        display_name=display_name,
        files=CampaignFileList(
            persistence=CampaignFileType(
                files=persistence_files or [],
                optional=not persistence_files,
            ),
            ctld_save=CampaignFileType(
                files=kwargs.get("ctld_save", []),
                optional=True,
            ),
            ctld_farps=CampaignFileType(
                files=kwargs.get("ctld_farps", []),
                optional=True,
            ),
            storage=CampaignFileType(
                files=kwargs.get("storage", []),
                optional=True,
            ),
        ),
    )

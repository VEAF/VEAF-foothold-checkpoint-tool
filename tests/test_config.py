"""Tests for configuration management module."""

import pytest
from pathlib import Path
from pydantic import ValidationError


class TestServerConfig:
    """Test suite for ServerConfig Pydantic model."""

    def test_valid_server_config(self):
        """ServerConfig should accept valid path and description."""
        from foothold_checkpoint.core.config import ServerConfig

        config = ServerConfig(
            path=Path("D:/Servers/DCS-Production/Missions/Saves"),
            description="Production server"
        )

        assert config.path == Path("D:/Servers/DCS-Production/Missions/Saves")
        assert config.description == "Production server"

    def test_server_config_path_must_be_path(self):
        """ServerConfig path field should convert strings to Path."""
        from foothold_checkpoint.core.config import ServerConfig

        config = ServerConfig(
            path="D:/Servers/DCS-Test/Missions/Saves",
            description="Test server"
        )

        assert isinstance(config.path, Path)
        assert config.path == Path("D:/Servers/DCS-Test/Missions/Saves")

    def test_server_config_requires_path(self):
        """ServerConfig should raise ValidationError if path is missing."""
        from foothold_checkpoint.core.config import ServerConfig

        with pytest.raises(ValidationError, match="path"):
            ServerConfig(description="Missing path")

    def test_server_config_requires_description(self):
        """ServerConfig should raise ValidationError if description is missing."""
        from foothold_checkpoint.core.config import ServerConfig

        with pytest.raises(ValidationError, match="description"):
            ServerConfig(path=Path("D:/Servers/DCS/Missions/Saves"))

    def test_server_config_is_immutable(self):
        """ServerConfig should be frozen (immutable)."""
        from foothold_checkpoint.core.config import ServerConfig

        config = ServerConfig(
            path=Path("D:/Servers/DCS/Missions/Saves"),
            description="Test"
        )

        with pytest.raises(ValidationError, match="frozen"):
            config.path = Path("D:/Other/Path")


class TestConfig:
    """Test suite for Config Pydantic model."""

    def test_valid_config(self):
        """Config should accept valid checkpoints_dir, servers, and campaigns."""
        from foothold_checkpoint.core.config import Config, ServerConfig

        config = Config(
            checkpoints_dir=Path("~/.foothold-checkpoints"),
            servers={
                "production-1": ServerConfig(
                    path=Path("D:/Servers/DCS-Production/Missions/Saves"),
                    description="Production server"
                )
            },
            campaigns={
                "Afghanistan": ["afghanistan"],
                "Caucasus": ["CA"],
            }
        )

        assert config.checkpoints_dir == Path("~/.foothold-checkpoints")
        assert "production-1" in config.servers
        assert config.servers["production-1"].description == "Production server"
        assert "Afghanistan" in config.campaigns
        assert config.campaigns["Afghanistan"] == ["afghanistan"]

    def test_config_requires_checkpoints_dir(self):
        """Config should raise ValidationError if checkpoints_dir is missing."""
        from foothold_checkpoint.core.config import Config

        with pytest.raises(ValidationError, match="checkpoints_dir"):
            Config(
                servers={},
                campaigns={}
            )

    def test_config_requires_servers(self):
        """Config should raise ValidationError if servers is missing."""
        from foothold_checkpoint.core.config import Config

        with pytest.raises(ValidationError, match="servers"):
            Config(
                checkpoints_dir=Path("~/.foothold-checkpoints"),
                campaigns={}
            )

    def test_config_requires_campaigns(self):
        """Config should raise ValidationError if campaigns is missing."""
        from foothold_checkpoint.core.config import Config

        with pytest.raises(ValidationError, match="campaigns"):
            Config(
                checkpoints_dir=Path("~/.foothold-checkpoints"),
                servers={}
            )

    def test_config_campaigns_values_must_be_lists(self):
        """Config campaigns values should be lists of strings."""
        from foothold_checkpoint.core.config import Config, ServerConfig

        # Valid: list of strings
        config = Config(
            checkpoints_dir=Path("~/.foothold-checkpoints"),
            servers={
                "test": ServerConfig(
                    path=Path("D:/Test"),
                    description="Test"
                )
            },
            campaigns={
                "Germany": ["GCW", "Germany_Modern"]
            }
        )

        assert isinstance(config.campaigns["Germany"], list)
        assert all(isinstance(name, str) for name in config.campaigns["Germany"])

    def test_config_campaigns_empty_list_invalid(self):
        """Config should raise ValidationError if campaign has empty name list."""
        from foothold_checkpoint.core.config import Config, ServerConfig

        with pytest.raises(ValidationError, match="at least 1 item"):
            Config(
                checkpoints_dir=Path("~/.foothold-checkpoints"),
                servers={
                    "test": ServerConfig(
                        path=Path("D:/Test"),
                        description="Test"
                    )
                },
                campaigns={
                    "Afghanistan": []  # Empty list should fail
                }
            )

    def test_config_is_immutable(self):
        """Config should be frozen (immutable)."""
        from foothold_checkpoint.core.config import Config, ServerConfig

        config = Config(
            checkpoints_dir=Path("~/.foothold-checkpoints"),
            servers={
                "test": ServerConfig(
                    path=Path("D:/Test"),
                    description="Test"
                )
            },
            campaigns={"Afghanistan": ["afghanistan"]}
        )

        with pytest.raises(ValidationError, match="frozen"):
            config.checkpoints_dir = Path("~/other")

"""Tests for configuration management module."""

import pytest
from pathlib import Path
from pydantic import ValidationError
import tempfile
import yaml


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


class TestLoadConfig:
    """Test suite for configuration loading from YAML files."""

    def test_load_valid_config(self):
        """load_config should successfully load a valid YAML configuration."""
        from foothold_checkpoint.core.config import load_config

        # Create a temporary YAML file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump({
                'checkpoints_dir': '~/.foothold-checkpoints',
                'servers': {
                    'production-1': {
                        'path': 'D:/Servers/DCS-Production/Missions/Saves',
                        'description': 'Production server'
                    }
                },
                'campaigns': {
                    'Afghanistan': ['afghanistan'],
                    'Caucasus': ['CA']
                }
            }, f)
            temp_path = Path(f.name)

        try:
            config = load_config(temp_path)

            assert config.checkpoints_dir == Path("~/.foothold-checkpoints")
            assert "production-1" in config.servers
            assert config.servers["production-1"].description == "Production server"
            assert config.campaigns["Afghanistan"] == ["afghanistan"]
        finally:
            temp_path.unlink()

    def test_load_config_file_not_found(self):
        """load_config should raise FileNotFoundError if file doesn't exist."""
        from foothold_checkpoint.core.config import load_config

        with pytest.raises(FileNotFoundError):
            load_config(Path("/nonexistent/config.yaml"))

    def test_load_config_invalid_yaml(self):
        """load_config should raise yaml.YAMLError for invalid YAML syntax."""
        from foothold_checkpoint.core.config import load_config

        # Create a file with invalid YAML syntax
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("invalid: yaml: syntax: here:\n  - broken")
            temp_path = Path(f.name)

        try:
            with pytest.raises(yaml.YAMLError):
                load_config(temp_path)
        finally:
            temp_path.unlink()

    def test_load_config_missing_required_fields(self):
        """load_config should raise ValidationError if required fields are missing."""
        from foothold_checkpoint.core.config import load_config

        # Create YAML without required 'campaigns' field
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump({
                'checkpoints_dir': '~/.foothold-checkpoints',
                'servers': {}
            }, f)
            temp_path = Path(f.name)

        try:
            with pytest.raises(ValidationError, match="campaigns"):
                load_config(temp_path)
        finally:
            temp_path.unlink()

    def test_load_config_invalid_campaign_empty_list(self):
        """load_config should raise ValidationError if campaign has empty name list."""
        from foothold_checkpoint.core.config import load_config

        # Create YAML with empty campaign list
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump({
                'checkpoints_dir': '~/.foothold-checkpoints',
                'servers': {
                    'test': {
                        'path': 'D:/Test',
                        'description': 'Test'
                    }
                },
                'campaigns': {
                    'Afghanistan': []  # Empty list should fail
                }
            }, f)
            temp_path = Path(f.name)

        try:
            with pytest.raises(ValidationError, match="at least 1 item"):
                load_config(temp_path)
        finally:
            temp_path.unlink()

    def test_load_config_converts_string_paths(self):
        """load_config should convert string paths to Path objects."""
        from foothold_checkpoint.core.config import load_config

        # YAML with string paths
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump({
                'checkpoints_dir': 'D:/Checkpoints',
                'servers': {
                    'test': {
                        'path': 'D:/Servers/Test/Missions/Saves',
                        'description': 'Test server'
                    }
                },
                'campaigns': {
                    'Germany': ['GCW', 'Germany_Modern']
                }
            }, f)
            temp_path = Path(f.name)

        try:
            config = load_config(temp_path)

            assert isinstance(config.checkpoints_dir, Path)
            assert isinstance(config.servers["test"].path, Path)
            assert config.checkpoints_dir == Path("D:/Checkpoints")
        finally:
            temp_path.unlink()

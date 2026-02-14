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

        # checkpoints_dir with ~ should be automatically expanded
        assert config.checkpoints_dir == Path.home() / ".foothold-checkpoints"
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

        with pytest.raises(ValidationError, match="empty name list"):
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

            # checkpoints_dir with ~ should be automatically expanded
            assert config.checkpoints_dir == Path.home() / ".foothold-checkpoints"
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
            with pytest.raises(ValidationError, match="empty name list"):
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


class TestCreateDefaultConfig:
    """Test suite for creating default configuration files."""

    def test_create_default_config_in_existing_directory(self):
        """create_default_config should create a config file in an existing directory."""
        from foothold_checkpoint.core.config import create_default_config

        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / "config.yaml"

            create_default_config(config_path)

            assert config_path.exists()
            assert config_path.is_file()

    def test_create_default_config_creates_parent_directory(self):
        """create_default_config should create parent directories if they don't exist."""
        from foothold_checkpoint.core.config import create_default_config

        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / "subdir" / "nested" / "config.yaml"

            create_default_config(config_path)

            assert config_path.exists()
            assert config_path.parent.exists()

    def test_create_default_config_does_not_overwrite(self):
        """create_default_config should not overwrite an existing config file."""
        from foothold_checkpoint.core.config import create_default_config

        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / "config.yaml"

            # Create a file with custom content
            config_path.write_text("existing: content", encoding='utf-8')
            original_content = config_path.read_text(encoding='utf-8')

            # Try to create default config (should not overwrite)
            create_default_config(config_path)

            # Content should remain unchanged
            assert config_path.read_text(encoding='utf-8') == original_content

    def test_create_default_config_creates_valid_yaml(self):
        """create_default_config should create a valid YAML file."""
        from foothold_checkpoint.core.config import create_default_config

        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / "config.yaml"

            create_default_config(config_path)

            # Should be valid YAML
            with open(config_path, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)

            assert isinstance(data, dict)
            assert 'checkpoints_dir' in data
            assert 'servers' in data
            assert 'campaigns' in data

    def test_create_default_config_loadable_by_load_config(self):
        """Config created by create_default_config should be loadable by load_config."""
        from foothold_checkpoint.core.config import create_default_config, load_config

        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / "config.yaml"

            create_default_config(config_path)

            # Should be loadable without errors
            config = load_config(config_path)

            # Should have valid structure
            assert isinstance(config.checkpoints_dir, Path)
            assert isinstance(config.servers, dict)
            assert isinstance(config.campaigns, dict)


class TestPathExpansion:
    """Test suite for path expansion (tilde and environment variables)."""

    def test_checkpoints_dir_expands_tilde(self):
        """Config should expand ~ in checkpoints_dir to user's home directory."""
        from foothold_checkpoint.core.config import Config, ServerConfig
        import os

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

        # ~ should be expanded to actual home directory
        expected_path = Path.home() / ".foothold-checkpoints"
        assert config.checkpoints_dir == expected_path
        assert "~" not in str(config.checkpoints_dir)

    def test_server_path_expands_tilde(self):
        """ServerConfig path should expand ~ to user's home directory."""
        from foothold_checkpoint.core.config import ServerConfig
        import os

        config = ServerConfig(
            path=Path("~/DCS/Missions/Saves"),
            description="Home server"
        )

        # ~ should be expanded
        expected_path = Path.home() / "DCS" / "Missions" / "Saves"
        assert config.path == expected_path
        assert "~" not in str(config.path)

    def test_checkpoints_dir_expands_environment_variables(self):
        """Config should expand environment variables in checkpoints_dir."""
        from foothold_checkpoint.core.config import Config, ServerConfig
        import os

        # Set a test environment variable
        os.environ["FOOTHOLD_TEST_DIR"] = "C:/TestCheckpoints"

        try:
            config = Config(
                checkpoints_dir=Path("$FOOTHOLD_TEST_DIR/backups"),
                servers={
                    "test": ServerConfig(
                        path=Path("D:/Test"),
                        description="Test"
                    )
                },
                campaigns={"Afghanistan": ["afghanistan"]}
            )

            # Environment variable should be expanded
            assert config.checkpoints_dir == Path("C:/TestCheckpoints/backups")
            assert "$FOOTHOLD_TEST_DIR" not in str(config.checkpoints_dir)
        finally:
            del os.environ["FOOTHOLD_TEST_DIR"]

    def test_server_path_expands_environment_variables(self):
        """ServerConfig path should expand environment variables."""
        from foothold_checkpoint.core.config import ServerConfig
        import os

        # Set a test environment variable
        os.environ["DCS_ROOT"] = "D:/Servers/DCS"

        try:
            config = ServerConfig(
                path=Path("$DCS_ROOT/Missions/Saves"),
                description="DCS server"
            )

            # Environment variable should be expanded
            assert config.path == Path("D:/Servers/DCS/Missions/Saves")
            assert "$DCS_ROOT" not in str(config.path)
        finally:
            del os.environ["DCS_ROOT"]

    def test_path_expansion_combined_tilde_and_envvar(self):
        """Path expansion should handle both tilde and environment variables."""
        from foothold_checkpoint.core.config import ServerConfig
        import os

        # This is a bit contrived but tests both mechanisms
        os.environ["MISSIONS_SUBDIR"] = "Missions"

        try:
            # Start with tilde, followed by env var
            config = ServerConfig(
                path=Path("~/DCS/$MISSIONS_SUBDIR/Saves"),
                description="Combined"
            )

            # Both should be expanded
            expected_path = Path.home() / "DCS" / "Missions" / "Saves"
            assert config.path == expected_path
        finally:
            del os.environ["MISSIONS_SUBDIR"]

    def test_load_config_expands_paths(self):
        """load_config should expand paths from YAML file."""
        from foothold_checkpoint.core.config import load_config
        import os

        # Set environment variable for test
        os.environ["TEST_CHECKPOINT_DIR"] = "C:/TestCheckpoints"

        # Create YAML with unexpanded paths
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump({
                'checkpoints_dir': '~/.foothold-checkpoints',
                'servers': {
                    'test-server': {
                        'path': '$TEST_CHECKPOINT_DIR/Saves',
                        'description': 'Test server with env var'
                    }
                },
                'campaigns': {
                    'Afghanistan': ['afghanistan']
                }
            }, f)
            temp_path = Path(f.name)

        try:
            config = load_config(temp_path)

            # checkpoints_dir should have expanded tilde
            expected_checkpoints = Path.home() / ".foothold-checkpoints"
            assert config.checkpoints_dir == expected_checkpoints

            # Server path should have expanded env var
            assert config.servers["test-server"].path == Path("C:/TestCheckpoints/Saves")
        finally:
            temp_path.unlink()
            del os.environ["TEST_CHECKPOINT_DIR"]

    def test_path_expansion_with_windows_style_envvar(self):
        """Path expansion should handle Windows %ENVVAR% style variables."""
        from foothold_checkpoint.core.config import ServerConfig
        import os

        os.environ["USERPROFILE"] = "C:/Users/TestUser"

        try:
            # Windows style: %USERPROFILE%
            config = ServerConfig(
                path=Path("%USERPROFILE%/DCS/Missions/Saves"),
                description="Windows style"
            )

            # Should be expanded
            assert config.path == Path("C:/Users/TestUser/DCS/Missions/Saves")
            assert "%" not in str(config.path)
        finally:
            if "USERPROFILE" in os.environ:
                del os.environ["USERPROFILE"]


class TestErrorMessages:
    """Test suite for clear and helpful error messages."""

    def test_missing_checkpoints_dir_error_message(self):
        """Config should provide clear error when checkpoints_dir is missing."""
        from foothold_checkpoint.core.config import Config
        from pydantic import ValidationError

        with pytest.raises(ValidationError) as exc_info:
            Config(
                servers={},
                campaigns={}
            )

        # Error should mention the missing field
        error_str = str(exc_info.value)
        assert "checkpoints_dir" in error_str.lower()
        assert "required" in error_str.lower() or "missing" in error_str.lower()

    def test_missing_servers_error_message(self):
        """Config should provide clear error when servers is missing."""
        from foothold_checkpoint.core.config import Config
        from pydantic import ValidationError
        from pathlib import Path

        with pytest.raises(ValidationError) as exc_info:
            Config(
                checkpoints_dir=Path("~/.foothold-checkpoints"),
                campaigns={}
            )

        # Error should mention the missing field
        error_str = str(exc_info.value)
        assert "servers" in error_str.lower()
        assert "required" in error_str.lower() or "missing" in error_str.lower()

    def test_missing_campaigns_error_message(self):
        """Config should provide clear error when campaigns is missing."""
        from foothold_checkpoint.core.config import Config
        from pydantic import ValidationError
        from pathlib import Path

        with pytest.raises(ValidationError) as exc_info:
            Config(
                checkpoints_dir=Path("~/.foothold-checkpoints"),
                servers={}
            )

        # Error should mention the missing field
        error_str = str(exc_info.value)
        assert "campaigns" in error_str.lower()
        assert "required" in error_str.lower() or "missing" in error_str.lower()

    def test_empty_campaign_list_error_message(self):
        """Config should provide clear error when campaign has empty name list."""
        from foothold_checkpoint.core.config import Config, ServerConfig
        from pydantic import ValidationError
        from pathlib import Path

        with pytest.raises(ValidationError) as exc_info:
            Config(
                checkpoints_dir=Path("~/.foothold-checkpoints"),
                servers={
                    "test": ServerConfig(
                        path=Path("D:/Test"),
                        description="Test"
                    )
                },
                campaigns={
                    "Afghanistan": []  # Empty list
                }
            )

        # Error should be clear about the problem
        error_str = str(exc_info.value)
        assert ("empty" in error_str.lower() or "at least 1" in error_str.lower())

    def test_invalid_yaml_error_message(self):
        """load_config should provide clear error for invalid YAML syntax."""
        from foothold_checkpoint.core.config import load_config
        from pathlib import Path
        import yaml

        # Create a file with invalid YAML
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("invalid: yaml: syntax:\n  broken: [unclosed")
            temp_path = Path(f.name)

        try:
            with pytest.raises(yaml.YAMLError) as exc_info:
                load_config(temp_path)

            # YAML library provides the error - we just need to ensure it's raised
            error_str = str(exc_info.value)
            assert len(error_str) > 0  # Should have some error message
        finally:
            temp_path.unlink()

    def test_file_not_found_error_message(self):
        """load_config should provide clear error when file doesn't exist."""
        from foothold_checkpoint.core.config import load_config
        from pathlib import Path

        nonexistent_path = Path("/nonexistent/directory/config.yaml")

        with pytest.raises(FileNotFoundError) as exc_info:
            load_config(nonexistent_path)

        # Error should mention the file path
        error_str = str(exc_info.value)
        assert "config" in error_str.lower() or str(nonexistent_path) in error_str

    def test_missing_server_path_error_message(self):
        """ServerConfig should provide clear error when path is missing."""
        from foothold_checkpoint.core.config import ServerConfig
        from pydantic import ValidationError

        with pytest.raises(ValidationError) as exc_info:
            ServerConfig(description="Test server")

        # Error should mention the missing field
        error_str = str(exc_info.value)
        assert "path" in error_str.lower()
        assert "required" in error_str.lower() or "missing" in error_str.lower()

    def test_missing_server_description_error_message(self):
        """ServerConfig should provide clear error when description is missing."""
        from foothold_checkpoint.core.config import ServerConfig
        from pydantic import ValidationError
        from pathlib import Path

        with pytest.raises(ValidationError) as exc_info:
            ServerConfig(path=Path("D:/Test"))

        # Error should mention the missing field
        error_str = str(exc_info.value)
        assert "description" in error_str.lower()
        assert "required" in error_str.lower() or "missing" in error_str.lower()

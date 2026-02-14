"""Configuration management with Pydantic validation."""

import os
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, Field, field_validator


def expand_path(path: Path) -> Path:
    """Expand tilde and environment variables in path.

    Args:
        path: Path potentially containing ~ or environment variables

    Returns:
        Path: Expanded path with ~ and environment variables resolved

    Examples:
        >>> expand_path(Path("~/.config"))
        Path("/home/user/.config")
        >>> expand_path(Path("$HOME/data"))
        Path("/home/user/data")
        >>> expand_path(Path("%USERPROFILE%/Documents"))
        Path("C:/Users/user/Documents")
    """
    # Convert to string for manipulation
    path_str = str(path)

    # Expand environment variables (supports both $VAR and %VAR% formats)
    path_str = os.path.expandvars(path_str)

    # Create Path and expand tilde
    expanded = Path(path_str).expanduser()

    return expanded


# Default configuration template
DEFAULT_CONFIG_TEMPLATE = """# Foothold Checkpoint Tool - Configuration
#
# This file was auto-generated. Customize it for your setup.

# Directory where checkpoints are stored
checkpoints_dir: ~/.foothold-checkpoints

# DCS servers configuration
servers:
  production-1:
    path: D:\\Servers\\DCS-Production-1\\Missions\\Saves
    description: "Main production server"

  test-server:
    path: D:\\Servers\\DCS-Test\\Missions\\Saves
    description: "Test and development server"

# Campaign name mappings (historical evolution)
# Format: campaign_id: [oldest_name, ..., newest_name]
# The last name in the list is used when restoring checkpoints
campaigns:
  Afghanistan:
    - afghanistan

  Caucasus:
    - CA

  Germany_Modern:
    - GCW_Modern
    - Germany_Modern

  Sinai:
    - SI

  PersianGulf:
    - persiangulf

  Syria:
    - Syria_Extended
"""


class ServerConfig(BaseModel):
    """Configuration for a DCS server.

    Attributes:
        path: Path to server's Missions/Saves directory
        description: Human-readable server description
    """

    path: Path = Field(
        ...,
        description="Path to server's Missions/Saves directory (e.g., 'D:/Servers/DCS/Missions/Saves')",
    )
    description: str = Field(
        ..., description="Human-readable server description (e.g., 'Production server')"
    )

    model_config = {"frozen": True}

    @field_validator("path", mode="before")
    @classmethod
    def expand_server_path(cls, value: Any) -> Path:
        """Expand tilde and environment variables in server path."""
        if isinstance(value, str):
            value = Path(value)
        return expand_path(value)


class Config(BaseModel):
    """Main configuration model.

    Attributes:
        checkpoints_dir: Directory where checkpoint ZIP files are stored
        servers: Map of server names to ServerConfig
        campaigns: Map of campaign names to list of historical names (oldest→newest)
    """

    checkpoints_dir: Path = Field(
        ...,
        description="Directory where checkpoint ZIP files are stored (e.g., '~/.foothold-checkpoints')",
    )
    servers: dict[str, ServerConfig] = Field(
        ...,
        description="Map of server names to ServerConfig. Each server needs 'path' and 'description' fields.",
    )
    campaigns: dict[str, list[str]] = Field(
        ...,
        description="Map of campaign IDs to lists of historical names (oldest→newest). Example: {'Afghanistan': ['afghanistan'], 'Germany_Modern': ['GCW_Modern', 'Germany_Modern']}",
    )

    model_config = {"frozen": True}

    @field_validator("checkpoints_dir", mode="before")
    @classmethod
    def expand_checkpoints_dir(cls, value: Any) -> Path:
        """Expand tilde and environment variables in checkpoints directory."""
        if isinstance(value, str):
            value = Path(value)
        return expand_path(value)

    @field_validator("campaigns")
    @classmethod
    def validate_campaign_names(cls, campaigns: dict[str, list[str]]) -> dict[str, list[str]]:
        """Validate that campaign name lists are not empty."""
        for campaign_id, names in campaigns.items():
            if not names:
                raise ValueError(
                    f"Campaign '{campaign_id}' has an empty name list. "
                    f"Each campaign must have at least one name. "
                    f"Example: '{campaign_id}: [\"campaign_name\"]'"
                )
        return campaigns


def load_config(path: Path) -> Config:
    """Load configuration from YAML file.

    Args:
        path: Path to the YAML configuration file

    Returns:
        Config: Validated configuration object

    Raises:
        FileNotFoundError: If the configuration file doesn't exist
        yaml.YAMLError: If the YAML syntax is invalid
        ValidationError: If the configuration doesn't match the schema
    """
    if not path.exists():
        raise FileNotFoundError(f"Configuration file not found: {path}")

    with open(path, encoding="utf-8") as f:
        data: dict[str, Any] = yaml.safe_load(f)

    # Parse servers section - convert dict to ServerConfig objects
    servers_data = data.get("servers", {})
    servers = {name: ServerConfig(**server_config) for name, server_config in servers_data.items()}

    # Create Config object with validated data
    # Pydantic will validate required fields and raise ValidationError if missing
    return Config(
        checkpoints_dir=data.get("checkpoints_dir"),  # type: ignore[arg-type]
        servers=servers,
        campaigns=data.get("campaigns"),  # type: ignore[arg-type]
    )


def create_default_config(path: Path) -> None:
    """Create a default configuration file with example content.

    Args:
        path: Path where the configuration file should be created

    Note:
        - Creates parent directories if they don't exist
        - Does NOT overwrite existing files
        - Creates a valid YAML file loadable by load_config()
    """
    # Don't overwrite existing files
    if path.exists():
        return

    # Create parent directories if needed
    path.parent.mkdir(parents=True, exist_ok=True)

    # Write default configuration
    path.write_text(DEFAULT_CONFIG_TEMPLATE, encoding="utf-8")

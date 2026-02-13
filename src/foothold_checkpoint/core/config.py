"""Configuration management with Pydantic validation."""

from pathlib import Path
from typing import Any
import yaml
from pydantic import BaseModel, Field, field_validator


class ServerConfig(BaseModel):
    """Configuration for a DCS server.

    Attributes:
        path: Path to server's Missions/Saves directory
        description: Human-readable server description
    """

    path: Path = Field(..., description="Path to server Missions/Saves directory")
    description: str = Field(..., description="Human-readable server description")

    model_config = {"frozen": True}


class Config(BaseModel):
    """Main configuration model.

    Attributes:
        checkpoints_dir: Directory where checkpoint ZIP files are stored
        servers: Map of server names to ServerConfig
        campaigns: Map of campaign names to list of historical names (oldest→newest)
    """

    checkpoints_dir: Path = Field(
        ..., description="Directory where checkpoint ZIP files are stored"
    )
    servers: dict[str, ServerConfig] = Field(
        ..., description="Map of server names to ServerConfig"
    )
    campaigns: dict[str, list[str]] = Field(
        ...,
        description="Map of campaign names to list of historical names (oldest→newest)",
    )

    model_config = {"frozen": True}

    @field_validator("campaigns")
    @classmethod
    def validate_campaign_names(cls, campaigns: dict[str, list[str]]) -> dict[str, list[str]]:
        """Validate that campaign name lists are not empty."""
        for campaign, names in campaigns.items():
            if not names:
                raise ValueError(f"List should have at least 1 item after validation, not 0")
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

    with open(path, 'r', encoding='utf-8') as f:
        data: dict[str, Any] = yaml.safe_load(f)

    # Parse servers section - convert dict to ServerConfig objects
    servers_data = data.get('servers', {})
    servers = {
        name: ServerConfig(**server_config)
        for name, server_config in servers_data.items()
    }

    # Create Config object with validated data
    # Pydantic will validate required fields and raise ValidationError if missing
    return Config(
        checkpoints_dir=data.get('checkpoints_dir'),
        servers=servers,
        campaigns=data.get('campaigns')
    )

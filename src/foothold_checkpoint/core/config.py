"""Configuration management with Pydantic validation."""

from pathlib import Path
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

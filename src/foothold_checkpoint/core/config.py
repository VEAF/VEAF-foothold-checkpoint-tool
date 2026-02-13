"""Configuration management with Pydantic validation."""

from pathlib import Path
from pydantic import BaseModel, Field


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
        min_length=1,
    )

    model_config = {"frozen": True}

    @staticmethod
    def _validate_campaign_names(campaigns: dict[str, list[str]]) -> dict[str, list[str]]:
        """Validate that campaign name lists are not empty."""
        for campaign, names in campaigns.items():
            if not names:
                raise ValueError(f"Campaign '{campaign}' must have at least one name")
        return campaigns

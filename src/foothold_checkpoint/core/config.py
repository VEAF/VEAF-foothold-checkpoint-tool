"""Configuration management with Pydantic validation."""

import os
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, Field, field_validator, model_validator


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

# Campaign configurations with explicit file lists
# Each campaign defines all known file names for each file type
campaigns:
  afghanistan:
    display_name: "Afghanistan"
    files:
      persistence:
        - "foothold_afghanistan.lua"
      ctld_save:
        - "foothold_afghanistan_CTLD_Save.csv"
      ctld_farps:
        - "foothold_afghanistan_CTLD_FARPS.csv"
      storage:
        files:
          - "foothold_afghanistan_storage.csv"
        optional: true

  caucasus:
    display_name: "Caucasus"
    files:
      persistence:
        - "FootHold_CA_v0.2.lua"
      ctld_save:
        - "FootHold_CA_v0.2_CTLD_Save.csv"
        - "FootHold_CA_CTLD_Save_Modern.csv"
      ctld_farps:
        - "FootHold_CA_v0.2_CTLD_FARPS.csv"
        - "Foothold_CA_CTLD_FARPS_Modern.csv"
      storage:
        files:
          - "FootHold_CA_v0.2_storage.csv"
        optional: true

  germany_modern:
    display_name: "Germany Modern"
    files:
      persistence:
        - "FootHold_GCW_Modern.lua"
        - "FootHold_Germany_Modern_V0.1.lua"
      ctld_save:
        - "FootHold_GCW_Modern_CTLD_Save.csv"
        - "FootHold_Germany_Modern_V0.1_CTLD_Save.csv"
      ctld_farps:
        - "FootHold_GCW_Modern_CTLD_FARPS.csv"
        - "FootHold_Germany_Modern_V0.1_CTLD_FARPS.csv"
      storage:
        files:
          - "FootHold_GCW_Modern_storage.csv"
          - "FootHold_Germany_Modern_V0.1_storage.csv"
        optional: true

  sinai:
    display_name: "Sinai"
    files:
      persistence:
        - "FootHold_SI_v0.3.lua"
      ctld_save:
        - "FootHold_SI_v0.3_CTLD_Save.csv"
      ctld_farps:
        - "FootHold_SI_v0.3_CTLD_FARPS.csv"
      storage:
        files:
          - "FootHold_SI_v0.3_storage.csv"
        optional: true

  persiangulf:
    display_name: "Persian Gulf"
    files:
      persistence:
        - "foothold_persiangulf.lua"
      ctld_save:
        - "FootHold_PG_CTLD_Save_Modern.csv"
      ctld_farps:
        - "Foothold_PG_CTLD_FARPS_Modern.csv"
      storage:
        optional: true

  syria:
    display_name: "Syria"
    files:
      persistence:
        - "footholdSyria_Extended_0.1.lua"
      ctld_save:
        - "FootHold_SY_Extended_CTLD_Modern.csv"
      ctld_farps:
        - "Foothold_SY_Extended_CTLD_FARPS_Modern.csv"
      storage:
        optional: true
"""


class CampaignFileType(BaseModel):
    """Configuration for a specific file type in a campaign.

    Defines the list of known file names for a file type (e.g., persistence, ctld_save)
    and whether the file type is optional.

    Attributes:
        files: List of known file names for this type (historical and current)
        optional: Whether this file type is optional (default: False)

    Examples:
        >>> # Required persistence files
        >>> CampaignFileType(files=["foothold_afghanistan.lua"])

        >>> # Optional storage files
        >>> CampaignFileType(files=["foothold_afghanistan_storage.csv"], optional=True)
    """

    files: list[str] = Field(
        default_factory=list,
        description="List of known file names for this type (e.g., ['FootHold_CA_v0.2.lua', 'Foothold_CA.lua'])",
    )
    optional: bool = Field(
        default=False, description="Whether this file type is optional (default: False)"
    )

    model_config = {"frozen": True}

    @model_validator(mode="after")
    def validate_file_list(self) -> "CampaignFileType":
        """Validate that non-optional file types have at least one file."""
        if not self.optional and not self.files:
            raise ValueError("Required file types must have at least one file in the list")
        return self


class CampaignFileList(BaseModel):
    """File lists for all file types in a campaign.

    Defines the expected files for each file type (persistence, ctld_save, ctld_farps, storage).
    Each file type can have multiple file names to support historical naming changes.

    Attributes:
        persistence: Main campaign persistence file (.lua)
        ctld_save: CTLD save data file (_CTLD_Save.csv)
        ctld_farps: CTLD FARP locations file (_CTLD_FARPS.csv)
        storage: Campaign storage file (_storage.csv)

    Examples:
        >>> files = CampaignFileList(
        ...     persistence=CampaignFileType(files=["foothold_afghan.lua"]),
        ...     ctld_save=CampaignFileType(files=["foothold_afghan_CTLD_Save.csv"]),
        ...     ctld_farps=CampaignFileType(files=["foothold_afghan_CTLD_FARPS.csv"]),
        ...     storage=CampaignFileType(files=["foothold_afghan_storage.csv"], optional=True)
        ... )
    """

    persistence: CampaignFileType = Field(..., description="Main campaign persistence file (.lua)")
    ctld_save: CampaignFileType = Field(..., description="CTLD save data file (_CTLD_Save.csv)")
    ctld_farps: CampaignFileType = Field(
        ..., description="CTLD FARP locations file (_CTLD_FARPS.csv)"
    )
    storage: CampaignFileType = Field(..., description="Campaign storage file (_storage.csv)")

    model_config = {"frozen": True}


class CampaignConfig(BaseModel):
    """Configuration for a campaign.

    Defines the display name and all known file names for a campaign,
    organized by file type.

    Attributes:
        display_name: User-friendly name for display in UI/messages
        files: File lists organized by file type

    Examples:
        >>> config = CampaignConfig(
        ...     display_name="Caucasus",
        ...     files=CampaignFileList(
        ...         persistence=CampaignFileType(files=["FootHold_CA_v0.2.lua"]),
        ...         ctld_save=CampaignFileType(files=["FootHold_CA_v0.2_CTLD_Save.csv"]),
        ...         ctld_farps=CampaignFileType(files=["FootHold_CA_v0.2_CTLD_FARPS.csv"]),
        ...         storage=CampaignFileType(files=["FootHold_CA_v0.2_storage.csv"], optional=True)
        ...     )
        ... )
    """

    display_name: str = Field(
        ...,
        description="User-friendly name for display in UI/messages (e.g., 'Caucasus', 'Germany Modern')",
    )
    files: CampaignFileList = Field(..., description="File lists organized by file type")

    model_config = {"frozen": True}


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
        campaigns: Map of campaign IDs to CampaignConfig with display names and file lists
    """

    checkpoints_dir: Path = Field(
        ...,
        description="Directory where checkpoint ZIP files are stored (e.g., '~/.foothold-checkpoints')",
    )
    servers: dict[str, ServerConfig] = Field(
        ...,
        description="Map of server names to ServerConfig. Each server needs 'path' and 'description' fields.",
    )
    campaigns: dict[str, CampaignConfig] = Field(
        ...,
        description="Map of campaign IDs to CampaignConfig with display name and file lists. Each campaign defines all known file names.",
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
    def validate_campaigns(cls, campaigns: dict[str, CampaignConfig]) -> dict[str, CampaignConfig]:
        """Validate that at least one campaign is configured."""
        if not campaigns:
            raise ValueError(
                "At least one campaign must be configured. "
                "Add campaign definitions to the 'campaigns' section in config.yaml."
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

    # Parse campaigns section - convert dict to CampaignConfig objects
    campaigns_data = data.get("campaigns", {})
    campaigns: dict[str, CampaignConfig] = {}
    for campaign_id, campaign_config in campaigns_data.items():
        # Validate that campaign_config is a dictionary
        if not isinstance(campaign_config, dict):
            raise ValueError(
                f"Campaign '{campaign_id}' must be a dictionary with 'display_name' and 'files' fields, "
                f"got {type(campaign_config).__name__} instead"
            )

        # Parse files section for each campaign
        files_data = campaign_config.get("files", {})
        file_types: dict[str, Any] = {}

        for file_type, file_spec in files_data.items():
            # file_spec can be:
            # 1. A list of files: ["file1.lua", "file2.lua"]
            # 2. A dict with optional flag: {optional: true} or {optional: true, 0: ["file.lua"]}
            # Note: YAML treats keys starting with numbers specially, so files might be under key 0
            if isinstance(file_spec, list):
                # Just a file list (required by default)
                file_types[file_type] = CampaignFileType(files=file_spec, optional=False)
            elif isinstance(file_spec, dict):
                # Has optional flag and potentially file list under various keys
                optional = file_spec.get("optional", False)
                # Try to find file list under common keys
                files_list = []
                if "files" in file_spec:
                    files_list = file_spec["files"] if isinstance(file_spec["files"], list) else []
                elif 0 in file_spec:
                    # YAML sometimes puts list items under numeric keys
                    files_list = file_spec[0] if isinstance(file_spec[0], list) else [file_spec[0]]
                # Allow empty file list only if optional
                file_types[file_type] = CampaignFileType(files=files_list, optional=optional)
            else:
                raise ValueError(
                    f"Invalid file type specification for campaign '{campaign_id}', "
                    f"file type '{file_type}': expected list or dict with 'optional' flag"
                )

        campaigns[campaign_id] = CampaignConfig(
            display_name=campaign_config.get("display_name", campaign_id),
            files=CampaignFileList(**file_types),
        )

    # Get checkpoints_dir with type assertion
    checkpoints_dir_raw = data.get("checkpoints_dir")
    if checkpoints_dir_raw is None:
        raise ValueError("Missing required field: checkpoints_dir")
    checkpoints_dir = (
        Path(checkpoints_dir_raw)
        if not isinstance(checkpoints_dir_raw, Path)
        else checkpoints_dir_raw
    )

    # Create Config object with validated data
    # Pydantic will validate required fields and raise ValidationError if missing
    return Config(
        checkpoints_dir=checkpoints_dir,
        servers=servers,
        campaigns=campaigns,
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

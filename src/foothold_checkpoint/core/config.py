"""Configuration management with Pydantic validation."""

import os
from pathlib import Path
from typing import Any

# Use ruamel.yaml for compatibility with DCSServerBot
try:
    # Try ruamel.yaml first (DCSServerBot standard)
    from ruamel.yaml import YAML

    _yaml = YAML()
    _yaml.preserve_quotes = True
    _yaml.default_flow_style = False
    YAML_BACKEND = "ruamel"
except ImportError:
    # Fallback to PyYAML (standalone CLI mode)
    import yaml as _pyyaml

    YAML_BACKEND = "pyyaml"

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
    return Path(path_str).expanduser()


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
        campaigns_file: Optional path to external campaigns.yaml file (DRY configuration for CLI+plugin)
    """

    checkpoints_dir: Path = Field(
        ...,
        description="Directory where checkpoint ZIP files are stored (e.g., '~/.foothold-checkpoints')",
    )
    servers: dict[str, ServerConfig] | None = Field(
        default=None,
        description="Map of server names to ServerConfig. Each server needs 'path' and 'description' fields. Optional for plugin mode.",
    )
    campaigns: dict[str, CampaignConfig] | None = Field(
        default=None,
        description="Map of campaign IDs to CampaignConfig with display name and file lists. Each campaign defines all known file names. If campaigns_file is specified, campaigns are loaded from that file instead.",
    )
    campaigns_file: Path | None = Field(
        default=None,
        description="Path to external campaigns.yaml file containing campaign definitions. Enables DRY configuration shared between CLI and plugin.",
    )

    model_config = {"frozen": True}

    @field_validator("checkpoints_dir", mode="before")
    @classmethod
    def expand_checkpoints_dir(cls, value: Any) -> Path:
        """Expand tilde and environment variables in checkpoints directory."""
        if isinstance(value, str):
            value = Path(value)
        return expand_path(value)

    @field_validator("campaigns_file", mode="before")
    @classmethod
    def expand_campaigns_file(cls, value: Any) -> Path | None:
        """Expand tilde and environment variables in campaigns file path."""
        if value is None:
            return None
        if isinstance(value, str):
            value = Path(value)
        return expand_path(value)

    @model_validator(mode="after")
    def validate_campaigns_source(self) -> "Config":
        """Validate that campaigns are provided either inline or via campaigns_file."""
        if not self.campaigns and not self.campaigns_file:
            raise ValueError(
                "At least one campaign must be configured. "
                "Either define campaigns inline in config.yaml or specify campaigns_file path."
            )
        if self.campaigns and self.campaigns_file:
            raise ValueError(
                "Cannot specify both 'campaigns' and 'campaigns_file'. "
                "Use campaigns_file to reference external campaigns.yaml (recommended for v2.0+), "
                "or define campaigns inline (legacy v1.x format)."
            )
        return self


def load_campaigns(campaigns_file: Path) -> dict[str, CampaignConfig]:
    """Load campaign definitions from external YAML file.

    Args:
        campaigns_file: Path to campaigns.yaml file

    Returns:
        dict[str, CampaignConfig]: Map of campaign IDs to CampaignConfig objects

    Raises:
        FileNotFoundError: If campaigns file doesn't exist
        yaml.YAMLError: If YAML syntax is invalid
        ValidationError: If campaigns don't match schema

    Example:
        >>> campaigns = load_campaigns(Path("~/.foothold-checkpoint/campaigns.yaml"))
        >>> print(campaigns["afghanistan"].display_name)
        Afghanistan
    """
    if not campaigns_file.exists():
        raise FileNotFoundError(
            f"Campaigns file not found: {campaigns_file}\n"
            "Create campaigns.yaml with campaign definitions or specify inline campaigns in config.yaml."
        )

    with open(campaigns_file, encoding="utf-8") as f:
        campaigns_file_data: dict[str, Any]
        if YAML_BACKEND == "ruamel":  # noqa: SIM108
            campaigns_file_data = _yaml.load(f)
        else:
            campaigns_file_data = _pyyaml.safe_load(f)

    campaigns_data = campaigns_file_data.get("campaigns", {})
    if not campaigns_data:
        raise ValueError(
            f"No campaigns defined in {campaigns_file}. "
            "File must contain 'campaigns' section with at least one campaign."
        )

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
        config_file_data: dict[str, Any]
        if YAML_BACKEND == "ruamel":  # noqa: SIM108
            config_file_data = _yaml.load(f)
        else:
            config_file_data = _pyyaml.safe_load(f)

    # Parse servers section - convert dict to ServerConfig objects (optional for plugin mode)
    servers_data = config_file_data.get("servers", {})
    servers = (
        {name: ServerConfig(**server_config) for name, server_config in servers_data.items()}
        if servers_data
        else None
    )

    # Check if campaigns should be loaded from external file or inline
    campaigns_file_raw = config_file_data.get("campaigns_file")
    campaigns: dict[str, CampaignConfig] | None = None
    campaigns_file: Path | None = None

    if campaigns_file_raw:
        # Load campaigns from external file
        campaigns_file = (
            Path(campaigns_file_raw) if isinstance(campaigns_file_raw, str) else campaigns_file_raw
        )
        # Resolve relative paths relative to config file location
        if campaigns_file and not campaigns_file.is_absolute():
            campaigns_file = (path.parent / campaigns_file).resolve()
        if campaigns_file is not None:
            campaigns = load_campaigns(campaigns_file)
    elif campaigns_data := config_file_data.get("campaigns", {}):
        campaigns_inline: dict[str, CampaignConfig] = {}
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
                if isinstance(file_spec, list):
                    # Just a file list (required by default)
                    file_types[file_type] = CampaignFileType(files=file_spec, optional=False)
                elif isinstance(file_spec, dict):
                    # Has optional flag and potentially file list under various keys
                    optional = file_spec.get("optional", False)
                    # Try to find file list under common keys
                    files_list = []
                    if "files" in file_spec:
                        files_list = (
                            file_spec["files"] if isinstance(file_spec["files"], list) else []
                        )
                    elif 0 in file_spec:
                        # YAML sometimes puts list items under numeric keys
                        files_list = (
                            file_spec[0] if isinstance(file_spec[0], list) else [file_spec[0]]
                        )
                    # Allow empty file list only if optional
                    file_types[file_type] = CampaignFileType(files=files_list, optional=optional)
                else:
                    raise ValueError(
                        f"Invalid file type specification for campaign '{campaign_id}', "
                        f"file type '{file_type}': expected list or dict with 'optional' flag"
                    )

            campaigns_inline[campaign_id] = CampaignConfig(
                display_name=campaign_config.get("display_name", campaign_id),
                files=CampaignFileList(**file_types),
            )
        campaigns = campaigns_inline

    # Get checkpoints_dir with type assertion
    checkpoints_dir_raw = config_file_data.get("checkpoints_dir")
    if checkpoints_dir_raw is None:
        raise ValueError("Missing required field: checkpoints_dir")
    checkpoints_dir = (
        checkpoints_dir_raw if isinstance(checkpoints_dir_raw, Path) else Path(checkpoints_dir_raw)
    )

    # Create Config object with validated data
    # Pydantic will validate required fields and raise ValidationError if missing
    return Config(
        checkpoints_dir=checkpoints_dir,
        servers=servers,
        campaigns=campaigns,
        campaigns_file=campaigns_file,
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

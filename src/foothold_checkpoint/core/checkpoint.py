"""Checkpoint metadata and storage operations."""

import hashlib
import json
from datetime import datetime
from pathlib import Path
from typing import Union
from pydantic import BaseModel, Field, field_validator, ValidationError


class CheckpointMetadata(BaseModel):
    """Metadata for a Foothold campaign checkpoint.

    Stores information about a checkpoint including campaign name, server,
    creation timestamp, file checksums, and optional user-provided metadata.

    Attributes:
        campaign_name: Name of the campaign (normalized, lowercase)
        server_name: Name of the server where checkpoint was created
        created_at: Timestamp when checkpoint was created (timezone-aware)
        files: Dictionary mapping filenames to their SHA-256 checksums
        name: Optional user-provided name for the checkpoint
        comment: Optional user-provided comment/description

    Examples:
        >>> from datetime import datetime, timezone
        >>> metadata = CheckpointMetadata(
        ...     campaign_name="afghanistan",
        ...     server_name="production-1",
        ...     created_at=datetime(2024, 1, 15, 10, 30, 0, tzinfo=timezone.utc),
        ...     files={
        ...         "foothold_afghanistan.lua": "sha256:abc123...",
        ...         "foothold_afghanistan_storage.csv": "sha256:def456..."
        ...     },
        ...     name="Before major update",
        ...     comment="Checkpoint before implementing new features"
        ... )
    """

    campaign_name: str = Field(
        ...,
        description="Campaign name (normalized, lowercase). Must not be empty."
    )
    server_name: str = Field(
        ...,
        description="Server name where checkpoint was created. Must not be empty."
    )
    created_at: datetime = Field(
        ...,
        description="Timestamp when checkpoint was created. Should be timezone-aware (UTC recommended)."
    )
    files: dict[str, str] = Field(
        ...,
        description="Dictionary mapping filenames to their SHA-256 checksums. Format: {'filename': 'sha256:checksum', ...}"
    )
    name: str | None = Field(
        None,
        description="Optional user-provided name for the checkpoint (e.g., 'Before major update')"
    )
    comment: str | None = Field(
        None,
        description="Optional user-provided comment or description for the checkpoint"
    )

    model_config = {"frozen": True}

    @field_validator("campaign_name")
    @classmethod
    def validate_campaign_name(cls, value: str) -> str:
        """Validate that campaign_name is not empty."""
        if not value or not value.strip():
            raise ValueError(
                "Campaign name must not be empty. "
                "Provide a valid campaign name (e.g., 'afghanistan', 'syria')."
            )
        return value

    @field_validator("server_name")
    @classmethod
    def validate_server_name(cls, value: str) -> str:
        """Validate that server_name is not empty."""
        if not value or not value.strip():
            raise ValueError(
                "Server name must not be empty. "
                "Provide a valid server name (e.g., 'production-1', 'test-server')."
            )
        return value


def compute_file_checksum(file_path: Union[str, Path]) -> str:
    """Compute SHA-256 checksum for a file.

    Reads the file in chunks to efficiently handle large files without
    loading the entire content into memory.

    Args:
        file_path: Path to the file (string or Path object).

    Returns:
        str: SHA-256 checksum in the format "sha256:hexdigest".

    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If the path points to a directory instead of a file.

    Examples:
        >>> checksum = compute_file_checksum("foothold_afghanistan.lua")
        >>> checksum
        'sha256:abc123def456...'

        >>> # Works with Path objects
        >>> from pathlib import Path
        >>> checksum = compute_file_checksum(Path("foothold_syria.lua"))
    """
    # Convert to Path if string
    path = Path(file_path) if isinstance(file_path, str) else file_path

    # Check if file exists
    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")

    # Check if path is a file (not a directory)
    if not path.is_file():
        raise ValueError(f"Path is not a file: {path}")

    # Compute SHA-256 checksum by reading in chunks
    sha256_hash = hashlib.sha256()
    chunk_size = 8192  # 8 KB chunks

    with open(path, "rb") as f:
        while chunk := f.read(chunk_size):
            sha256_hash.update(chunk)

    # Return checksum in format "sha256:hexdigest"
    return f"sha256:{sha256_hash.hexdigest()}"


def save_metadata(metadata: CheckpointMetadata, json_path: Union[str, Path]) -> None:
    """Save checkpoint metadata to a JSON file.

    Serializes the metadata to JSON format with proper datetime handling
    (ISO 8601 format with timezone). Creates parent directories if needed.

    Args:
        metadata: CheckpointMetadata object to serialize.
        json_path: Path where the JSON file should be saved (string or Path).

    Examples:
        >>> from datetime import datetime, timezone
        >>> metadata = CheckpointMetadata(
        ...     campaign_name="afghanistan",
        ...     server_name="production-1",
        ...     created_at=datetime(2024, 1, 15, 10, 30, 0, tzinfo=timezone.utc),
        ...     files={"foothold_afghanistan.lua": "sha256:abc123..."}
        ... )
        >>> save_metadata(metadata, "checkpoint/metadata.json")
    """
    # Convert to Path if string
    path = Path(json_path) if isinstance(json_path, str) else json_path

    # Create parent directories if needed
    path.parent.mkdir(parents=True, exist_ok=True)

    # Serialize metadata to dict with proper JSON handling
    # mode='json' ensures datetime is serialized to ISO 8601 string
    data = metadata.model_dump(mode='json')

    # Write to JSON file with pretty formatting
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def load_metadata(json_path: Union[str, Path]) -> CheckpointMetadata:
    """Load checkpoint metadata from a JSON file.

    Deserializes JSON file to a CheckpointMetadata object with validation.
    Handles datetime parsing from ISO 8601 format.

    Args:
        json_path: Path to the JSON file (string or Path).

    Returns:
        CheckpointMetadata: Validated metadata object.

    Raises:
        FileNotFoundError: If the JSON file does not exist.
        ValueError: If the JSON syntax is invalid.
        ValidationError: If the data doesn't match the metadata schema.

    Examples:
        >>> metadata = load_metadata("checkpoint/metadata.json")
        >>> metadata.campaign_name
        'afghanistan'
    """
    # Convert to Path if string
    path = Path(json_path) if isinstance(json_path, str) else json_path

    # Check if file exists
    if not path.exists():
        raise FileNotFoundError(f"Metadata file not found: {path}")

    # Read and parse JSON
    try:
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON in metadata file: {e}")

    # Validate and create CheckpointMetadata object
    # Pydantic will automatically parse ISO 8601 datetime strings
    return CheckpointMetadata.model_validate(data)

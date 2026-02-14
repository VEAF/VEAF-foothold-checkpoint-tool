"""Checkpoint metadata and storage operations."""

import hashlib
import json
import zipfile
from collections.abc import Callable, Sequence
from datetime import datetime, timezone
from pathlib import Path
from typing import cast

from pydantic import BaseModel, Field, field_validator


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
        ..., description="Campaign name (normalized, lowercase). Must not be empty."
    )
    server_name: str = Field(
        ..., description="Server name where checkpoint was created. Must not be empty."
    )
    created_at: datetime = Field(
        ...,
        description="Timestamp when checkpoint was created. Should be timezone-aware (UTC recommended).",
    )
    files: dict[str, str] = Field(
        ...,
        description="Dictionary mapping filenames to their SHA-256 checksums. Format: {'filename': 'sha256:checksum', ...}",
    )
    name: str | None = Field(
        None,
        description="Optional user-provided name for the checkpoint (e.g., 'Before major update')",
    )
    comment: str | None = Field(
        None, description="Optional user-provided comment or description for the checkpoint"
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


def compute_file_checksum(file_path: str | Path) -> str:
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


def save_metadata(metadata: CheckpointMetadata, json_path: str | Path) -> None:
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
    data = metadata.model_dump(mode="json")

    # Write to JSON file with pretty formatting
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def load_metadata(json_path: str | Path) -> CheckpointMetadata:
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
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON in metadata file: {e}") from e

    # Validate and create CheckpointMetadata object
    # Pydantic will automatically parse ISO 8601 datetime strings
    return CheckpointMetadata.model_validate(data)


def generate_checkpoint_filename(campaign_name: str, created_at: datetime | None = None) -> str:
    """Generate a checkpoint filename with timestamp.

    Creates a filename in the format: campaign_YYYY-MM-DD_HH-MM-SS.zip

    The timestamp ensures uniqueness when multiple checkpoints are created
    for the same campaign. Uses UTC timezone for consistency.

    Args:
        campaign_name: Name of the campaign (e.g., "afghanistan", "germany_modern").
        created_at: Timestamp for the checkpoint. If None, uses current UTC time.

    Returns:
        str: Checkpoint filename (e.g., "afghanistan_2024-01-15_10-30-45.zip").

    Examples:
        >>> from datetime import datetime, timezone
        >>> timestamp = datetime(2024, 1, 15, 10, 30, 45, tzinfo=timezone.utc)
        >>> generate_checkpoint_filename("afghanistan", timestamp)
        'afghanistan_2024-01-15_10-30-45.zip'

        >>> # Use current time if not provided
        >>> generate_checkpoint_filename("syria")
        'syria_2024-02-14_15-45-30.zip'  # Current timestamp
    """
    # Use current UTC time if not provided
    if created_at is None:
        created_at = datetime.now(timezone.utc)

    # Format: campaign_YYYY-MM-DD_HH-MM-SS.zip
    timestamp_str = created_at.strftime("%Y-%m-%d_%H-%M-%S")
    filename = f"{campaign_name}_{timestamp_str}.zip"

    return filename


def create_checkpoint(
    campaign_name: str,
    server_name: str,
    campaign_files: Sequence[str | Path],
    output_dir: str | Path,
    created_at: datetime | None = None,
    name: str | None = None,
    comment: str | None = None,
    progress_callback: Callable[[str, int, int], None] | None = None,
) -> Path:
    """Create a checkpoint ZIP archive with campaign files and metadata.

    Creates a ZIP file containing:
    - All campaign files (preserving original filenames)
    - metadata.json with checksums and metadata
    - Foothold_Ranks.lua if included in campaign_files

    Args:
        campaign_name: Name of the campaign (e.g., "afghanistan").
        server_name: Name of the server (e.g., "production-1").
        campaign_files: List of file paths to include in checkpoint.
        output_dir: Directory where the ZIP file will be created.
        created_at: Checkpoint timestamp. If None, uses current UTC time.
        name: Optional user-provided name for the checkpoint.
        comment: Optional user-provided comment.
        progress_callback: Optional callback for progress tracking.
                          Called with (message, current, total) during creation.
                          Example: callback("Computing checksums", 1, 3)

    Returns:
        Path: Path to the created ZIP file.

    Raises:
        FileNotFoundError: If any source file doesn't exist.

    Examples:
        >>> from pathlib import Path
        >>> files = [
        ...     Path("foothold_afghanistan.lua"),
        ...     Path("foothold_afghanistan_storage.csv")
        ... ]
        >>> zip_path = create_checkpoint(
        ...     campaign_name="afghanistan",
        ...     server_name="production-1",
        ...     campaign_files=files,
        ...     output_dir=Path("checkpoints")
        ... )
        >>> zip_path
        Path('checkpoints/afghanistan_2024-01-15_10-30-45.zip')
    """
    # Use current UTC time if not provided
    if created_at is None:
        created_at = datetime.now(timezone.utc)

    # Convert paths to Path objects
    output_dir = Path(output_dir) if isinstance(output_dir, str) else output_dir
    # Convert all campaign files to Path objects (str -> Path, leave Path as-is)
    # We need to cast because mypy can't infer that all items become Path after the comprehension
    campaign_files = cast(
        list[Path], [Path(f) if isinstance(f, str) else f for f in campaign_files]
    )

    # Validate that all source files exist
    for file_path in campaign_files:
        if not file_path.exists():
            raise FileNotFoundError(f"Source file not found: {file_path}")

    # Compute checksums for all files
    files_checksums: dict[str, str] = {}
    total_files = len(campaign_files)

    for index, file_path in enumerate(campaign_files, start=1):
        # Report progress if callback provided
        if progress_callback:
            progress_callback(f"Computing checksum for {file_path.name}", index, total_files)

        checksum = compute_file_checksum(file_path)
        # Store with just the filename (not full path)
        files_checksums[file_path.name] = checksum

    # Create metadata object
    metadata = CheckpointMetadata(
        campaign_name=campaign_name,
        server_name=server_name,
        created_at=created_at,
        files=files_checksums,
        name=name,
        comment=comment,
    )

    # Generate ZIP filename
    zip_filename = generate_checkpoint_filename(campaign_name, created_at)

    # Create output directory if it doesn't exist
    output_dir.mkdir(parents=True, exist_ok=True)

    # Full path to ZIP file
    zip_path = output_dir / zip_filename

    # Report progress for ZIP creation
    if progress_callback:
        progress_callback("Creating ZIP archive", total_files, total_files)

    # Create ZIP archive
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        # Add all campaign files
        for file_path in campaign_files:
            # Add file with just its name (not full path)
            zf.write(file_path, arcname=file_path.name)

        # Create and add metadata.json
        metadata_json = metadata.model_dump(mode="json")
        metadata_str = json.dumps(metadata_json, indent=2, ensure_ascii=False)
        zf.writestr("metadata.json", metadata_str)

    return zip_path

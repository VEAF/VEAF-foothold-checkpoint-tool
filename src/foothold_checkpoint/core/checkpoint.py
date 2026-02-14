"""Checkpoint metadata and storage operations."""

from datetime import datetime
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

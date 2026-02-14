"""Tests for checkpoint metadata and storage."""

from datetime import datetime, timezone
from pathlib import Path
import pytest
from pydantic import ValidationError


class TestCheckpointMetadata:
    """Test suite for checkpoint metadata structure."""

    def test_metadata_required_fields(self):
        """Should require campaign_name, server_name, created_at, and files."""
        from foothold_checkpoint.core.checkpoint import CheckpointMetadata

        metadata = CheckpointMetadata(
            campaign_name="afghanistan",
            server_name="production-1",
            created_at=datetime(2024, 1, 15, 10, 30, 0, tzinfo=timezone.utc),
            files={
                "foothold_afghanistan.lua": "abc123...",
                "foothold_afghanistan_storage.csv": "def456..."
            }
        )

        assert metadata.campaign_name == "afghanistan"
        assert metadata.server_name == "production-1"
        assert metadata.created_at == datetime(2024, 1, 15, 10, 30, 0, tzinfo=timezone.utc)
        assert len(metadata.files) == 2

    def test_metadata_optional_fields(self):
        """Should support optional name and comment fields."""
        from foothold_checkpoint.core.checkpoint import CheckpointMetadata

        metadata = CheckpointMetadata(
            campaign_name="afghanistan",
            server_name="production-1",
            created_at=datetime(2024, 1, 15, 10, 30, 0, tzinfo=timezone.utc),
            files={"foothold_afghanistan.lua": "abc123..."},
            name="Before major update",
            comment="Checkpoint created before implementing new features"
        )

        assert metadata.name == "Before major update"
        assert metadata.comment == "Checkpoint created before implementing new features"

    def test_metadata_optional_fields_default_none(self):
        """Should default optional fields to None."""
        from foothold_checkpoint.core.checkpoint import CheckpointMetadata

        metadata = CheckpointMetadata(
            campaign_name="afghanistan",
            server_name="production-1",
            created_at=datetime(2024, 1, 15, 10, 30, 0, tzinfo=timezone.utc),
            files={"foothold_afghanistan.lua": "abc123..."}
        )

        assert metadata.name is None
        assert metadata.comment is None

    def test_metadata_missing_required_field_raises_error(self):
        """Should raise validation error when required fields are missing."""
        from foothold_checkpoint.core.checkpoint import CheckpointMetadata
        from pydantic import ValidationError

        with pytest.raises(ValidationError) as exc_info:
            CheckpointMetadata(
                campaign_name="afghanistan",
                server_name="production-1",
                # Missing created_at and files
            )

        error = exc_info.value
        assert "created_at" in str(error)
        assert "files" in str(error)

    def test_metadata_empty_files_dict(self):
        """Should allow empty files dict (edge case for validation)."""
        from foothold_checkpoint.core.checkpoint import CheckpointMetadata

        metadata = CheckpointMetadata(
            campaign_name="afghanistan",
            server_name="production-1",
            created_at=datetime(2024, 1, 15, 10, 30, 0, tzinfo=timezone.utc),
            files={}
        )

        assert metadata.files == {}

    def test_metadata_immutable(self):
        """Should be immutable (frozen)."""
        from foothold_checkpoint.core.checkpoint import CheckpointMetadata

        metadata = CheckpointMetadata(
            campaign_name="afghanistan",
            server_name="production-1",
            created_at=datetime(2024, 1, 15, 10, 30, 0, tzinfo=timezone.utc),
            files={"foothold_afghanistan.lua": "abc123..."}
        )

        with pytest.raises(ValidationError):
            metadata.campaign_name = "syria"

    def test_metadata_files_dict_format(self):
        """Should store files as dict mapping filename to checksum."""
        from foothold_checkpoint.core.checkpoint import CheckpointMetadata

        files = {
            "foothold_afghanistan.lua": "sha256:abc123def456...",
            "foothold_afghanistan_storage.csv": "sha256:789012abc345...",
            "foothold_afghanistan_CTLD_FARPS.csv": "sha256:def789ghi012..."
        }

        metadata = CheckpointMetadata(
            campaign_name="afghanistan",
            server_name="production-1",
            created_at=datetime(2024, 1, 15, 10, 30, 0, tzinfo=timezone.utc),
            files=files
        )

        assert metadata.files == files
        assert metadata.files["foothold_afghanistan.lua"] == "sha256:abc123def456..."

    def test_metadata_campaign_name_validation(self):
        """Should validate campaign_name is not empty."""
        from foothold_checkpoint.core.checkpoint import CheckpointMetadata
        from pydantic import ValidationError

        with pytest.raises(ValidationError) as exc_info:
            CheckpointMetadata(
                campaign_name="",  # Empty string
                server_name="production-1",
                created_at=datetime(2024, 1, 15, 10, 30, 0, tzinfo=timezone.utc),
                files={"foothold_afghanistan.lua": "abc123..."}
            )

        assert "campaign_name" in str(exc_info.value)

    def test_metadata_server_name_validation(self):
        """Should validate server_name is not empty."""
        from foothold_checkpoint.core.checkpoint import CheckpointMetadata
        from pydantic import ValidationError

        with pytest.raises(ValidationError) as exc_info:
            CheckpointMetadata(
                campaign_name="afghanistan",
                server_name="",  # Empty string
                created_at=datetime(2024, 1, 15, 10, 30, 0, tzinfo=timezone.utc),
                files={"foothold_afghanistan.lua": "abc123..."}
            )

        assert "server_name" in str(exc_info.value)

    def test_metadata_timezone_aware_datetime(self):
        """Should handle timezone-aware datetime objects."""
        from foothold_checkpoint.core.checkpoint import CheckpointMetadata

        # UTC timezone
        utc_time = datetime(2024, 1, 15, 10, 30, 0, tzinfo=timezone.utc)
        metadata = CheckpointMetadata(
            campaign_name="afghanistan",
            server_name="production-1",
            created_at=utc_time,
            files={"foothold_afghanistan.lua": "abc123..."}
        )

        assert metadata.created_at == utc_time
        assert metadata.created_at.tzinfo == timezone.utc

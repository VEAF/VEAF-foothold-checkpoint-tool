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


class TestChecksumComputation:
    """Test suite for SHA-256 checksum computation."""

    def test_compute_checksum_small_file(self, tmp_path):
        """Should compute SHA-256 checksum for small file."""
        from foothold_checkpoint.core.checkpoint import compute_file_checksum

        # Create a small test file
        test_file = tmp_path / "test.txt"
        test_file.write_text("Hello, World!", encoding="utf-8")

        checksum = compute_file_checksum(test_file)

        # Known SHA-256 of "Hello, World!"
        expected = "sha256:dffd6021bb2bd5b0af676290809ec3a53191dd81c7f70a4b28688a362182986f"
        assert checksum == expected

    def test_compute_checksum_large_file(self, tmp_path):
        """Should compute SHA-256 checksum for large file (using chunks)."""
        from foothold_checkpoint.core.checkpoint import compute_file_checksum

        # Create a large test file (1 MB)
        test_file = tmp_path / "large.bin"
        test_file.write_bytes(b"x" * (1024 * 1024))  # 1 MB of 'x'

        checksum = compute_file_checksum(test_file)

        # Should return a valid sha256 checksum
        assert checksum.startswith("sha256:")
        assert len(checksum) == 71  # "sha256:" (7) + 64 hex chars

    def test_compute_checksum_same_content_same_hash(self, tmp_path):
        """Should produce same checksum for files with identical content."""
        from foothold_checkpoint.core.checkpoint import compute_file_checksum

        # Create two files with identical content
        file1 = tmp_path / "file1.txt"
        file2 = tmp_path / "file2.txt"
        content = "Identical content for testing"
        file1.write_text(content, encoding="utf-8")
        file2.write_text(content, encoding="utf-8")

        checksum1 = compute_file_checksum(file1)
        checksum2 = compute_file_checksum(file2)

        assert checksum1 == checksum2

    def test_compute_checksum_different_content_different_hash(self, tmp_path):
        """Should produce different checksums for different content."""
        from foothold_checkpoint.core.checkpoint import compute_file_checksum

        file1 = tmp_path / "file1.txt"
        file2 = tmp_path / "file2.txt"
        file1.write_text("Content A", encoding="utf-8")
        file2.write_text("Content B", encoding="utf-8")

        checksum1 = compute_file_checksum(file1)
        checksum2 = compute_file_checksum(file2)

        assert checksum1 != checksum2

    def test_compute_checksum_empty_file(self, tmp_path):
        """Should compute checksum for empty file."""
        from foothold_checkpoint.core.checkpoint import compute_file_checksum

        test_file = tmp_path / "empty.txt"
        test_file.write_bytes(b"")

        checksum = compute_file_checksum(test_file)

        # Known SHA-256 of empty string
        expected = "sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
        assert checksum == expected

    def test_compute_checksum_file_not_found(self, tmp_path):
        """Should raise FileNotFoundError for non-existent file."""
        from foothold_checkpoint.core.checkpoint import compute_file_checksum

        non_existent = tmp_path / "does_not_exist.txt"

        with pytest.raises(FileNotFoundError):
            compute_file_checksum(non_existent)

    def test_compute_checksum_directory_raises_error(self, tmp_path):
        """Should raise error when path is a directory."""
        from foothold_checkpoint.core.checkpoint import compute_file_checksum

        # tmp_path itself is a directory
        with pytest.raises(ValueError) as exc_info:
            compute_file_checksum(tmp_path)

        assert "not a file" in str(exc_info.value).lower()

    def test_compute_checksum_accepts_string_path(self, tmp_path):
        """Should accept path as string."""
        from foothold_checkpoint.core.checkpoint import compute_file_checksum

        test_file = tmp_path / "test.txt"
        test_file.write_text("Test content", encoding="utf-8")

        # Pass as string instead of Path
        checksum = compute_file_checksum(str(test_file))

        assert checksum.startswith("sha256:")
        assert len(checksum) == 71

    def test_compute_checksum_binary_file(self, tmp_path):
        """Should compute checksum for binary files."""
        from foothold_checkpoint.core.checkpoint import compute_file_checksum

        test_file = tmp_path / "binary.bin"
        test_file.write_bytes(bytes([0, 1, 2, 3, 255, 254, 253]))

        checksum = compute_file_checksum(test_file)

        assert checksum.startswith("sha256:")
        assert len(checksum) == 71

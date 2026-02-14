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


class TestMetadataSerialization:
    """Test suite for metadata JSON serialization."""

    def test_serialize_metadata_all_fields(self, tmp_path):
        """Should serialize metadata with all fields to JSON file."""
        from foothold_checkpoint.core.checkpoint import CheckpointMetadata, save_metadata

        metadata = CheckpointMetadata(
            campaign_name="afghanistan",
            server_name="production-1",
            created_at=datetime(2024, 1, 15, 10, 30, 0, tzinfo=timezone.utc),
            files={
                "foothold_afghanistan.lua": "sha256:abc123...",
                "foothold_afghanistan_storage.csv": "sha256:def456..."
            },
            name="Before major update",
            comment="Checkpoint created before implementing new features"
        )

        json_file = tmp_path / "metadata.json"
        save_metadata(metadata, json_file)

        # Verify file was created
        assert json_file.exists()

        # Verify JSON content
        import json
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        assert data["campaign_name"] == "afghanistan"
        assert data["server_name"] == "production-1"
        assert data["created_at"] == "2024-01-15T10:30:00Z"
        assert data["files"] == {
            "foothold_afghanistan.lua": "sha256:abc123...",
            "foothold_afghanistan_storage.csv": "sha256:def456..."
        }
        assert data["name"] == "Before major update"
        assert data["comment"] == "Checkpoint created before implementing new features"

    def test_serialize_metadata_optional_fields_none(self, tmp_path):
        """Should serialize metadata with optional fields as null."""
        from foothold_checkpoint.core.checkpoint import CheckpointMetadata, save_metadata

        metadata = CheckpointMetadata(
            campaign_name="afghanistan",
            server_name="production-1",
            created_at=datetime(2024, 1, 15, 10, 30, 0, tzinfo=timezone.utc),
            files={"foothold_afghanistan.lua": "sha256:abc123..."}
        )

        json_file = tmp_path / "metadata.json"
        save_metadata(metadata, json_file)

        import json
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        assert data["name"] is None
        assert data["comment"] is None

    def test_deserialize_metadata_all_fields(self, tmp_path):
        """Should deserialize JSON file to CheckpointMetadata."""
        from foothold_checkpoint.core.checkpoint import load_metadata

        json_file = tmp_path / "metadata.json"
        json_content = {
            "campaign_name": "afghanistan",
            "server_name": "production-1",
            "created_at": "2024-01-15T10:30:00Z",
            "files": {
                "foothold_afghanistan.lua": "sha256:abc123...",
                "foothold_afghanistan_storage.csv": "sha256:def456..."
            },
            "name": "Before major update",
            "comment": "Test checkpoint"
        }

        import json
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(json_content, f)

        metadata = load_metadata(json_file)

        assert metadata.campaign_name == "afghanistan"
        assert metadata.server_name == "production-1"
        assert metadata.created_at == datetime(2024, 1, 15, 10, 30, 0, tzinfo=timezone.utc)
        assert metadata.files == {
            "foothold_afghanistan.lua": "sha256:abc123...",
            "foothold_afghanistan_storage.csv": "sha256:def456..."
        }
        assert metadata.name == "Before major update"
        assert metadata.comment == "Test checkpoint"

    def test_deserialize_metadata_optional_fields_null(self, tmp_path):
        """Should deserialize JSON with null optional fields."""
        from foothold_checkpoint.core.checkpoint import load_metadata

        json_file = tmp_path / "metadata.json"
        json_content = {
            "campaign_name": "afghanistan",
            "server_name": "production-1",
            "created_at": "2024-01-15T10:30:00Z",
            "files": {"foothold_afghanistan.lua": "sha256:abc123..."},
            "name": None,
            "comment": None
        }

        import json
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(json_content, f)

        metadata = load_metadata(json_file)

        assert metadata.name is None
        assert metadata.comment is None

    def test_roundtrip_serialization(self, tmp_path):
        """Should preserve data through serialize → deserialize cycle."""
        from foothold_checkpoint.core.checkpoint import (
            CheckpointMetadata, save_metadata, load_metadata
        )

        original = CheckpointMetadata(
            campaign_name="afghanistan",
            server_name="production-1",
            created_at=datetime(2024, 1, 15, 10, 30, 0, tzinfo=timezone.utc),
            files={
                "foothold_afghanistan.lua": "sha256:abc123...",
                "foothold_afghanistan_storage.csv": "sha256:def456..."
            },
            name="Test checkpoint",
            comment="Roundtrip test"
        )

        json_file = tmp_path / "metadata.json"
        save_metadata(original, json_file)
        loaded = load_metadata(json_file)

        assert loaded.campaign_name == original.campaign_name
        assert loaded.server_name == original.server_name
        assert loaded.created_at == original.created_at
        assert loaded.files == original.files
        assert loaded.name == original.name
        assert loaded.comment == original.comment

    def test_deserialize_invalid_json_raises_error(self, tmp_path):
        """Should raise error for invalid JSON."""
        from foothold_checkpoint.core.checkpoint import load_metadata

        json_file = tmp_path / "invalid.json"
        json_file.write_text("{ invalid json content", encoding="utf-8")

        with pytest.raises(ValueError) as exc_info:
            load_metadata(json_file)

        assert "invalid json" in str(exc_info.value).lower() or "json" in str(exc_info.value).lower()

    def test_deserialize_missing_required_field_raises_error(self, tmp_path):
        """Should raise error when required fields are missing."""
        from foothold_checkpoint.core.checkpoint import load_metadata

        json_file = tmp_path / "incomplete.json"
        json_content = {
            "campaign_name": "afghanistan",
            # Missing server_name, created_at, files
        }

        import json
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(json_content, f)

        with pytest.raises(ValidationError):
            load_metadata(json_file)

    def test_deserialize_file_not_found(self, tmp_path):
        """Should raise FileNotFoundError for non-existent file."""
        from foothold_checkpoint.core.checkpoint import load_metadata

        json_file = tmp_path / "does_not_exist.json"

        with pytest.raises(FileNotFoundError):
            load_metadata(json_file)

    def test_serialize_datetime_iso_format(self, tmp_path):
        """Should serialize datetime in ISO 8601 format with timezone."""
        from foothold_checkpoint.core.checkpoint import CheckpointMetadata, save_metadata

        metadata = CheckpointMetadata(
            campaign_name="afghanistan",
            server_name="production-1",
            created_at=datetime(2024, 1, 15, 10, 30, 45, tzinfo=timezone.utc),
            files={"foothold_afghanistan.lua": "sha256:abc123..."}
        )

        json_file = tmp_path / "metadata.json"
        save_metadata(metadata, json_file)

        import json
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # Should be in ISO 8601 format
        assert data["created_at"] == "2024-01-15T10:30:45Z"

    def test_serialize_accepts_string_path(self, tmp_path):
        """Should accept path as string for save_metadata."""
        from foothold_checkpoint.core.checkpoint import CheckpointMetadata, save_metadata

        metadata = CheckpointMetadata(
            campaign_name="afghanistan",
            server_name="production-1",
            created_at=datetime(2024, 1, 15, 10, 30, 0, tzinfo=timezone.utc),
            files={"foothold_afghanistan.lua": "sha256:abc123..."}
        )

        json_file = str(tmp_path / "metadata.json")
        save_metadata(metadata, json_file)

        assert Path(json_file).exists()


class TestFilenameGeneration:
    """Test suite for checkpoint filename generation."""

    def test_generate_filename_with_datetime(self):
        """Should generate filename in format campaign_YYYY-MM-DD_HH-MM-SS.zip."""
        from foothold_checkpoint.core.checkpoint import generate_checkpoint_filename

        campaign_name = "afghanistan"
        timestamp = datetime(2024, 1, 15, 10, 30, 45, tzinfo=timezone.utc)

        filename = generate_checkpoint_filename(campaign_name, timestamp)

        assert filename == "afghanistan_2024-01-15_10-30-45.zip"

    def test_generate_filename_format_components(self):
        """Should include all datetime components in correct format."""
        from foothold_checkpoint.core.checkpoint import generate_checkpoint_filename

        timestamp = datetime(2024, 3, 7, 8, 5, 3, tzinfo=timezone.utc)
        filename = generate_checkpoint_filename("syria", timestamp)

        # Should zero-pad single digits
        assert filename == "syria_2024-03-07_08-05-03.zip"

    def test_generate_filename_different_timestamps(self):
        """Should generate different filenames for different timestamps."""
        from foothold_checkpoint.core.checkpoint import generate_checkpoint_filename

        campaign = "afghanistan"
        time1 = datetime(2024, 1, 15, 10, 30, 0, tzinfo=timezone.utc)
        time2 = datetime(2024, 1, 15, 10, 30, 1, tzinfo=timezone.utc)

        filename1 = generate_checkpoint_filename(campaign, time1)
        filename2 = generate_checkpoint_filename(campaign, time2)

        assert filename1 != filename2
        assert filename1 == "afghanistan_2024-01-15_10-30-00.zip"
        assert filename2 == "afghanistan_2024-01-15_10-30-01.zip"

    def test_generate_filename_same_timestamp(self):
        """Should generate same filename for same timestamp."""
        from foothold_checkpoint.core.checkpoint import generate_checkpoint_filename

        campaign = "afghanistan"
        timestamp = datetime(2024, 1, 15, 10, 30, 45, tzinfo=timezone.utc)

        filename1 = generate_checkpoint_filename(campaign, timestamp)
        filename2 = generate_checkpoint_filename(campaign, timestamp)

        assert filename1 == filename2

    def test_generate_filename_with_underscores_in_campaign(self):
        """Should handle campaign names with underscores."""
        from foothold_checkpoint.core.checkpoint import generate_checkpoint_filename

        campaign = "germany_modern"
        timestamp = datetime(2024, 1, 15, 10, 30, 45, tzinfo=timezone.utc)

        filename = generate_checkpoint_filename(campaign, timestamp)

        assert filename == "germany_modern_2024-01-15_10-30-45.zip"

    def test_generate_filename_without_datetime_uses_now(self):
        """Should use current time if datetime not provided."""
        from foothold_checkpoint.core.checkpoint import generate_checkpoint_filename
        from datetime import datetime

        campaign = "afghanistan"

        # Generate filename without providing datetime
        before = datetime.now(timezone.utc)
        filename = generate_checkpoint_filename(campaign)
        after = datetime.now(timezone.utc)

        # Filename should start with campaign name and end with .zip
        assert filename.startswith("afghanistan_")
        assert filename.endswith(".zip")

        # Extract timestamp from filename
        # Format: afghanistan_2024-01-15_10-30-45.zip
        timestamp_part = filename[len("afghanistan_"):-len(".zip")]
        year, month, day, hour, minute, second = (
            timestamp_part[:4], timestamp_part[5:7], timestamp_part[8:10],
            timestamp_part[11:13], timestamp_part[14:16], timestamp_part[17:19]
        )

        file_time = datetime(
            int(year), int(month), int(day),
            int(hour), int(minute), int(second),
            tzinfo=timezone.utc
        )

        # File timestamp should be within the time window (compare without microseconds)
        # Remove microseconds from before/after for fair comparison since filename has second precision
        before_no_micro = before.replace(microsecond=0)
        after_no_micro = after.replace(microsecond=0)
        assert before_no_micro <= file_time <= after_no_micro

    def test_generate_filename_extension_is_zip(self):
        """Should always end with .zip extension."""
        from foothold_checkpoint.core.checkpoint import generate_checkpoint_filename

        timestamp = datetime(2024, 1, 15, 10, 30, 45, tzinfo=timezone.utc)
        filename = generate_checkpoint_filename("afghanistan", timestamp)

        assert filename.endswith(".zip")

    def test_generate_filename_no_spaces_in_output(self):
        """Should not contain spaces in filename."""
        from foothold_checkpoint.core.checkpoint import generate_checkpoint_filename

        timestamp = datetime(2024, 1, 15, 10, 30, 45, tzinfo=timezone.utc)
        filename = generate_checkpoint_filename("afghanistan", timestamp)

        assert " " not in filename

"""Tests for checkpoint storage operations."""

import tempfile
from datetime import datetime, timezone
from pathlib import Path

import pytest


class TestSaveCheckpoint:
    """Test suite for save_checkpoint function."""

    def test_save_checkpoint_creates_zip_in_output_dir(self):
        """save_checkpoint should create a ZIP file in the specified output directory."""
        from foothold_checkpoint.core.storage import save_checkpoint

        with tempfile.TemporaryDirectory() as tmpdir:
            source_dir = Path(tmpdir) / "source"
            source_dir.mkdir()
            output_dir = Path(tmpdir) / "checkpoints"
            output_dir.mkdir()

            # Create test campaign files
            (source_dir / "foothold_test.lua").write_text("-- test campaign")
            (source_dir / "foothold_test_storage.csv").write_text("test,data")

            result = save_checkpoint(
                campaign_name="test",
                server_name="test-server",
                source_dir=source_dir,
                output_dir=output_dir,
            )

            assert result.exists()
            assert result.parent == output_dir
            assert result.suffix == ".zip"
            assert result.name.startswith("test_")

    def test_save_checkpoint_returns_path_to_created_checkpoint(self):
        """save_checkpoint should return the Path to the created checkpoint ZIP."""
        from foothold_checkpoint.core.storage import save_checkpoint

        with tempfile.TemporaryDirectory() as tmpdir:
            source_dir = Path(tmpdir) / "source"
            source_dir.mkdir()
            output_dir = Path(tmpdir) / "checkpoints"
            output_dir.mkdir()

            (source_dir / "foothold_test.lua").write_text("-- test")

            result = save_checkpoint(
                campaign_name="test",
                server_name="server",
                source_dir=source_dir,
                output_dir=output_dir,
            )

            assert isinstance(result, Path)
            assert result.is_file()

    def test_save_checkpoint_with_custom_name_and_comment(self):
        """save_checkpoint should accept optional name and comment parameters."""
        import json
        import zipfile

        from foothold_checkpoint.core.storage import save_checkpoint

        with tempfile.TemporaryDirectory() as tmpdir:
            source_dir = Path(tmpdir) / "source"
            source_dir.mkdir()
            output_dir = Path(tmpdir) / "checkpoints"
            output_dir.mkdir()

            (source_dir / "foothold_test.lua").write_text("-- test")

            result = save_checkpoint(
                campaign_name="test",
                server_name="server",
                source_dir=source_dir,
                output_dir=output_dir,
                name="Before Mission 5",
                comment="Test checkpoint",
            )

            # Verify metadata contains name and comment
            with zipfile.ZipFile(result, "r") as zf, zf.open("metadata.json") as mf:
                metadata_dict = json.load(mf)
                assert metadata_dict["name"] == "Before Mission 5"
                assert metadata_dict["comment"] == "Test checkpoint"

    def test_save_checkpoint_finds_campaign_files_automatically(self):
        """save_checkpoint should find all campaign files matching the campaign name."""
        import zipfile

        from foothold_checkpoint.core.storage import save_checkpoint

        with tempfile.TemporaryDirectory() as tmpdir:
            source_dir = Path(tmpdir) / "source"
            source_dir.mkdir()
            output_dir = Path(tmpdir) / "checkpoints"
            output_dir.mkdir()

            # Create campaign files
            (source_dir / "foothold_afghanistan.lua").write_text("-- campaign")
            (source_dir / "foothold_afghanistan_storage.csv").write_text("data")
            (source_dir / "foothold_afghanistan_CTLD_FARPS.csv").write_text("ctld")
            (source_dir / "foothold_syria.lua").write_text("-- other")

            result = save_checkpoint(
                campaign_name="afghanistan",
                server_name="server",
                source_dir=source_dir,
                output_dir=output_dir,
            )

            # Verify only afghanistan files are in checkpoint
            with zipfile.ZipFile(result, "r") as zf:
                names = zf.namelist()
                assert "foothold_afghanistan.lua" in names
                assert "foothold_afghanistan_storage.csv" in names
                assert "foothold_afghanistan_CTLD_FARPS.csv" in names
                assert "foothold_syria.lua" not in names

    def test_save_checkpoint_includes_foothold_ranks_when_present(self):
        """save_checkpoint should include Foothold_Ranks.lua if it exists."""
        import zipfile

        from foothold_checkpoint.core.storage import save_checkpoint

        with tempfile.TemporaryDirectory() as tmpdir:
            source_dir = Path(tmpdir) / "source"
            source_dir.mkdir()
            output_dir = Path(tmpdir) / "checkpoints"
            output_dir.mkdir()

            (source_dir / "foothold_test.lua").write_text("-- test")
            (source_dir / "Foothold_Ranks.lua").write_text("-- ranks")

            result = save_checkpoint(
                campaign_name="test",
                server_name="server",
                source_dir=source_dir,
                output_dir=output_dir,
            )

            with zipfile.ZipFile(result, "r") as zf:
                assert "Foothold_Ranks.lua" in zf.namelist()

    def test_save_checkpoint_without_foothold_ranks(self):
        """save_checkpoint should work when Foothold_Ranks.lua is absent."""
        import zipfile

        from foothold_checkpoint.core.storage import save_checkpoint

        with tempfile.TemporaryDirectory() as tmpdir:
            source_dir = Path(tmpdir) / "source"
            source_dir.mkdir()
            output_dir = Path(tmpdir) / "checkpoints"
            output_dir.mkdir()

            (source_dir / "foothold_test.lua").write_text("-- test")

            result = save_checkpoint(
                campaign_name="test",
                server_name="server",
                source_dir=source_dir,
                output_dir=output_dir,
            )

            with zipfile.ZipFile(result, "r") as zf:
                assert "Foothold_Ranks.lua" not in zf.namelist()

    def test_save_checkpoint_with_custom_timestamp(self):
        """save_checkpoint should accept optional created_at timestamp."""
        from foothold_checkpoint.core.storage import save_checkpoint

        with tempfile.TemporaryDirectory() as tmpdir:
            source_dir = Path(tmpdir) / "source"
            source_dir.mkdir()
            output_dir = Path(tmpdir) / "checkpoints"
            output_dir.mkdir()

            (source_dir / "foothold_test.lua").write_text("-- test")

            custom_time = datetime(2024, 1, 15, 10, 30, 0, tzinfo=timezone.utc)
            result = save_checkpoint(
                campaign_name="test",
                server_name="server",
                source_dir=source_dir,
                output_dir=output_dir,
                created_at=custom_time,
            )

            assert "2024-01-15_10-30-00" in result.name

    def test_save_checkpoint_with_progress_callback(self):
        """save_checkpoint should call progress callback during operation."""
        from foothold_checkpoint.core.storage import save_checkpoint

        with tempfile.TemporaryDirectory() as tmpdir:
            source_dir = Path(tmpdir) / "source"
            source_dir.mkdir()
            output_dir = Path(tmpdir) / "checkpoints"
            output_dir.mkdir()

            (source_dir / "foothold_test.lua").write_text("-- test")

            progress_calls = []

            def progress_callback(message: str, current: int, total: int) -> None:
                progress_calls.append((message, current, total))

            save_checkpoint(
                campaign_name="test",
                server_name="server",
                source_dir=source_dir,
                output_dir=output_dir,
                progress_callback=progress_callback,
            )

            assert len(progress_calls) > 0
            # Should have been called during checkpoint creation
            assert any(isinstance(call[0], str) for call in progress_calls)

    def test_save_checkpoint_raises_error_when_no_campaign_files_found(self):
        """save_checkpoint should raise ValueError when no campaign files are found."""
        from foothold_checkpoint.core.storage import save_checkpoint

        with tempfile.TemporaryDirectory() as tmpdir:
            source_dir = Path(tmpdir) / "source"
            source_dir.mkdir()
            output_dir = Path(tmpdir) / "checkpoints"
            output_dir.mkdir()

            # Create only unrelated files
            (source_dir / "other_file.txt").write_text("not a campaign")

            with pytest.raises(
                ValueError,
                match="No campaign files found for campaign 'nonexistent'",
            ):
                save_checkpoint(
                    campaign_name="nonexistent",
                    server_name="server",
                    source_dir=source_dir,
                    output_dir=output_dir,
                )

    def test_save_checkpoint_raises_error_when_source_dir_does_not_exist(self):
        """save_checkpoint should raise FileNotFoundError if source_dir doesn't exist."""
        from foothold_checkpoint.core.storage import save_checkpoint

        with tempfile.TemporaryDirectory() as tmpdir:
            source_dir = Path(tmpdir) / "nonexistent"  # Does not exist
            output_dir = Path(tmpdir) / "checkpoints"
            output_dir.mkdir()

            with pytest.raises(
                FileNotFoundError,
                match="Source directory.*does not exist",
            ):
                save_checkpoint(
                    campaign_name="test",
                    server_name="server",
                    source_dir=source_dir,
                    output_dir=output_dir,
                )

    def test_save_checkpoint_raises_error_when_source_dir_is_not_directory(self):
        """save_checkpoint should raise NotADirectoryError if source_dir is a file."""
        from foothold_checkpoint.core.storage import save_checkpoint

        with tempfile.TemporaryDirectory() as tmpdir:
            source_file = Path(tmpdir) / "source.txt"
            source_file.write_text("not a directory")
            output_dir = Path(tmpdir) / "checkpoints"
            output_dir.mkdir()

            with pytest.raises(
                NotADirectoryError,
                match="Source path.*is not a directory",
            ):
                save_checkpoint(
                    campaign_name="test",
                    server_name="server",
                    source_dir=source_file,
                    output_dir=output_dir,
                )

    def test_save_checkpoint_raises_error_when_source_dir_not_readable(self):
        """save_checkpoint should raise PermissionError if source_dir is not readable."""
        import os
        import stat

        from foothold_checkpoint.core.storage import save_checkpoint

        # Skip this test on Windows as chmod doesn't work reliably
        if os.name == "nt":
            pytest.skip("Permission tests not reliable on Windows")

        with tempfile.TemporaryDirectory() as tmpdir:
            source_dir = Path(tmpdir) / "source"
            source_dir.mkdir()
            output_dir = Path(tmpdir) / "checkpoints"
            output_dir.mkdir()

            # Create campaign file
            (source_dir / "foothold_test.lua").write_text("-- test")

            # Remove read permissions
            os.chmod(source_dir, 0o000)

            try:
                with pytest.raises(PermissionError):
                    save_checkpoint(
                        campaign_name="test",
                        server_name="server",
                        source_dir=source_dir,
                        output_dir=output_dir,
                    )
            finally:
                # Restore permissions for cleanup
                os.chmod(source_dir, stat.S_IRWXU)


class TestSaveAllCampaigns:
    """Test suite for save_all_campaigns function."""

    def test_save_all_campaigns_creates_multiple_checkpoints(self):
        """save_all_campaigns should create one checkpoint per detected campaign."""
        from foothold_checkpoint.core.storage import save_all_campaigns

        with tempfile.TemporaryDirectory() as tmpdir:
            source_dir = Path(tmpdir) / "source"
            source_dir.mkdir()
            output_dir = Path(tmpdir) / "checkpoints"
            output_dir.mkdir()

            # Create files for multiple campaigns
            (source_dir / "foothold_afghanistan.lua").write_text("-- afghanistan")
            (source_dir / "foothold_syria.lua").write_text("-- syria")
            (source_dir / "foothold_caucasus.lua").write_text("-- caucasus")

            results = save_all_campaigns(
                server_name="server",
                source_dir=source_dir,
                output_dir=output_dir,
            )

            assert len(results) == 3
            assert all(path.exists() for path in results.values())
            assert "afghanistan" in results
            assert "syria" in results
            assert "caucasus" in results

    def test_save_all_campaigns_returns_dict_mapping_campaigns_to_paths(self):
        """save_all_campaigns should return dict of campaign names to checkpoint paths."""
        from foothold_checkpoint.core.storage import save_all_campaigns

        with tempfile.TemporaryDirectory() as tmpdir:
            source_dir = Path(tmpdir) / "source"
            source_dir.mkdir()
            output_dir = Path(tmpdir) / "checkpoints"
            output_dir.mkdir()

            (source_dir / "foothold_test1.lua").write_text("-- test1")
            (source_dir / "foothold_test2.lua").write_text("-- test2")

            results = save_all_campaigns(
                server_name="server",
                source_dir=source_dir,
                output_dir=output_dir,
            )

            assert isinstance(results, dict)
            for campaign, path in results.items():
                assert isinstance(campaign, str)
                assert isinstance(path, Path)
                assert path.name.startswith(campaign + "_")

    def test_save_all_campaigns_with_shared_name_and_comment(self):
        """save_all_campaigns should apply same name/comment to all checkpoints."""
        import json
        import zipfile

        from foothold_checkpoint.core.storage import save_all_campaigns

        with tempfile.TemporaryDirectory() as tmpdir:
            source_dir = Path(tmpdir) / "source"
            source_dir.mkdir()
            output_dir = Path(tmpdir) / "checkpoints"
            output_dir.mkdir()

            (source_dir / "foothold_test1.lua").write_text("-- test1")
            (source_dir / "foothold_test2.lua").write_text("-- test2")

            results = save_all_campaigns(
                server_name="server",
                source_dir=source_dir,
                output_dir=output_dir,
                name="Shared name",
                comment="Shared comment",
            )

            # Verify all checkpoints have same name/comment
            for checkpoint_path in results.values():
                with zipfile.ZipFile(checkpoint_path, "r") as zf, zf.open(
                    "metadata.json"
                ) as mf:
                    metadata = json.load(mf)
                    assert metadata["name"] == "Shared name"
                    assert metadata["comment"] == "Shared comment"

    def test_save_all_campaigns_continues_on_partial_failure(self):
        """save_all_campaigns should continue saving other campaigns if one fails."""
        from foothold_checkpoint.core.storage import save_all_campaigns

        with tempfile.TemporaryDirectory() as tmpdir:
            source_dir = Path(tmpdir) / "source"
            source_dir.mkdir()
            output_dir = Path(tmpdir) / "checkpoints"
            output_dir.mkdir()

            # Create valid campaign
            (source_dir / "foothold_valid.lua").write_text("-- valid")
            # Create directory with campaign name (will cause error)
            invalid_campaign_dir = source_dir / "foothold_invalid.lua"
            invalid_campaign_dir.mkdir()  # Directory, not a file

            # Should succeed for valid campaign despite invalid one
            results = save_all_campaigns(
                server_name="server",
                source_dir=source_dir,
                output_dir=output_dir,
                continue_on_error=True,
            )

            # Should have saved the valid campaign
            assert "valid" in results
            assert results["valid"].exists()
            # Invalid campaign should not be in results
            assert "invalid" not in results

    def test_save_all_campaigns_raises_error_when_continue_on_error_false(self):
        """save_all_campaigns should raise error immediately if continue_on_error=False."""
        from foothold_checkpoint.core.storage import save_all_campaigns

        with tempfile.TemporaryDirectory() as tmpdir:
            source_dir = Path(tmpdir) / "source"
            source_dir.mkdir()
            # Use a file as output_dir (not a directory) to trigger error
            output_path = Path(tmpdir) / "not_a_directory.txt"
            output_path.write_text("this is a file, not a directory")

            # Create valid campaign file
            (source_dir / "foothold_test.lua").write_text("-- test")

            # Should raise error when trying to create checkpoint in a file path
            with pytest.raises((NotADirectoryError, OSError, FileNotFoundError)):
                save_all_campaigns(
                    server_name="server",
                    source_dir=source_dir,
                    output_dir=output_path,  # This is a file, not a directory
                    continue_on_error=False,
                )

    def test_save_all_campaigns_with_no_campaigns_returns_empty_dict(self):
        """save_all_campaigns should return empty dict when no campaigns found."""
        from foothold_checkpoint.core.storage import save_all_campaigns

        with tempfile.TemporaryDirectory() as tmpdir:
            source_dir = Path(tmpdir) / "source"
            source_dir.mkdir()
            output_dir = Path(tmpdir) / "checkpoints"
            output_dir.mkdir()

            # No campaign files
            (source_dir / "other_file.txt").write_text("not a campaign")

            results = save_all_campaigns(
                server_name="server",
                source_dir=source_dir,
                output_dir=output_dir,
            )

            assert results == {}

    def test_save_all_campaigns_with_custom_timestamp(self):
        """save_all_campaigns should apply same timestamp to all checkpoints."""
        from foothold_checkpoint.core.storage import save_all_campaigns

        with tempfile.TemporaryDirectory() as tmpdir:
            source_dir = Path(tmpdir) / "source"
            source_dir.mkdir()
            output_dir = Path(tmpdir) / "checkpoints"
            output_dir.mkdir()

            (source_dir / "foothold_test1.lua").write_text("-- test1")
            (source_dir / "foothold_test2.lua").write_text("-- test2")

            custom_time = datetime(2024, 1, 15, 10, 30, 0, tzinfo=timezone.utc)
            results = save_all_campaigns(
                server_name="server",
                source_dir=source_dir,
                output_dir=output_dir,
                created_at=custom_time,
            )

            # All checkpoints should have the same timestamp
            for path in results.values():
                assert "2024-01-15_10-30-00" in path.name


class TestStorageDirectoryCreation:
    """Test suite for automatic storage directory creation."""

    def test_save_checkpoint_creates_output_dir_if_not_exists(self):
        """save_checkpoint should create output_dir if it doesn't exist."""
        from foothold_checkpoint.core.storage import save_checkpoint

        with tempfile.TemporaryDirectory() as tmpdir:
            source_dir = Path(tmpdir) / "source"
            source_dir.mkdir()
            output_dir = Path(tmpdir) / "checkpoints" / "nested" / "deep"
            # Don't create output_dir - let save_checkpoint create it

            (source_dir / "foothold_test.lua").write_text("-- test")

            result = save_checkpoint(
                campaign_name="test",
                server_name="server",
                source_dir=source_dir,
                output_dir=output_dir,
            )

            assert output_dir.exists()
            assert output_dir.is_dir()
            assert result.parent == output_dir

    def test_save_checkpoint_works_when_output_dir_already_exists(self):
        """save_checkpoint should work normally when output_dir already exists."""
        from foothold_checkpoint.core.storage import save_checkpoint

        with tempfile.TemporaryDirectory() as tmpdir:
            source_dir = Path(tmpdir) / "source"
            source_dir.mkdir()
            output_dir = Path(tmpdir) / "checkpoints"
            output_dir.mkdir()  # Pre-create

            (source_dir / "foothold_test.lua").write_text("-- test")

            result = save_checkpoint(
                campaign_name="test",
                server_name="server",
                source_dir=source_dir,
                output_dir=output_dir,
            )

            assert result.exists()
            assert result.parent == output_dir

    def test_save_all_campaigns_creates_output_dir_if_not_exists(self):
        """save_all_campaigns should create output_dir if it doesn't exist."""
        from foothold_checkpoint.core.storage import save_all_campaigns

        with tempfile.TemporaryDirectory() as tmpdir:
            source_dir = Path(tmpdir) / "source"
            source_dir.mkdir()
            output_dir = Path(tmpdir) / "checkpoints" / "nested"
            # Don't create output_dir

            (source_dir / "foothold_test.lua").write_text("-- test")

            results = save_all_campaigns(
                server_name="server",
                source_dir=source_dir,
                output_dir=output_dir,
            )

            assert output_dir.exists()
            assert output_dir.is_dir()
            assert len(results) == 1

    def test_save_checkpoint_raises_error_if_output_dir_is_file(self):
        """save_checkpoint should raise error if output_dir is a file."""
        from foothold_checkpoint.core.storage import save_checkpoint

        with tempfile.TemporaryDirectory() as tmpdir:
            source_dir = Path(tmpdir) / "source"
            source_dir.mkdir()
            output_file = Path(tmpdir) / "output.txt"
            output_file.write_text("this is a file")

            (source_dir / "foothold_test.lua").write_text("-- test")

            with pytest.raises((NotADirectoryError, FileExistsError, OSError)):
                save_checkpoint(
                    campaign_name="test",
                    server_name="server",
                    source_dir=source_dir,
                    output_dir=output_file,
                )



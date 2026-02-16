"""Tests for checkpoint storage operations."""

import asyncio
import contextlib
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

import pytest


class TestSaveCheckpoint:
    """Test suite for save_checkpoint function."""

    def test_save_checkpoint_creates_zip_in_output_dir(self):
        """save_checkpoint should create a ZIP file in the specified output directory."""
        from foothold_checkpoint.core.storage import save_checkpoint
        from tests.conftest import make_simple_campaign, make_test_config

        with tempfile.TemporaryDirectory() as tmpdir:
            source_dir = Path(tmpdir) / "source"
            source_dir.mkdir()
            output_dir = Path(tmpdir) / "checkpoints"
            output_dir.mkdir()

            # Create test campaign files
            (source_dir / "foothold_test.lua").write_text("-- test campaign")
            (source_dir / "foothold_test_storage.csv").write_text("test,data")

            config = make_test_config(
                campaigns={
                    "test": make_simple_campaign(
                        "Test Campaign",
                        ["foothold_test.lua"],
                        storage=["foothold_test_storage.csv"],
                    )
                }
            )

            result = asyncio.run(
                save_checkpoint(
                    campaign_name="test",
                    server_name="test-server",
                    source_dir=source_dir,
                    output_dir=output_dir,
                    config=config,
                )
            )

            assert result.exists()
            assert result.parent == output_dir
            assert result.suffix == ".zip"
            assert result.name.startswith("test_")

    def test_save_checkpoint_returns_path_to_created_checkpoint(self):
        """save_checkpoint should return the Path to the created checkpoint ZIP."""
        from foothold_checkpoint.core.storage import save_checkpoint
        from tests.conftest import make_simple_campaign, make_test_config

        with tempfile.TemporaryDirectory() as tmpdir:
            source_dir = Path(tmpdir) / "source"
            source_dir.mkdir()
            output_dir = Path(tmpdir) / "checkpoints"
            output_dir.mkdir()

            (source_dir / "foothold_test.lua").write_text("-- test")

            config = make_test_config(
                campaigns={"test": make_simple_campaign("Test", ["foothold_test.lua"])}
            )

            result = asyncio.run(
                save_checkpoint(
                    campaign_name="test",
                    server_name="server",
                    source_dir=source_dir,
                    output_dir=output_dir,
                    config=config,
                )
            )

            assert isinstance(result, Path)
            assert result.is_file()

    def test_save_checkpoint_with_custom_name_and_comment(self):
        """save_checkpoint should accept optional name and comment parameters."""
        import json
        import zipfile

        from foothold_checkpoint.core.storage import save_checkpoint
        from tests.conftest import make_simple_campaign, make_test_config

        with tempfile.TemporaryDirectory() as tmpdir:
            source_dir = Path(tmpdir) / "source"
            source_dir.mkdir()
            output_dir = Path(tmpdir) / "checkpoints"
            output_dir.mkdir()

            (source_dir / "foothold_test.lua").write_text("-- test")

            config = make_test_config(
                campaigns={"test": make_simple_campaign("Test", ["foothold_test.lua"])}
            )

            result = asyncio.run(
                save_checkpoint(
                    campaign_name="test",
                    server_name="server",
                    source_dir=source_dir,
                    output_dir=output_dir,
                    config=config,
                    name="Before Mission 5",
                    comment="Test checkpoint",
                )
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
        from tests.conftest import make_simple_campaign, make_test_config

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

            config = make_test_config(
                campaigns={
                    "afghanistan": make_simple_campaign(
                        "Afghanistan",
                        ["foothold_afghanistan.lua"],
                        storage=["foothold_afghanistan_storage.csv"],
                        ctld_farps=["foothold_afghanistan_CTLD_FARPS.csv"],
                    ),
                    "syria": make_simple_campaign("Syria", ["foothold_syria.lua"]),
                }
            )

            result = asyncio.run(
                save_checkpoint(
                    campaign_name="afghanistan",
                    server_name="server",
                    source_dir=source_dir,
                    output_dir=output_dir,
                    config=config,
                )
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
        from tests.conftest import make_simple_campaign, make_test_config

        with tempfile.TemporaryDirectory() as tmpdir:
            source_dir = Path(tmpdir) / "source"
            source_dir.mkdir()
            output_dir = Path(tmpdir) / "checkpoints"
            output_dir.mkdir()

            (source_dir / "foothold_test.lua").write_text("-- test")
            (source_dir / "Foothold_Ranks.lua").write_text("-- ranks")

            config = make_test_config(
                campaigns={"test": make_simple_campaign("Test", ["foothold_test.lua"])}
            )

            result = asyncio.run(
                save_checkpoint(
                    campaign_name="test",
                    server_name="server",
                    source_dir=source_dir,
                    output_dir=output_dir,
                    config=config,
                )
            )

            with zipfile.ZipFile(result, "r") as zf:
                assert "Foothold_Ranks.lua" in zf.namelist()

    def test_save_checkpoint_without_foothold_ranks(self):
        """save_checkpoint should work when Foothold_Ranks.lua is absent."""
        import zipfile

        from foothold_checkpoint.core.storage import save_checkpoint
        from tests.conftest import make_simple_campaign, make_test_config

        with tempfile.TemporaryDirectory() as tmpdir:
            source_dir = Path(tmpdir) / "source"
            source_dir.mkdir()
            output_dir = Path(tmpdir) / "checkpoints"
            output_dir.mkdir()

            (source_dir / "foothold_test.lua").write_text("-- test")

            config = make_test_config(
                campaigns={"test": make_simple_campaign("Test", ["foothold_test.lua"])}
            )

            result = asyncio.run(
                save_checkpoint(
                    campaign_name="test",
                    server_name="server",
                    source_dir=source_dir,
                    output_dir=output_dir,
                    config=config,
                )
            )

            with zipfile.ZipFile(result, "r") as zf:
                assert "Foothold_Ranks.lua" not in zf.namelist()

    def test_save_checkpoint_with_custom_timestamp(self):
        """save_checkpoint should accept optional created_at timestamp."""
        from foothold_checkpoint.core.storage import save_checkpoint
        from tests.conftest import make_simple_campaign, make_test_config

        with tempfile.TemporaryDirectory() as tmpdir:
            source_dir = Path(tmpdir) / "source"
            source_dir.mkdir()
            output_dir = Path(tmpdir) / "checkpoints"
            output_dir.mkdir()

            (source_dir / "foothold_test.lua").write_text("-- test")

            config = make_test_config(
                campaigns={"test": make_simple_campaign("Test", ["foothold_test.lua"])}
            )

            custom_time = datetime(2024, 1, 15, 10, 30, 0, tzinfo=timezone.utc)
            result = asyncio.run(
                save_checkpoint(
                    campaign_name="test",
                    server_name="server",
                    source_dir=source_dir,
                    output_dir=output_dir,
                    config=config,
                    created_at=custom_time,
                )
            )

            assert "2024-01-15_10-30-00" in result.name

    def test_save_checkpoint_with_progress_callback(self):
        """save_checkpoint should call progress callback during operation."""
        from foothold_checkpoint.core.storage import save_checkpoint
        from tests.conftest import make_simple_campaign, make_test_config

        with tempfile.TemporaryDirectory() as tmpdir:
            source_dir = Path(tmpdir) / "source"
            source_dir.mkdir()
            output_dir = Path(tmpdir) / "checkpoints"
            output_dir.mkdir()

            (source_dir / "foothold_test.lua").write_text("-- test")

            config = make_test_config(
                campaigns={"test": make_simple_campaign("Test", ["foothold_test.lua"])}
            )

            progress_calls = []

            def progress_callback(message: str, current: int, total: int) -> None:
                progress_calls.append((message, current, total))

            asyncio.run(
                save_checkpoint(
                    campaign_name="test",
                    server_name="server",
                    source_dir=source_dir,
                    output_dir=output_dir,
                    config=config,
                    progress_callback=progress_callback,
                )
            )

            assert len(progress_calls) > 0
            # Should have been called during checkpoint creation
            assert any(isinstance(call[0], str) for call in progress_calls)

    def test_save_checkpoint_raises_error_when_no_campaign_files_found(self):
        """save_checkpoint should raise ValueError when no campaign files are found."""
        from foothold_checkpoint.core.storage import save_checkpoint
        from tests.conftest import make_simple_campaign, make_test_config

        with tempfile.TemporaryDirectory() as tmpdir:
            source_dir = Path(tmpdir) / "source"
            source_dir.mkdir()
            output_dir = Path(tmpdir) / "checkpoints"
            output_dir.mkdir()

            # Create only unrelated files
            (source_dir / "other_file.txt").write_text("not a campaign")

            config = make_test_config(
                campaigns={"nonexistent": make_simple_campaign("NE", ["foothold_nonexistent.lua"])}
            )

            with pytest.raises(
                ValueError,
                match="No campaign files found for campaign 'nonexistent'",
            ):
                asyncio.run(
                    save_checkpoint(
                        campaign_name="nonexistent",
                        server_name="server",
                        source_dir=source_dir,
                        output_dir=output_dir,
                        config=config,
                    )
                )

    def test_save_checkpoint_raises_error_when_source_dir_does_not_exist(self):
        """save_checkpoint should raise FileNotFoundError if source_dir doesn't exist."""
        from foothold_checkpoint.core.storage import save_checkpoint
        from tests.conftest import make_simple_campaign, make_test_config

        with tempfile.TemporaryDirectory() as tmpdir:
            source_dir = Path(tmpdir) / "nonexistent"  # Does not exist
            output_dir = Path(tmpdir) / "checkpoints"
            output_dir.mkdir()

            config = make_test_config(
                campaigns={"test": make_simple_campaign("Test", ["foothold_test.lua"])}
            )

            with pytest.raises(
                FileNotFoundError,
                match="Source directory.*does not exist",
            ):
                asyncio.run(
                    save_checkpoint(
                        campaign_name="test",
                        server_name="server",
                        source_dir=source_dir,
                        output_dir=output_dir,
                        config=config,
                    )
                )

    def test_save_checkpoint_raises_error_when_source_dir_is_not_directory(self):
        """save_checkpoint should raise NotADirectoryError if source_dir is a file."""
        from foothold_checkpoint.core.storage import save_checkpoint
        from tests.conftest import make_simple_campaign, make_test_config

        with tempfile.TemporaryDirectory() as tmpdir:
            source_file = Path(tmpdir) / "source.txt"
            source_file.write_text("not a directory")
            output_dir = Path(tmpdir) / "checkpoints"
            output_dir.mkdir()

            config = make_test_config(
                campaigns={"test": make_simple_campaign("Test", ["foothold_test.lua"])}
            )

            with pytest.raises(
                NotADirectoryError,
                match="Source path.*is not a directory",
            ):
                asyncio.run(
                    save_checkpoint(
                        campaign_name="test",
                        server_name="server",
                        source_dir=source_file,
                        output_dir=output_dir,
                        config=config,
                    )
                )

    def test_save_checkpoint_raises_error_when_source_dir_not_readable(self):
        """save_checkpoint should raise PermissionError if source_dir is not readable."""
        import os
        import stat

        from foothold_checkpoint.core.storage import save_checkpoint
        from tests.conftest import make_simple_campaign, make_test_config

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

            config = make_test_config(
                campaigns={"test": make_simple_campaign("Test", ["foothold_test.lua"])}
            )

            # Remove read permissions
            os.chmod(source_dir, 0o000)

            try:
                with pytest.raises(PermissionError):
                    asyncio.run(
                        save_checkpoint(
                            campaign_name="test",
                            server_name="server",
                            source_dir=source_dir,
                            output_dir=output_dir,
                            config=config,
                        )
                    )
            finally:
                # Restore permissions for cleanup
                os.chmod(source_dir, stat.S_IRWXU)


class TestSaveAllCampaigns:
    """Test suite for save_all_campaigns function."""

    def test_save_all_campaigns_creates_multiple_checkpoints(self):
        """save_all_campaigns should create one checkpoint per detected campaign."""
        from foothold_checkpoint.core.storage import save_all_campaigns
        from tests.conftest import make_simple_campaign, make_test_config

        with tempfile.TemporaryDirectory() as tmpdir:
            source_dir = Path(tmpdir) / "source"
            source_dir.mkdir()
            output_dir = Path(tmpdir) / "checkpoints"
            output_dir.mkdir()

            # Create files for multiple campaigns
            (source_dir / "foothold_afghanistan.lua").write_text("-- afghanistan")
            (source_dir / "foothold_syria.lua").write_text("-- syria")
            (source_dir / "foothold_caucasus.lua").write_text("-- caucasus")

            config = make_test_config(
                campaigns={
                    "afghanistan": make_simple_campaign(
                        "Afghanistan", ["foothold_afghanistan.lua"]
                    ),
                    "syria": make_simple_campaign("Syria", ["foothold_syria.lua"]),
                    "caucasus": make_simple_campaign("Caucasus", ["foothold_caucasus.lua"]),
                }
            )

            results = asyncio.run(
                save_all_campaigns(
                    server_name="server",
                    source_dir=source_dir,
                    output_dir=output_dir,
                    config=config,
                )
            )

            assert len(results) == 3
            assert all(path.exists() for path in results.values())
            assert "afghanistan" in results
            assert "syria" in results
            assert "caucasus" in results

    def test_save_all_campaigns_returns_dict_mapping_campaigns_to_paths(self):
        """save_all_campaigns should return dict of campaign names to checkpoint paths."""
        from foothold_checkpoint.core.storage import save_all_campaigns
        from tests.conftest import make_simple_campaign, make_test_config

        with tempfile.TemporaryDirectory() as tmpdir:
            source_dir = Path(tmpdir) / "source"
            source_dir.mkdir()
            output_dir = Path(tmpdir) / "checkpoints"
            output_dir.mkdir()

            (source_dir / "foothold_test1.lua").write_text("-- test1")
            (source_dir / "foothold_test2.lua").write_text("-- test2")

            config = make_test_config(
                campaigns={
                    "test1": make_simple_campaign("Test1", ["foothold_test1.lua"]),
                    "test2": make_simple_campaign("Test2", ["foothold_test2.lua"]),
                }
            )

            results = asyncio.run(
                save_all_campaigns(
                    server_name="server",
                    source_dir=source_dir,
                    output_dir=output_dir,
                    config=config,
                )
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
        from tests.conftest import make_simple_campaign, make_test_config

        with tempfile.TemporaryDirectory() as tmpdir:
            source_dir = Path(tmpdir) / "source"
            source_dir.mkdir()
            output_dir = Path(tmpdir) / "checkpoints"
            output_dir.mkdir()

            (source_dir / "foothold_test1.lua").write_text("-- test1")
            (source_dir / "foothold_test2.lua").write_text("-- test2")

            config = make_test_config(
                campaigns={
                    "test1": make_simple_campaign("Test1", ["foothold_test1.lua"]),
                    "test2": make_simple_campaign("Test2", ["foothold_test2.lua"]),
                }
            )

            results = asyncio.run(
                save_all_campaigns(
                    server_name="server",
                    source_dir=source_dir,
                    output_dir=output_dir,
                    config=config,
                    name="Shared name",
                    comment="Shared comment",
                )
            )

            # Verify all checkpoints have same name/comment
            for checkpoint_path in results.values():
                with zipfile.ZipFile(checkpoint_path, "r") as zf, zf.open("metadata.json") as mf:
                    metadata = json.load(mf)
                    assert metadata["name"] == "Shared name"
                    assert metadata["comment"] == "Shared comment"

    def test_save_all_campaigns_continues_on_partial_failure(self):
        """save_all_campaigns should continue saving other campaigns if one fails."""
        from foothold_checkpoint.core.storage import save_all_campaigns
        from tests.conftest import make_simple_campaign, make_test_config

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

            config = make_test_config(
                campaigns={
                    "valid": make_simple_campaign("Valid", ["foothold_valid.lua"]),
                    "invalid": make_simple_campaign("Invalid", ["foothold_invalid.lua"]),
                }
            )

            # Should succeed for valid campaign despite invalid one
            results = asyncio.run(
                save_all_campaigns(
                    server_name="server",
                    source_dir=source_dir,
                    output_dir=output_dir,
                    config=config,
                    continue_on_error=True,
                )
            )

            # Should have saved the valid campaign
            assert "valid" in results
            assert results["valid"].exists()
            # Invalid campaign should not be in results
            assert "invalid" not in results

    def test_save_all_campaigns_raises_error_when_continue_on_error_false(self):
        """save_all_campaigns should raise error immediately if continue_on_error=False."""
        from foothold_checkpoint.core.storage import save_all_campaigns
        from tests.conftest import make_simple_campaign, make_test_config

        with tempfile.TemporaryDirectory() as tmpdir:
            source_dir = Path(tmpdir) / "source"
            source_dir.mkdir()
            # Use a file as output_dir (not a directory) to trigger error
            output_path = Path(tmpdir) / "not_a_directory.txt"
            output_path.write_text("this is a file, not a directory")

            # Create valid campaign file
            (source_dir / "foothold_test.lua").write_text("-- test")

            config = make_test_config(
                campaigns={"test": make_simple_campaign("Test", ["foothold_test.lua"])}
            )

            # Should raise error when trying to create checkpoint in a file path
            with pytest.raises((NotADirectoryError, OSError, FileNotFoundError)):
                asyncio.run(
                    save_all_campaigns(
                        server_name="server",
                        source_dir=source_dir,
                        output_dir=output_path,  # This is a file, not a directory
                        config=config,
                        continue_on_error=False,
                    )
                )

    def test_save_all_campaigns_with_no_campaigns_returns_empty_dict(self):
        """save_all_campaigns should return empty dict when no campaigns found."""
        from foothold_checkpoint.core.storage import save_all_campaigns
        from tests.conftest import make_simple_campaign, make_test_config

        with tempfile.TemporaryDirectory() as tmpdir:
            source_dir = Path(tmpdir) / "source"
            source_dir.mkdir()
            output_dir = Path(tmpdir) / "checkpoints"
            output_dir.mkdir()

            # No campaign files matching
            (source_dir / "other_file.txt").write_text("not a campaign")

            # Config needs at least one campaign, but source_dir has no matching files
            config = make_test_config(
                campaigns={"test": make_simple_campaign("Test", ["foothold_test.lua"])}
            )

            results = asyncio.run(
                save_all_campaigns(
                    server_name="server",
                    source_dir=source_dir,
                    output_dir=output_dir,
                    config=config,
                )
            )

            assert results == {}

    def test_save_all_campaigns_with_custom_timestamp(self):
        """save_all_campaigns should apply same timestamp to all checkpoints."""
        from foothold_checkpoint.core.storage import save_all_campaigns
        from tests.conftest import make_simple_campaign, make_test_config

        with tempfile.TemporaryDirectory() as tmpdir:
            source_dir = Path(tmpdir) / "source"
            source_dir.mkdir()
            output_dir = Path(tmpdir) / "checkpoints"
            output_dir.mkdir()

            (source_dir / "foothold_test1.lua").write_text("-- test1")
            (source_dir / "foothold_test2.lua").write_text("-- test2")

            config = make_test_config(
                campaigns={
                    "test1": make_simple_campaign("Test1", ["foothold_test1.lua"]),
                    "test2": make_simple_campaign("Test2", ["foothold_test2.lua"]),
                }
            )

            custom_time = datetime(2024, 1, 15, 10, 30, 0, tzinfo=timezone.utc)
            results = asyncio.run(
                save_all_campaigns(
                    server_name="server",
                    source_dir=source_dir,
                    output_dir=output_dir,
                    config=config,
                    created_at=custom_time,
                )
            )

            # All checkpoints should have the same timestamp
            for path in results.values():
                assert "2024-01-15_10-30-00" in path.name


class TestStorageDirectoryCreation:
    """Test suite for automatic storage directory creation."""

    def test_save_checkpoint_creates_output_dir_if_not_exists(self):
        """save_checkpoint should create output_dir if it doesn't exist."""
        from foothold_checkpoint.core.storage import save_checkpoint
        from tests.conftest import make_simple_campaign, make_test_config

        with tempfile.TemporaryDirectory() as tmpdir:
            source_dir = Path(tmpdir) / "source"
            source_dir.mkdir()
            output_dir = Path(tmpdir) / "checkpoints" / "nested" / "deep"
            # Don't create output_dir - let save_checkpoint create it

            (source_dir / "foothold_test.lua").write_text("-- test")

            config = make_test_config(
                campaigns={"test": make_simple_campaign("Test", ["foothold_test.lua"])}
            )

            result = asyncio.run(
                save_checkpoint(
                    campaign_name="test",
                    server_name="server",
                    source_dir=source_dir,
                    output_dir=output_dir,
                    config=config,
                )
            )

            assert output_dir.exists()
            assert output_dir.is_dir()
            assert result.parent == output_dir

    def test_save_checkpoint_works_when_output_dir_already_exists(self):
        """save_checkpoint should work normally when output_dir already exists."""
        from foothold_checkpoint.core.storage import save_checkpoint
        from tests.conftest import make_simple_campaign, make_test_config

        with tempfile.TemporaryDirectory() as tmpdir:
            source_dir = Path(tmpdir) / "source"
            source_dir.mkdir()
            output_dir = Path(tmpdir) / "checkpoints"
            output_dir.mkdir()  # Pre-create

            (source_dir / "foothold_test.lua").write_text("-- test")

            config = make_test_config(
                campaigns={"test": make_simple_campaign("Test", ["foothold_test.lua"])}
            )

            result = asyncio.run(
                save_checkpoint(
                    campaign_name="test",
                    server_name="server",
                    source_dir=source_dir,
                    output_dir=output_dir,
                    config=config,
                )
            )

            assert result.exists()
            assert result.parent == output_dir

    def test_save_all_campaigns_creates_output_dir_if_not_exists(self):
        """save_all_campaigns should create output_dir if it doesn't exist."""
        from foothold_checkpoint.core.storage import save_all_campaigns
        from tests.conftest import make_simple_campaign, make_test_config

        with tempfile.TemporaryDirectory() as tmpdir:
            source_dir = Path(tmpdir) / "source"
            source_dir.mkdir()
            output_dir = Path(tmpdir) / "checkpoints" / "nested"
            # Don't create output_dir

            (source_dir / "foothold_test.lua").write_text("-- test")

            config = make_test_config(
                campaigns={"test": make_simple_campaign("Test", ["foothold_test.lua"])}
            )

            results = asyncio.run(
                save_all_campaigns(
                    server_name="server",
                    source_dir=source_dir,
                    output_dir=output_dir,
                    config=config,
                )
            )

            assert output_dir.exists()
            assert output_dir.is_dir()
            assert len(results) == 1

    def test_save_checkpoint_raises_error_if_output_dir_is_file(self):
        """save_checkpoint should raise error if output_dir is a file."""
        from foothold_checkpoint.core.storage import save_checkpoint
        from tests.conftest import make_simple_campaign, make_test_config

        with tempfile.TemporaryDirectory() as tmpdir:
            source_dir = Path(tmpdir) / "source"
            source_dir.mkdir()
            output_file = Path(tmpdir) / "output.txt"
            output_file.write_text("this is a file")

            (source_dir / "foothold_test.lua").write_text("-- test")

            config = make_test_config(
                campaigns={"test": make_simple_campaign("Test", ["foothold_test.lua"])}
            )

            with pytest.raises((NotADirectoryError, FileExistsError, OSError)):
                asyncio.run(
                    save_checkpoint(
                        campaign_name="test",
                        server_name="server",
                        source_dir=source_dir,
                        output_dir=output_file,
                        config=config,
                    )
                )


class TestRestoreCheckpoint:
    """Test suite for restore_checkpoint function."""

    def test_restore_checkpoint_extracts_files_to_target_dir(self):
        """restore_checkpoint should extract campaign files to the target directory."""
        from foothold_checkpoint.core.storage import restore_checkpoint, save_checkpoint
        from tests.conftest import make_simple_campaign, make_test_config

        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a checkpoint
            source_dir = Path(tmpdir) / "source"
            source_dir.mkdir()
            (source_dir / "foothold_test.lua").write_text("-- campaign code")
            (source_dir / "foothold_test_storage.csv").write_text("test,data")

            config = make_test_config(
                campaigns={
                    "test": make_simple_campaign(
                        "Test",
                        ["foothold_test.lua"],
                        storage=["foothold_test_storage.csv"],
                    )
                }
            )

            checkpoint_dir = Path(tmpdir) / "checkpoints"
            checkpoint_dir.mkdir()
            checkpoint_path = asyncio.run(
                save_checkpoint(
                    campaign_name="test",
                    server_name="test-server",
                    source_dir=source_dir,
                    output_dir=checkpoint_dir,
                    config=config,
                )
            )

            # Restore to a different directory
            target_dir = Path(tmpdir) / "target"
            target_dir.mkdir()

            asyncio.run(
                restore_checkpoint(
                    checkpoint_path=checkpoint_path, target_dir=target_dir, config=None
                )
            )

            # Verify files were extracted
            assert (target_dir / "foothold_test.lua").exists()
            assert (target_dir / "foothold_test_storage.csv").exists()
            assert (target_dir / "foothold_test.lua").read_text() == "-- campaign code"
            assert (target_dir / "foothold_test_storage.csv").read_text() == "test,data"

    def test_restore_checkpoint_returns_list_of_restored_files(self):
        """restore_checkpoint should return a list of restored file paths."""
        from foothold_checkpoint.core.storage import restore_checkpoint, save_checkpoint
        from tests.conftest import make_simple_campaign, make_test_config

        with tempfile.TemporaryDirectory() as tmpdir:
            source_dir = Path(tmpdir) / "source"
            source_dir.mkdir()
            (source_dir / "foothold_test.lua").write_text("-- test")

            config = make_test_config(
                campaigns={"test": make_simple_campaign("Test", ["foothold_test.lua"])}
            )

            checkpoint_dir = Path(tmpdir) / "checkpoints"
            checkpoint_dir.mkdir()
            checkpoint_path = asyncio.run(
                save_checkpoint(
                    campaign_name="test",
                    server_name="server",
                    source_dir=source_dir,
                    output_dir=checkpoint_dir,
                    config=config,
                )
            )

            target_dir = Path(tmpdir) / "target"
            target_dir.mkdir()

            restored_files = asyncio.run(
                restore_checkpoint(
                    checkpoint_path=checkpoint_path, target_dir=target_dir, config=None
                )
            )

            assert isinstance(restored_files, list)
            assert len(restored_files) >= 1
            assert all(isinstance(f, Path) for f in restored_files)
            assert any(f.name == "foothold_test.lua" for f in restored_files)

    def test_restore_checkpoint_raises_error_if_checkpoint_not_exists(self):
        """restore_checkpoint should raise FileNotFoundError if checkpoint doesn't exist."""
        from foothold_checkpoint.core.storage import restore_checkpoint

        with tempfile.TemporaryDirectory() as tmpdir:
            checkpoint_path = Path(tmpdir) / "nonexistent.zip"
            target_dir = Path(tmpdir) / "target"
            target_dir.mkdir()

            with pytest.raises(FileNotFoundError, match="Checkpoint file not found"):
                asyncio.run(
                    restore_checkpoint(
                        checkpoint_path=checkpoint_path, target_dir=target_dir, config=None
                    )
                )

    def test_restore_checkpoint_raises_error_if_not_valid_zip(self):
        """restore_checkpoint should raise error if file is not a valid ZIP."""
        from foothold_checkpoint.core.storage import restore_checkpoint

        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a non-ZIP file
            invalid_zip = Path(tmpdir) / "invalid.zip"
            invalid_zip.write_text("this is not a ZIP file")

            target_dir = Path(tmpdir) / "target"
            target_dir.mkdir()

            with pytest.raises(ValueError, match="not a valid ZIP archive"):
                asyncio.run(
                    restore_checkpoint(
                        checkpoint_path=invalid_zip, target_dir=target_dir, config=None
                    )
                )

    def test_restore_checkpoint_raises_error_if_metadata_missing(self):
        """restore_checkpoint should raise error if metadata.json is missing."""
        import zipfile

        from foothold_checkpoint.core.storage import restore_checkpoint

        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a ZIP without metadata.json
            zip_path = Path(tmpdir) / "no_metadata.zip"
            with zipfile.ZipFile(zip_path, "w") as zf:
                zf.writestr("foothold_test.lua", "-- test")

            target_dir = Path(tmpdir) / "target"
            target_dir.mkdir()

            with pytest.raises(ValueError, match="missing metadata"):
                asyncio.run(
                    restore_checkpoint(checkpoint_path=zip_path, target_dir=target_dir, config=None)
                )

    def test_restore_checkpoint_raises_error_if_metadata_invalid_json(self):
        """restore_checkpoint should raise error if metadata.json has invalid JSON."""
        import zipfile

        from foothold_checkpoint.core.storage import restore_checkpoint

        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a ZIP with invalid JSON in metadata
            zip_path = Path(tmpdir) / "invalid_metadata.zip"
            with zipfile.ZipFile(zip_path, "w") as zf:
                zf.writestr("metadata.json", "{ invalid json }")

            target_dir = Path(tmpdir) / "target"
            target_dir.mkdir()

            with pytest.raises(ValueError, match="Invalid metadata JSON"):
                asyncio.run(
                    restore_checkpoint(checkpoint_path=zip_path, target_dir=target_dir, config=None)
                )

    def test_restore_checkpoint_raises_error_if_target_dir_not_exists(self):
        """restore_checkpoint should raise error if target directory doesn't exist."""
        from foothold_checkpoint.core.storage import restore_checkpoint, save_checkpoint
        from tests.conftest import make_simple_campaign, make_test_config

        with tempfile.TemporaryDirectory() as tmpdir:
            source_dir = Path(tmpdir) / "source"
            source_dir.mkdir()
            (source_dir / "foothold_test.lua").write_text("-- test")

            config = make_test_config(
                campaigns={"test": make_simple_campaign("Test", ["foothold_test.lua"])}
            )

            checkpoint_dir = Path(tmpdir) / "checkpoints"
            checkpoint_dir.mkdir()
            checkpoint_path = asyncio.run(
                save_checkpoint(
                    campaign_name="test",
                    server_name="server",
                    source_dir=source_dir,
                    output_dir=checkpoint_dir,
                    config=config,
                )
            )

            target_dir = Path(tmpdir) / "nonexistent_target"

            with pytest.raises(FileNotFoundError, match="Target directory does not exist"):
                asyncio.run(
                    restore_checkpoint(
                        checkpoint_path=checkpoint_path, target_dir=target_dir, config=None
                    )
                )

    def test_restore_checkpoint_raises_error_if_target_not_writable(self):
        """restore_checkpoint should raise error if target directory is not writable."""
        import os

        if os.name == "nt":
            pytest.skip("Permission tests unreliable on Windows")

        from foothold_checkpoint.core.storage import restore_checkpoint, save_checkpoint
        from tests.conftest import make_simple_campaign, make_test_config

        with tempfile.TemporaryDirectory() as tmpdir:
            source_dir = Path(tmpdir) / "source"
            source_dir.mkdir()
            (source_dir / "foothold_test.lua").write_text("-- test")

            config = make_test_config(
                campaigns={"test": make_simple_campaign("Test", ["foothold_test.lua"])}
            )

            checkpoint_dir = Path(tmpdir) / "checkpoints"
            checkpoint_dir.mkdir()
            checkpoint_path = asyncio.run(
                save_checkpoint(
                    campaign_name="test",
                    server_name="server",
                    source_dir=source_dir,
                    output_dir=checkpoint_dir,
                    config=config,
                )
            )

            target_dir = Path(tmpdir) / "readonly_target"
            target_dir.mkdir()
            target_dir.chmod(0o444)  # Read-only

            try:
                with pytest.raises(PermissionError):
                    asyncio.run(
                        restore_checkpoint(
                            checkpoint_path=checkpoint_path, target_dir=target_dir, config=None
                        )
                    )
            finally:
                target_dir.chmod(0o755)

    def test_restore_checkpoint_verifies_checksums(self):
        """restore_checkpoint should verify file checksums before extraction."""
        import zipfile

        from foothold_checkpoint.core.storage import restore_checkpoint, save_checkpoint
        from tests.conftest import make_simple_campaign, make_test_config

        with tempfile.TemporaryDirectory() as tmpdir:
            source_dir = Path(tmpdir) / "source"
            source_dir.mkdir()
            (source_dir / "foothold_test.lua").write_text("-- test content")

            config = make_test_config(
                campaigns={"test": make_simple_campaign("Test", ["foothold_test.lua"])}
            )

            checkpoint_dir = Path(tmpdir) / "checkpoints"
            checkpoint_dir.mkdir()
            checkpoint_path = asyncio.run(
                save_checkpoint(
                    campaign_name="test",
                    server_name="server",
                    source_dir=source_dir,
                    output_dir=checkpoint_dir,
                    config=config,
                )
            )

            # Tamper with the ZIP by recreating it with wrong content but same metadata
            with zipfile.ZipFile(checkpoint_path, "r") as zf:
                metadata_json = zf.read("metadata.json")

            # Recreate ZIP with tampered content
            temp_zip = Path(tmpdir) / "tampered.zip"
            with zipfile.ZipFile(temp_zip, "w") as zf:
                zf.writestr("metadata.json", metadata_json)
                zf.writestr("foothold_test.lua", "-- tampered content")

            # Replace original with tampered
            temp_zip.replace(checkpoint_path)

            target_dir = Path(tmpdir) / "target"
            target_dir.mkdir()

            with pytest.raises(ValueError, match="Checksum mismatch"):
                asyncio.run(
                    restore_checkpoint(
                        checkpoint_path=checkpoint_path, target_dir=target_dir, config=None
                    )
                )

    def test_restore_checkpoint_excludes_foothold_ranks_by_default(self):
        """restore_checkpoint should exclude Foothold_Ranks.lua by default."""
        from foothold_checkpoint.core.storage import restore_checkpoint, save_checkpoint
        from tests.conftest import make_simple_campaign, make_test_config

        with tempfile.TemporaryDirectory() as tmpdir:
            source_dir = Path(tmpdir) / "source"
            source_dir.mkdir()
            (source_dir / "foothold_test.lua").write_text("-- campaign")
            (source_dir / "Foothold_Ranks.lua").write_text("-- ranks")

            config = make_test_config(
                campaigns={"test": make_simple_campaign("Test", ["foothold_test.lua"])}
            )

            checkpoint_dir = Path(tmpdir) / "checkpoints"
            checkpoint_dir.mkdir()
            checkpoint_path = asyncio.run(
                save_checkpoint(
                    campaign_name="test",
                    server_name="server",
                    source_dir=source_dir,
                    output_dir=checkpoint_dir,
                    config=config,
                )
            )

            target_dir = Path(tmpdir) / "target"
            target_dir.mkdir()

            restored_files = asyncio.run(
                restore_checkpoint(
                    checkpoint_path=checkpoint_path, target_dir=target_dir, config=None
                )
            )

            # Campaign file should be restored
            assert (target_dir / "foothold_test.lua").exists()
            # Ranks file should NOT be restored
            assert not (target_dir / "Foothold_Ranks.lua").exists()
            # Ranks file should not be in returned list
            assert not any(f.name == "Foothold_Ranks.lua" for f in restored_files)

    def test_restore_checkpoint_includes_ranks_with_flag(self):
        """restore_checkpoint should restore Foothold_Ranks.lua when restore_ranks=True."""
        from foothold_checkpoint.core.storage import restore_checkpoint, save_checkpoint
        from tests.conftest import make_simple_campaign, make_test_config

        with tempfile.TemporaryDirectory() as tmpdir:
            source_dir = Path(tmpdir) / "source"
            source_dir.mkdir()
            (source_dir / "foothold_test.lua").write_text("-- campaign")
            (source_dir / "Foothold_Ranks.lua").write_text("-- ranks")

            config = make_test_config(
                campaigns={"test": make_simple_campaign("Test", ["foothold_test.lua"])}
            )

            checkpoint_dir = Path(tmpdir) / "checkpoints"
            checkpoint_dir.mkdir()
            checkpoint_path = asyncio.run(
                save_checkpoint(
                    campaign_name="test",
                    server_name="server",
                    source_dir=source_dir,
                    output_dir=checkpoint_dir,
                    config=config,
                )
            )

            target_dir = Path(tmpdir) / "target"
            target_dir.mkdir()

            restored_files = asyncio.run(
                restore_checkpoint(
                    checkpoint_path=checkpoint_path,
                    target_dir=target_dir,
                    restore_ranks=True,
                    config=None,
                )
            )

            # Both files should be restored
            assert (target_dir / "foothold_test.lua").exists()
            assert (target_dir / "Foothold_Ranks.lua").exists()
            assert any(f.name == "Foothold_Ranks.lua" for f in restored_files)

    def test_restore_checkpoint_warns_if_ranks_requested_but_not_in_checkpoint(self):
        """restore_checkpoint should warn if restore_ranks=True but Foothold_Ranks.lua not in checkpoint."""
        from foothold_checkpoint.core.storage import restore_checkpoint, save_checkpoint
        from tests.conftest import make_simple_campaign, make_test_config

        with tempfile.TemporaryDirectory() as tmpdir:
            source_dir = Path(tmpdir) / "source"
            source_dir.mkdir()
            (source_dir / "foothold_test.lua").write_text("-- campaign")
            # NO Foothold_Ranks.lua

            config = make_test_config(
                campaigns={"test": make_simple_campaign("Test", ["foothold_test.lua"])}
            )

            checkpoint_dir = Path(tmpdir) / "checkpoints"
            checkpoint_dir.mkdir()
            checkpoint_path = asyncio.run(
                save_checkpoint(
                    campaign_name="test",
                    server_name="server",
                    source_dir=source_dir,
                    output_dir=checkpoint_dir,
                    config=config,
                )
            )

            target_dir = Path(tmpdir) / "target"
            target_dir.mkdir()

            # Should not raise error, should just warn/log
            restored_files = asyncio.run(
                restore_checkpoint(
                    checkpoint_path=checkpoint_path,
                    target_dir=target_dir,
                    restore_ranks=True,
                    config=None,
                )
            )

            # Should restore campaign file successfully
            assert (target_dir / "foothold_test.lua").exists()
            assert not any(f.name == "Foothold_Ranks.lua" for f in restored_files)

    def test_restore_checkpoint_prompts_confirmation_on_overwrite(self):
        """restore_checkpoint should prompt for confirmation when overwriting existing files."""
        from foothold_checkpoint.core.storage import restore_checkpoint, save_checkpoint
        from tests.conftest import make_simple_campaign, make_test_config

        with tempfile.TemporaryDirectory() as tmpdir:
            source_dir = Path(tmpdir) / "source"
            source_dir.mkdir()
            (source_dir / "foothold_test.lua").write_text("-- campaign")

            config = make_test_config(
                campaigns={"test": make_simple_campaign("Test", ["foothold_test.lua"])}
            )

            checkpoint_dir = Path(tmpdir) / "checkpoints"
            checkpoint_dir.mkdir()
            checkpoint_path = asyncio.run(
                save_checkpoint(
                    campaign_name="test",
                    server_name="server",
                    source_dir=source_dir,
                    output_dir=checkpoint_dir,
                    config=config,
                )
            )

            target_dir = Path(tmpdir) / "target"
            target_dir.mkdir()
            # Create existing file
            (target_dir / "foothold_test.lua").write_text("-- existing content")

            # Mock user cancelling confirmation
            import unittest.mock

            with (
                unittest.mock.patch("builtins.input", return_value="n"),
                pytest.raises(RuntimeError, match="Restoration cancelled"),
            ):
                asyncio.run(
                    restore_checkpoint(
                        checkpoint_path=checkpoint_path, target_dir=target_dir, config=None
                    )
                )

            # Original file should remain unchanged
            assert (target_dir / "foothold_test.lua").read_text() == "-- existing content"

    def test_restore_checkpoint_proceeds_on_confirmation(self):
        """restore_checkpoint should proceed with restoration when user confirms overwrite."""
        from foothold_checkpoint.core.storage import restore_checkpoint, save_checkpoint
        from tests.conftest import make_simple_campaign, make_test_config

        with tempfile.TemporaryDirectory() as tmpdir:
            source_dir = Path(tmpdir) / "source"
            source_dir.mkdir()
            (source_dir / "foothold_test.lua").write_text("-- new campaign")

            config = make_test_config(
                campaigns={"test": make_simple_campaign("Test", ["foothold_test.lua"])}
            )

            checkpoint_dir = Path(tmpdir) / "checkpoints"
            checkpoint_dir.mkdir()
            checkpoint_path = asyncio.run(
                save_checkpoint(
                    campaign_name="test",
                    server_name="server",
                    source_dir=source_dir,
                    output_dir=checkpoint_dir,
                    config=config,
                )
            )

            target_dir = Path(tmpdir) / "target"
            target_dir.mkdir()
            (target_dir / "foothold_test.lua").write_text("-- old content")

            import unittest.mock

            with unittest.mock.patch("builtins.input", return_value="y"):
                restored_files = asyncio.run(
                    restore_checkpoint(
                        checkpoint_path=checkpoint_path, target_dir=target_dir, config=None
                    )
                )

            # File should be overwritten
            assert (target_dir / "foothold_test.lua").read_text() == "-- new campaign"
            assert len(restored_files) >= 1

    def test_restore_checkpoint_skips_prompt_for_empty_target(self):
        """restore_checkpoint should not prompt when target directory is empty."""
        from foothold_checkpoint.core.storage import restore_checkpoint, save_checkpoint
        from tests.conftest import make_simple_campaign, make_test_config

        with tempfile.TemporaryDirectory() as tmpdir:
            source_dir = Path(tmpdir) / "source"
            source_dir.mkdir()
            (source_dir / "foothold_test.lua").write_text("-- campaign")

            config = make_test_config(
                campaigns={"test": make_simple_campaign("Test", ["foothold_test.lua"])}
            )

            checkpoint_dir = Path(tmpdir) / "checkpoints"
            checkpoint_dir.mkdir()
            checkpoint_path = asyncio.run(
                save_checkpoint(
                    campaign_name="test",
                    server_name="server",
                    source_dir=source_dir,
                    output_dir=checkpoint_dir,
                    config=config,
                )
            )

            target_dir = Path(tmpdir) / "target"
            target_dir.mkdir()
            # Empty target - no prompt should be shown

            import unittest.mock

            # Should not call input
            with unittest.mock.patch("builtins.input") as mock_input:
                restored_files = asyncio.run(
                    restore_checkpoint(
                        checkpoint_path=checkpoint_path, target_dir=target_dir, config=None
                    )
                )
                mock_input.assert_not_called()

            assert len(restored_files) >= 1

    def test_restore_checkpoint_supports_progress_callback(self):
        """restore_checkpoint should call progress callback during restoration."""
        from foothold_checkpoint.core.storage import restore_checkpoint, save_checkpoint
        from tests.conftest import make_simple_campaign, make_test_config

        with tempfile.TemporaryDirectory() as tmpdir:
            source_dir = Path(tmpdir) / "source"
            source_dir.mkdir()
            (source_dir / "foothold_test.lua").write_text("-- campaign")
            (source_dir / "foothold_test_storage.csv").write_text("data")

            config = make_test_config(
                campaigns={
                    "test": make_simple_campaign(
                        "Test",
                        ["foothold_test.lua"],
                        storage=["foothold_test_storage.csv"],
                    )
                }
            )

            checkpoint_dir = Path(tmpdir) / "checkpoints"
            checkpoint_dir.mkdir()
            checkpoint_path = asyncio.run(
                save_checkpoint(
                    campaign_name="test",
                    server_name="server",
                    source_dir=source_dir,
                    output_dir=checkpoint_dir,
                    config=config,
                )
            )

            target_dir = Path(tmpdir) / "target"
            target_dir.mkdir()

            progress_calls = []

            def progress_callback(message: str, current: int, total: int):
                progress_calls.append((message, current, total))

            restored_files = asyncio.run(
                restore_checkpoint(
                    checkpoint_path=checkpoint_path,
                    target_dir=target_dir,
                    progress_callback=progress_callback,
                )
            )

            # Should have called progress callback
            assert len(progress_calls) > 0
            assert any(
                "verifying" in msg.lower() or "extracting" in msg.lower()
                for msg, _, _ in progress_calls
            )
            assert len(restored_files) >= 1

    def test_restore_checkpoint_handles_disk_full_gracefully(self):
        """restore_checkpoint should handle disk full errors gracefully."""
        from foothold_checkpoint.core.storage import restore_checkpoint, save_checkpoint
        from tests.conftest import make_simple_campaign, make_test_config

        with tempfile.TemporaryDirectory() as tmpdir:
            source_dir = Path(tmpdir) / "source"
            source_dir.mkdir()
            (source_dir / "foothold_test.lua").write_text("-- test" * 10000)

            config = make_test_config(
                campaigns={"test": make_simple_campaign("Test", ["foothold_test.lua"])}
            )

            checkpoint_dir = Path(tmpdir) / "checkpoints"
            checkpoint_dir.mkdir()
            checkpoint_path = asyncio.run(
                save_checkpoint(
                    campaign_name="test",
                    server_name="server",
                    source_dir=source_dir,
                    output_dir=checkpoint_dir,
                    config=config,
                )
            )

            target_dir = Path(tmpdir) / "target"
            target_dir.mkdir()

            # Mock disk full error on write_bytes
            import unittest.mock

            def mock_write_bytes_raises(*args, **kwargs):
                raise OSError("No space left on device")

            # Patch write_bytes on Path instances
            with unittest.mock.patch.object(
                Path, "write_bytes", side_effect=mock_write_bytes_raises, autospec=False
            ):
                # Need to re-create target_dir Path instance after patching
                target_dir_patched = Path(tmpdir) / "target"
                with pytest.raises(OSError, match="No space left on device"):
                    asyncio.run(
                        restore_checkpoint(
                            checkpoint_path=checkpoint_path, target_dir=target_dir_patched
                        )
                    )
        """restore_checkpoint should rename files when campaign name has evolved."""
        import hashlib
        import json
        import zipfile

        from foothold_checkpoint.core.config import Config, ServerConfig
        from foothold_checkpoint.core.storage import restore_checkpoint
        from tests.conftest import make_simple_campaign

        with tempfile.TemporaryDirectory() as tmpdir:
            # Create config with campaign name evolution (old names in files list)
            config = Config(
                checkpoints_dir=Path(tmpdir) / "checkpoints",
                servers={
                    "test-server": ServerConfig(
                        path=Path(tmpdir) / "server", description="Test server"
                    )
                },
                campaigns={
                    "germany_modern": make_simple_campaign(
                        "Germany Modern",
                        persistence_files=[
                            "FootHold_germany_modern.lua",  # Current/preferred name (first)
                            "FootHold_GCW_Modern.lua",  # Old name (still accepted)
                        ],
                        storage=[
                            "FootHold_germany_modern_storage.csv",  # Current name
                            "FootHold_GCW_Modern_storage.csv",  # Old name
                        ],
                    )
                },
            )

            # Create a checkpoint with old campaign name files
            checkpoint_path = Path(tmpdir) / "checkpoint.zip"
            with zipfile.ZipFile(checkpoint_path, "w") as zf:
                # Add files with historical campaign name
                old_lua_content = b"-- GCW Modern campaign"
                old_csv_content = b"gcw,data"

                zf.writestr("FootHold_GCW_Modern.lua", old_lua_content)
                zf.writestr("FootHold_GCW_Modern_storage.csv", old_csv_content)

                # Add metadata with checksums
                metadata = {
                    "campaign_name": "germany_modern",  # Current campaign ID
                    "server_name": "test-server",
                    "created_at": "2024-02-13T14:30:00Z",
                    "files": {
                        "FootHold_GCW_Modern.lua": f"sha256:{hashlib.sha256(old_lua_content).hexdigest()}",
                        "FootHold_GCW_Modern_storage.csv": f"sha256:{hashlib.sha256(old_csv_content).hexdigest()}",
                    },
                }
                zf.writestr("metadata.json", json.dumps(metadata))

            target_dir = Path(tmpdir) / "target"
            target_dir.mkdir()

            # Restore with config (should use target directory as-is since metadata has gcw_modern)
            restored_files = asyncio.run(
                restore_checkpoint(
                    checkpoint_path=checkpoint_path,
                    target_dir=target_dir,
                    config=config,
                    skip_overwrite_check=True,
                    auto_backup=False,  # Disable auto-backup for this test
                )
            )

            # Files should still exist with original names (or may be renamed based on config logic)
            # The key is that restoration completes successfully
            assert len(restored_files) == 2

            # Content should be preserved
            assert (target_dir / "FootHold_germany_modern.lua").read_bytes() == old_lua_content
            assert (
                target_dir / "FootHold_germany_modern_storage.csv"
            ).read_bytes() == old_csv_content

            # Returned paths should use new names
            assert any(f.name == "FootHold_germany_modern.lua" for f in restored_files)
            assert any(f.name == "FootHold_germany_modern_storage.csv" for f in restored_files)

    def test_restore_checkpoint_keeps_files_unchanged_when_no_name_evolution(self):
        """restore_checkpoint should keep filenames unchanged when campaign name hasn't evolved."""
        import hashlib
        import json
        import zipfile

        from foothold_checkpoint.core.config import Config, ServerConfig
        from foothold_checkpoint.core.storage import restore_checkpoint
        from tests.conftest import make_simple_campaign

        with tempfile.TemporaryDirectory() as tmpdir:
            config = Config(
                checkpoints_dir=Path(tmpdir) / "checkpoints",
                servers={
                    "test-server": ServerConfig(
                        path=Path(tmpdir) / "server", description="Test server"
                    )
                },
                campaigns={
                    "afghanistan": make_simple_campaign(
                        "Afghanistan", persistence_files=["foothold_afghanistan.lua"]
                    )
                },
            )

            checkpoint_path = Path(tmpdir) / "checkpoint.zip"
            with zipfile.ZipFile(checkpoint_path, "w") as zf:
                lua_content = b"-- Afghanistan campaign"

                zf.writestr("foothold_afghanistan.lua", lua_content)

                metadata = {
                    "campaign_name": "afghanistan",
                    "server_name": "test-server",
                    "created_at": "2024-02-13T14:30:00Z",
                    "files": {
                        "foothold_afghanistan.lua": f"sha256:{hashlib.sha256(lua_content).hexdigest()}",
                    },
                }
                zf.writestr("metadata.json", json.dumps(metadata))

            target_dir = Path(tmpdir) / "target"
            target_dir.mkdir()

            asyncio.run(
                restore_checkpoint(
                    checkpoint_path=checkpoint_path,
                    target_dir=target_dir,
                    config=config,
                    skip_overwrite_check=True,
                    auto_backup=False,  # Disable auto-backup for this test
                )
            )

            # Filename should be unchanged (campaign name hasn't evolved)
            assert (target_dir / "foothold_afghanistan.lua").exists()

    def test_restore_checkpoint_without_config_keeps_original_names(self):
        """restore_checkpoint without config should keep original filenames (backward compatibility)."""
        from foothold_checkpoint.core.storage import restore_checkpoint, save_checkpoint
        from tests.conftest import make_simple_campaign, make_test_config

        with tempfile.TemporaryDirectory() as tmpdir:
            source_dir = Path(tmpdir) / "source"
            source_dir.mkdir()
            (source_dir / "FootHold_GCW_Modern.lua").write_text("-- test")

            config = make_test_config(
                campaigns={
                    "gcw_modern": make_simple_campaign("GCW Modern", ["FootHold_GCW_Modern.lua"])
                }
            )

            checkpoint_dir = Path(tmpdir) / "checkpoints"
            checkpoint_dir.mkdir()
            checkpoint_path = asyncio.run(
                save_checkpoint(
                    campaign_name="gcw_modern",
                    server_name="test-server",
                    source_dir=source_dir,
                    output_dir=checkpoint_dir,
                    config=config,
                )
            )

            target_dir = Path(tmpdir) / "target"
            target_dir.mkdir()

            # Restore without config (backward compatibility)
            asyncio.run(
                restore_checkpoint(
                    checkpoint_path=checkpoint_path, target_dir=target_dir, config=None
                )
            )

            # Original filename should be preserved
            assert (target_dir / "FootHold_GCW_Modern.lua").exists()


class TestListCheckpoints:
    """Test suite for list_checkpoints function."""

    def test_list_checkpoints_returns_empty_list_for_empty_directory(self):
        """list_checkpoints should return an empty list when no checkpoints exist."""
        from foothold_checkpoint.core.storage import list_checkpoints

        with tempfile.TemporaryDirectory() as tmpdir:
            checkpoint_dir = Path(tmpdir) / "checkpoints"
            checkpoint_dir.mkdir()

            result = asyncio.run(list_checkpoints(checkpoint_dir))

            assert result == []

    def test_list_checkpoints_returns_list_of_checkpoint_info(self):
        """list_checkpoints should return a list of checkpoint metadata dictionaries."""
        from foothold_checkpoint.core.storage import list_checkpoints, save_checkpoint
        from tests.conftest import make_simple_campaign, make_test_config

        with tempfile.TemporaryDirectory() as tmpdir:
            source_dir = Path(tmpdir) / "source"
            source_dir.mkdir()
            checkpoint_dir = Path(tmpdir) / "checkpoints"
            checkpoint_dir.mkdir()

            # Create test campaign files
            (source_dir / "foothold_test.lua").write_text("-- test")
            (source_dir / "foothold_test_storage.csv").write_text("data")

            config = make_test_config(
                campaigns={
                    "test": make_simple_campaign(
                        "Test",
                        ["foothold_test.lua"],
                        storage=["foothold_test_storage.csv"],
                    )
                }
            )

            # Create a checkpoint
            asyncio.run(
                save_checkpoint(
                    campaign_name="test",
                    server_name="test-server",
                    source_dir=source_dir,
                    output_dir=checkpoint_dir,
                    config=config,
                )
            )

            result = asyncio.run(list_checkpoints(checkpoint_dir))

            assert len(result) == 1
            assert isinstance(result[0], dict)
            assert "filename" in result[0]
            assert "campaign" in result[0]
            assert "server" in result[0]
            assert "timestamp" in result[0]

    def test_list_checkpoints_includes_multiple_checkpoints(self):
        """list_checkpoints should return all valid checkpoints in the directory."""
        from foothold_checkpoint.core.storage import list_checkpoints, save_checkpoint
        from tests.conftest import make_simple_campaign, make_test_config

        with tempfile.TemporaryDirectory() as tmpdir:
            source_dir = Path(tmpdir) / "source"
            source_dir.mkdir()
            checkpoint_dir = Path(tmpdir) / "checkpoints"
            checkpoint_dir.mkdir()

            # Create test campaign files for first checkpoint
            (source_dir / "foothold_test.lua").write_text("-- test")
            (source_dir / "foothold_test_storage.csv").write_text("data")

            config = make_test_config(
                campaigns={
                    "test": make_simple_campaign(
                        "Test",
                        ["foothold_test.lua"],
                        storage=["foothold_test_storage.csv"],
                    ),
                    "test2": make_simple_campaign(
                        "Test2",
                        ["foothold_test2.lua"],
                        storage=["foothold_test2_storage.csv"],
                    ),
                }
            )

            asyncio.run(
                save_checkpoint(
                    campaign_name="test",
                    server_name="server1",
                    source_dir=source_dir,
                    output_dir=checkpoint_dir,
                    config=config,
                )
            )

            # Create test campaign files for second checkpoint
            (source_dir / "foothold_test2.lua").write_text("-- test2")
            (source_dir / "foothold_test2_storage.csv").write_text("data2")

            asyncio.run(
                save_checkpoint(
                    campaign_name="test2",
                    server_name="server2",
                    source_dir=source_dir,
                    output_dir=checkpoint_dir,
                    config=config,
                )
            )

            result = asyncio.run(list_checkpoints(checkpoint_dir))

            assert len(result) == 2

    def test_list_checkpoints_reads_metadata_without_extracting_zip(self):
        """list_checkpoints should read metadata.json without extracting the entire ZIP."""
        import json
        import zipfile

        from foothold_checkpoint.core.storage import list_checkpoints

        with tempfile.TemporaryDirectory() as tmpdir:
            checkpoint_dir = Path(tmpdir) / "checkpoints"
            checkpoint_dir.mkdir()

            # Create a large fake checkpoint ZIP
            checkpoint_path = checkpoint_dir / "test_checkpoint.zip"
            with zipfile.ZipFile(checkpoint_path, "w") as zf:
                # Add metadata (using Pydantic field names)
                metadata = {
                    "campaign_name": "test",
                    "server_name": "test-server",
                    "created_at": "2024-02-13T14:30:00Z",
                    "files": {
                        "foothold_test.lua": "sha256:abc123",
                        "foothold_test_storage.csv": "sha256:def456",
                    },
                }
                zf.writestr("metadata.json", json.dumps(metadata))

                # Add a large fake file (simulate large storage.csv)
                # We create a 10 MB file in memory
                large_data = b"x" * (10 * 1024 * 1024)
                zf.writestr("foothold_test_storage.csv", large_data)

            # List checkpoints (should be fast, not extracting 10 MB)
            result = asyncio.run(list_checkpoints(checkpoint_dir))

            assert len(result) == 1
            assert result[0]["campaign"] == "test"
            # The test passes if it completes quickly (no assertion for speed, but conceptually)

    def test_list_checkpoints_filters_by_server(self):
        """list_checkpoints should filter checkpoints by server name."""
        import time

        from foothold_checkpoint.core.storage import list_checkpoints, save_checkpoint
        from tests.conftest import make_simple_campaign, make_test_config

        with tempfile.TemporaryDirectory() as tmpdir:
            source_dir = Path(tmpdir) / "source"
            source_dir.mkdir()
            checkpoint_dir = Path(tmpdir) / "checkpoints"
            checkpoint_dir.mkdir()

            (source_dir / "foothold_test.lua").write_text("-- test")
            (source_dir / "foothold_test_storage.csv").write_text("data")

            config = make_test_config(
                campaigns={
                    "test": make_simple_campaign(
                        "Test",
                        ["foothold_test.lua"],
                        storage=["foothold_test_storage.csv"],
                    )
                }
            )

            # Create checkpoints for different servers
            asyncio.run(
                save_checkpoint(
                    campaign_name="test",
                    server_name="server1",
                    source_dir=source_dir,
                    output_dir=checkpoint_dir,
                    config=config,
                )
            )
            time.sleep(1)  # Ensure different timestamp for unique filename
            asyncio.run(
                save_checkpoint(
                    campaign_name="test",
                    server_name="server2",
                    source_dir=source_dir,
                    output_dir=checkpoint_dir,
                    config=config,
                )
            )

            result = asyncio.run(list_checkpoints(checkpoint_dir, server_filter="server1"))

            assert len(result) == 1
            assert result[0]["server"] == "server1"

    def test_list_checkpoints_filters_by_campaign(self):
        """list_checkpoints should filter checkpoints by campaign name."""
        from foothold_checkpoint.core.storage import list_checkpoints, save_checkpoint
        from tests.conftest import make_simple_campaign, make_test_config

        with tempfile.TemporaryDirectory() as tmpdir:
            source_dir = Path(tmpdir) / "source"
            source_dir.mkdir()
            checkpoint_dir = Path(tmpdir) / "checkpoints"
            checkpoint_dir.mkdir()

            # Create campaign files for campaign1
            (source_dir / "foothold_campaign1.lua").write_text("-- campaign1")
            (source_dir / "foothold_campaign1_storage.csv").write_text("data1")

            config = make_test_config(
                campaigns={
                    "campaign1": make_simple_campaign(
                        "Campaign1",
                        ["foothold_campaign1.lua"],
                        storage=["foothold_campaign1_storage.csv"],
                    ),
                    "campaign2": make_simple_campaign(
                        "Campaign2",
                        ["foothold_campaign2.lua"],
                        storage=["foothold_campaign2_storage.csv"],
                    ),
                }
            )

            asyncio.run(
                save_checkpoint(
                    campaign_name="campaign1",
                    server_name="server",
                    source_dir=source_dir,
                    output_dir=checkpoint_dir,
                    config=config,
                )
            )

            # Create campaign files for campaign2
            (source_dir / "foothold_campaign2.lua").write_text("-- campaign2")
            (source_dir / "foothold_campaign2_storage.csv").write_text("data2")

            asyncio.run(
                save_checkpoint(
                    campaign_name="campaign2",
                    server_name="server",
                    source_dir=source_dir,
                    output_dir=checkpoint_dir,
                    config=config,
                )
            )

            result = asyncio.run(list_checkpoints(checkpoint_dir, campaign_filter="campaign1"))

            assert len(result) == 1
            assert result[0]["campaign"] == "campaign1"

    def test_list_checkpoints_filters_by_combined_server_and_campaign(self):
        """list_checkpoints should filter by both server and campaign."""
        import time

        from foothold_checkpoint.core.storage import list_checkpoints, save_checkpoint
        from tests.conftest import make_simple_campaign, make_test_config

        with tempfile.TemporaryDirectory() as tmpdir:
            source_dir = Path(tmpdir) / "source"
            source_dir.mkdir()
            checkpoint_dir = Path(tmpdir) / "checkpoints"
            checkpoint_dir.mkdir()

            # Create campaign files for campaign1
            (source_dir / "foothold_campaign1.lua").write_text("-- campaign1")
            (source_dir / "foothold_campaign1_storage.csv").write_text("data1")

            config = make_test_config(
                campaigns={
                    "campaign1": make_simple_campaign(
                        "Campaign1",
                        ["foothold_campaign1.lua"],
                        storage=["foothold_campaign1_storage.csv"],
                    ),
                    "campaign2": make_simple_campaign(
                        "Campaign2",
                        ["foothold_campaign2.lua"],
                        storage=["foothold_campaign2_storage.csv"],
                    ),
                }
            )

            asyncio.run(
                save_checkpoint(
                    campaign_name="campaign1",
                    server_name="server1",
                    source_dir=source_dir,
                    output_dir=checkpoint_dir,
                    config=config,
                )
            )

            # Create campaign files for campaign2
            (source_dir / "foothold_campaign2.lua").write_text("-- campaign2")
            (source_dir / "foothold_campaign2_storage.csv").write_text("data2")
            time.sleep(1)  # Ensure different timestamp

            asyncio.run(
                save_checkpoint(
                    campaign_name="campaign2",
                    server_name="server1",
                    source_dir=source_dir,
                    output_dir=checkpoint_dir,
                    config=config,
                )
            )
            time.sleep(1)  # Ensure different timestamp

            asyncio.run(
                save_checkpoint(
                    campaign_name="campaign1",
                    server_name="server2",
                    source_dir=source_dir,
                    output_dir=checkpoint_dir,
                    config=config,
                )
            )

            result = asyncio.run(
                list_checkpoints(
                    checkpoint_dir, server_filter="server1", campaign_filter="campaign1"
                )
            )

            assert len(result) == 1
            assert result[0]["server"] == "server1"
            assert result[0]["campaign"] == "campaign1"

    def test_list_checkpoints_sorts_chronologically_oldest_first_within_groups(self):
        """list_checkpoints should sort checkpoints by timestamp (oldest first within each group)."""
        import json
        import time
        import zipfile

        from foothold_checkpoint.core.storage import list_checkpoints

        with tempfile.TemporaryDirectory() as tmpdir:
            checkpoint_dir = Path(tmpdir) / "checkpoints"
            checkpoint_dir.mkdir()

            # Create checkpoints with different timestamps
            for i, timestamp in enumerate(
                ["2024-02-10T10:00:00Z", "2024-02-12T10:00:00Z", "2024-02-11T10:00:00Z"]
            ):
                checkpoint_path = checkpoint_dir / f"checkpoint_{i}.zip"
                with zipfile.ZipFile(checkpoint_path, "w") as zf:
                    metadata = {
                        "campaign_name": f"campaign{i}",
                        "server_name": "server",
                        "created_at": timestamp,
                        "files": {},
                    }
                    zf.writestr("metadata.json", json.dumps(metadata))
                time.sleep(0.01)  # Ensure different file creation times

            result = asyncio.run(list_checkpoints(checkpoint_dir))

            assert len(result) == 3
            # Should be sorted oldest first (chronologically within group)
            assert result[0]["timestamp"] == "2024-02-10T10:00:00Z"
            assert result[1]["timestamp"] == "2024-02-11T10:00:00Z"
            assert result[2]["timestamp"] == "2024-02-12T10:00:00Z"

    def test_list_checkpoints_includes_file_size(self):
        """list_checkpoints should include the file size for each checkpoint."""
        from foothold_checkpoint.core.storage import list_checkpoints, save_checkpoint
        from tests.conftest import make_simple_campaign, make_test_config

        with tempfile.TemporaryDirectory() as tmpdir:
            source_dir = Path(tmpdir) / "source"
            source_dir.mkdir()
            checkpoint_dir = Path(tmpdir) / "checkpoints"
            checkpoint_dir.mkdir()

            (source_dir / "foothold_test.lua").write_text("-- test content")
            (source_dir / "foothold_test_storage.csv").write_text("data content")

            config = make_test_config(
                campaigns={
                    "test": make_simple_campaign(
                        "Test",
                        ["foothold_test.lua"],
                        storage=["foothold_test_storage.csv"],
                    )
                }
            )

            asyncio.run(
                save_checkpoint(
                    campaign_name="test",
                    server_name="server",
                    source_dir=source_dir,
                    output_dir=checkpoint_dir,
                    config=config,
                )
            )

            result = asyncio.run(list_checkpoints(checkpoint_dir))

            assert len(result) == 1
            assert "size_bytes" in result[0]
            assert result[0]["size_bytes"] > 0

    def test_list_checkpoints_formats_file_size_human_readable(self):
        """list_checkpoints should include human-readable file size."""
        from foothold_checkpoint.core.storage import list_checkpoints, save_checkpoint
        from tests.conftest import make_simple_campaign, make_test_config

        with tempfile.TemporaryDirectory() as tmpdir:
            source_dir = Path(tmpdir) / "source"
            source_dir.mkdir()
            checkpoint_dir = Path(tmpdir) / "checkpoints"
            checkpoint_dir.mkdir()

            (source_dir / "foothold_test.lua").write_text("-- test")
            (source_dir / "foothold_test_storage.csv").write_text("data")

            config = make_test_config(
                campaigns={"test": make_simple_campaign("Test", ["foothold_test.lua"])}
            )

            asyncio.run(
                save_checkpoint(
                    campaign_name="test",
                    server_name="server",
                    source_dir=source_dir,
                    output_dir=checkpoint_dir,
                    config=config,
                )
            )

            result = asyncio.run(list_checkpoints(checkpoint_dir))

            assert len(result) == 1
            assert "size_human" in result[0]
            # Should be in format like "1.2 KB", "5.6 MB", etc.
            assert any(unit in result[0]["size_human"] for unit in ["B", "KB", "MB", "GB", "TB"])

    def test_list_checkpoints_handles_corrupted_checkpoint_gracefully(self):
        """list_checkpoints should skip corrupted checkpoints and continue."""

        from foothold_checkpoint.core.storage import list_checkpoints, save_checkpoint
        from tests.conftest import make_simple_campaign, make_test_config

        with tempfile.TemporaryDirectory() as tmpdir:
            source_dir = Path(tmpdir) / "source"
            source_dir.mkdir()
            checkpoint_dir = Path(tmpdir) / "checkpoints"
            checkpoint_dir.mkdir()

            # Create valid campaign files
            (source_dir / "foothold_valid.lua").write_text("-- valid")
            (source_dir / "foothold_valid_storage.csv").write_text("data")

            config = make_test_config(
                campaigns={"valid": make_simple_campaign("Valid", ["foothold_valid.lua"])}
            )

            # Create a valid checkpoint
            asyncio.run(
                save_checkpoint(
                    campaign_name="valid",
                    server_name="server",
                    source_dir=source_dir,
                    output_dir=checkpoint_dir,
                    config=config,
                )
            )

            # Create a corrupted ZIP file
            corrupted_path = checkpoint_dir / "corrupted.zip"
            corrupted_path.write_text("This is not a valid ZIP file")

            # Should return only the valid checkpoint
            result = asyncio.run(list_checkpoints(checkpoint_dir))

            assert len(result) == 1
            assert result[0]["campaign"] == "valid"

    def test_list_checkpoints_handles_missing_metadata_gracefully(self):
        """list_checkpoints should skip checkpoints with missing metadata."""
        import zipfile

        from foothold_checkpoint.core.storage import list_checkpoints, save_checkpoint
        from tests.conftest import make_simple_campaign, make_test_config

        with tempfile.TemporaryDirectory() as tmpdir:
            source_dir = Path(tmpdir) / "source"
            source_dir.mkdir()
            checkpoint_dir = Path(tmpdir) / "checkpoints"
            checkpoint_dir.mkdir()

            # Create valid campaign files
            (source_dir / "foothold_valid.lua").write_text("-- valid")
            (source_dir / "foothold_valid_storage.csv").write_text("data")

            config = make_test_config(
                campaigns={"valid": make_simple_campaign("Valid", ["foothold_valid.lua"])}
            )

            # Create a valid checkpoint
            asyncio.run(
                save_checkpoint(
                    campaign_name="valid",
                    server_name="server",
                    source_dir=source_dir,
                    output_dir=checkpoint_dir,
                    config=config,
                )
            )

            # Create a ZIP without metadata.json
            no_metadata_path = checkpoint_dir / "no_metadata.zip"
            with zipfile.ZipFile(no_metadata_path, "w") as zf:
                zf.writestr("some_file.txt", "content")

            # Should return only the valid checkpoint
            result = asyncio.run(list_checkpoints(checkpoint_dir))

            assert len(result) == 1
            assert result[0]["campaign"] == "valid"

    def test_list_checkpoints_raises_error_if_directory_not_exists(self):
        """list_checkpoints should raise FileNotFoundError if checkpoint directory doesn't exist."""
        from foothold_checkpoint.core.storage import list_checkpoints

        with tempfile.TemporaryDirectory() as tmpdir:
            non_existent_dir = Path(tmpdir) / "nonexistent"

            with pytest.raises(FileNotFoundError, match="Checkpoint directory not found"):
                asyncio.run(list_checkpoints(non_existent_dir))

    def test_list_checkpoints_skips_non_zip_files(self):
        """list_checkpoints should ignore non-ZIP files in the checkpoint directory."""
        from foothold_checkpoint.core.storage import list_checkpoints, save_checkpoint
        from tests.conftest import make_simple_campaign, make_test_config

        with tempfile.TemporaryDirectory() as tmpdir:
            source_dir = Path(tmpdir) / "source"
            source_dir.mkdir()
            checkpoint_dir = Path(tmpdir) / "checkpoints"
            checkpoint_dir.mkdir()

            (source_dir / "foothold_test.lua").write_text("-- test")
            (source_dir / "foothold_test_storage.csv").write_text("data")

            config = make_test_config(
                campaigns={
                    "test": make_simple_campaign(
                        "Test",
                        ["foothold_test.lua"],
                        storage=["foothold_test_storage.csv"],
                    )
                }
            )

            # Create a valid checkpoint
            asyncio.run(
                save_checkpoint(
                    campaign_name="test",
                    server_name="server",
                    source_dir=source_dir,
                    output_dir=checkpoint_dir,
                    config=config,
                )
            )

            # Create non-ZIP files
            (checkpoint_dir / "readme.txt").write_text("This is not a checkpoint")
            (checkpoint_dir / "notes.md").write_text("# Notes")

            result = asyncio.run(list_checkpoints(checkpoint_dir))

            # Should only return the valid checkpoint
            assert len(result) == 1
            assert result[0]["campaign"] == "test"

    def test_list_checkpoints_handles_invalid_json_metadata(self):
        """list_checkpoints should skip checkpoints with invalid JSON in metadata."""
        import zipfile

        from foothold_checkpoint.core.storage import list_checkpoints, save_checkpoint
        from tests.conftest import make_simple_campaign, make_test_config

        with tempfile.TemporaryDirectory() as tmpdir:
            source_dir = Path(tmpdir) / "source"
            source_dir.mkdir()
            checkpoint_dir = Path(tmpdir) / "checkpoints"
            checkpoint_dir.mkdir()

            # Create valid campaign files
            (source_dir / "foothold_valid.lua").write_text("-- valid")
            (source_dir / "foothold_valid_storage.csv").write_text("data")

            config = make_test_config(
                campaigns={
                    "valid": make_simple_campaign(
                        "Valid",
                        ["foothold_valid.lua"],
                        storage=["foothold_valid_storage.csv"],
                    )
                }
            )

            # Create a valid checkpoint
            asyncio.run(
                save_checkpoint(
                    campaign_name="valid",
                    server_name="server",
                    source_dir=source_dir,
                    output_dir=checkpoint_dir,
                    config=config,
                )
            )

            # Create a ZIP with invalid JSON metadata
            invalid_json_path = checkpoint_dir / "invalid_json.zip"
            with zipfile.ZipFile(invalid_json_path, "w") as zf:
                zf.writestr("metadata.json", '{"campaign": "test", invalid json here')

            result = asyncio.run(list_checkpoints(checkpoint_dir))

            # Should return only the valid checkpoint
            assert len(result) == 1
            assert result[0]["campaign"] == "valid"


class TestDeleteCheckpoint:
    """Test suite for delete_checkpoint function."""

    def test_delete_checkpoint_removes_existing_file(self):
        """delete_checkpoint should delete an existing checkpoint file."""
        from foothold_checkpoint.core.storage import delete_checkpoint, save_checkpoint
        from tests.conftest import make_simple_campaign, make_test_config

        with tempfile.TemporaryDirectory() as tmpdir:
            source_dir = Path(tmpdir) / "source"
            source_dir.mkdir()
            checkpoint_dir = Path(tmpdir) / "checkpoints"
            checkpoint_dir.mkdir()

            # Create a campaign file
            (source_dir / "foothold_test.lua").write_text("-- test campaign")

            config = make_test_config(
                campaigns={"test": make_simple_campaign("Test", ["foothold_test.lua"])}
            )

            # Save a checkpoint
            checkpoint_path = asyncio.run(
                save_checkpoint(
                    campaign_name="test",
                    server_name="test-server",
                    source_dir=source_dir,
                    output_dir=checkpoint_dir,
                    config=config,
                )
            )

            # Verify file exists
            assert checkpoint_path.exists()

            # Delete the checkpoint
            asyncio.run(delete_checkpoint(checkpoint_path, force=True))

            # Verify file is gone
            assert not checkpoint_path.exists()

    def test_delete_checkpoint_accepts_string_path(self):
        """delete_checkpoint should accept checkpoint path as string."""
        from foothold_checkpoint.core.storage import delete_checkpoint, save_checkpoint
        from tests.conftest import make_simple_campaign, make_test_config

        with tempfile.TemporaryDirectory() as tmpdir:
            source_dir = Path(tmpdir) / "source"
            source_dir.mkdir()
            checkpoint_dir = Path(tmpdir) / "checkpoints"
            checkpoint_dir.mkdir()

            (source_dir / "foothold_test.lua").write_text("-- test")

            config = make_test_config(
                campaigns={"test": make_simple_campaign("Test", ["foothold_test.lua"])}
            )

            checkpoint_path = asyncio.run(
                save_checkpoint(
                    campaign_name="test",
                    server_name="test-server",
                    source_dir=source_dir,
                    output_dir=checkpoint_dir,
                    config=config,
                )
            )

            # Delete using string path
            asyncio.run(delete_checkpoint(str(checkpoint_path), force=True))

            assert not checkpoint_path.exists()

    def test_delete_checkpoint_raises_error_if_file_not_exists(self):
        """delete_checkpoint should raise FileNotFoundError if checkpoint doesn't exist."""
        from foothold_checkpoint.core.storage import delete_checkpoint

        with tempfile.TemporaryDirectory() as tmpdir:
            checkpoint_dir = Path(tmpdir) / "checkpoints"
            checkpoint_dir.mkdir()
            non_existent = checkpoint_dir / "nonexistent.zip"

            with pytest.raises(FileNotFoundError, match="Checkpoint file not found"):
                asyncio.run(delete_checkpoint(non_existent, force=True))

    def test_delete_checkpoint_raises_error_if_not_a_zip(self):
        """delete_checkpoint should raise ValueError if file is not a ZIP."""
        from foothold_checkpoint.core.storage import delete_checkpoint

        with tempfile.TemporaryDirectory() as tmpdir:
            checkpoint_dir = Path(tmpdir) / "checkpoints"
            checkpoint_dir.mkdir()

            # Create a non-ZIP file
            not_zip = checkpoint_dir / "notazip.txt"
            not_zip.write_text("not a zip file")

            with pytest.raises(ValueError, match="Not a valid checkpoint file"):
                asyncio.run(delete_checkpoint(not_zip, force=True))

    def test_delete_checkpoint_raises_error_if_zip_missing_metadata(self):
        """delete_checkpoint should raise ValueError if ZIP lacks metadata.json."""
        import zipfile

        from foothold_checkpoint.core.storage import delete_checkpoint

        with tempfile.TemporaryDirectory() as tmpdir:
            checkpoint_dir = Path(tmpdir) / "checkpoints"
            checkpoint_dir.mkdir()

            # Create a ZIP without metadata.json
            invalid_zip = checkpoint_dir / "invalid.zip"
            with zipfile.ZipFile(invalid_zip, "w") as zf:
                zf.writestr("some_file.txt", "content")

            with pytest.raises(ValueError, match="Not a valid checkpoint.*missing metadata"):
                asyncio.run(delete_checkpoint(invalid_zip, force=True))

    def test_delete_checkpoint_returns_metadata_dict(self):
        """delete_checkpoint should return checkpoint metadata dict before deletion."""
        from foothold_checkpoint.core.storage import delete_checkpoint, save_checkpoint
        from tests.conftest import make_simple_campaign, make_test_config

        with tempfile.TemporaryDirectory() as tmpdir:
            source_dir = Path(tmpdir) / "source"
            source_dir.mkdir()
            checkpoint_dir = Path(tmpdir) / "checkpoints"
            checkpoint_dir.mkdir()

            (source_dir / "foothold_test.lua").write_text("-- test")

            config = make_test_config(
                campaigns={"test": make_simple_campaign("Test", ["foothold_test.lua"])}
            )

            checkpoint_path = asyncio.run(
                save_checkpoint(
                    campaign_name="test",
                    server_name="test-server",
                    source_dir=source_dir,
                    output_dir=checkpoint_dir,
                    config=config,
                    name="Test Checkpoint",
                    comment="Test comment",
                )
            )

            metadata = asyncio.run(delete_checkpoint(checkpoint_path, force=True))

            # Should return metadata dict
            assert isinstance(metadata, dict)
            assert metadata["campaign_name"] == "test"
            assert metadata["server_name"] == "test-server"
            assert metadata["name"] == "Test Checkpoint"
            assert metadata["comment"] == "Test comment"
            assert "created_at" in metadata

    def test_delete_checkpoint_handles_corrupted_metadata_gracefully(self):
        """delete_checkpoint should allow deletion even with corrupted metadata in force mode."""
        import zipfile

        from foothold_checkpoint.core.storage import delete_checkpoint

        with tempfile.TemporaryDirectory() as tmpdir:
            checkpoint_dir = Path(tmpdir) / "checkpoints"
            checkpoint_dir.mkdir()

            # Create a ZIP with corrupted metadata
            corrupted_zip = checkpoint_dir / "corrupted.zip"
            with zipfile.ZipFile(corrupted_zip, "w") as zf:
                zf.writestr("metadata.json", "invalid json {{{")

            # Should raise error even in force mode (cannot validate it's a checkpoint)
            with pytest.raises(ValueError, match="Cannot read checkpoint metadata"):
                asyncio.run(delete_checkpoint(corrupted_zip, force=True))

    @pytest.mark.skipif(
        sys.platform != "win32",
        reason="Linux allows deletion of read-only files when parent dir is writable",
    )
    def test_delete_checkpoint_handles_permission_error(self):
        """delete_checkpoint should raise PermissionError if file is read-only."""
        import os
        import stat

        from foothold_checkpoint.core.storage import delete_checkpoint, save_checkpoint
        from tests.conftest import make_simple_campaign, make_test_config

        with tempfile.TemporaryDirectory() as tmpdir:
            source_dir = Path(tmpdir) / "source"
            source_dir.mkdir()
            checkpoint_dir = Path(tmpdir) / "checkpoints"
            checkpoint_dir.mkdir()

            (source_dir / "foothold_test.lua").write_text("-- test")

            config = make_test_config(
                campaigns={"test": make_simple_campaign("Test", ["foothold_test.lua"])}
            )

            checkpoint_path = asyncio.run(
                save_checkpoint(
                    campaign_name="test",
                    server_name="test-server",
                    source_dir=source_dir,
                    output_dir=checkpoint_dir,
                    config=config,
                )
            )

            # Make file read-only
            os.chmod(checkpoint_path, stat.S_IRUSR | stat.S_IRGRP | stat.S_IROTH)

            try:
                with pytest.raises(PermissionError):
                    asyncio.run(delete_checkpoint(checkpoint_path, force=True))
            finally:
                # Restore permissions for cleanup
                with contextlib.suppress(OSError, FileNotFoundError):
                    os.chmod(
                        checkpoint_path,
                        stat.S_IRUSR | stat.S_IWUSR | stat.S_IRGRP | stat.S_IWGRP | stat.S_IROTH,
                    )

    def test_delete_checkpoint_force_mode_skips_confirmation(self):
        """delete_checkpoint with force=True should delete immediately without confirmation."""
        from foothold_checkpoint.core.storage import delete_checkpoint, save_checkpoint
        from tests.conftest import make_simple_campaign, make_test_config

        with tempfile.TemporaryDirectory() as tmpdir:
            source_dir = Path(tmpdir) / "source"
            source_dir.mkdir()
            checkpoint_dir = Path(tmpdir) / "checkpoints"
            checkpoint_dir.mkdir()

            (source_dir / "foothold_test.lua").write_text("-- test")

            config = make_test_config(
                campaigns={"test": make_simple_campaign("Test", ["foothold_test.lua"])}
            )

            checkpoint_path = asyncio.run(
                save_checkpoint(
                    campaign_name="test",
                    server_name="test-server",
                    source_dir=source_dir,
                    output_dir=checkpoint_dir,
                    config=config,
                )
            )

            # Force mode should delete immediately
            asyncio.run(delete_checkpoint(checkpoint_path, force=True))

            assert not checkpoint_path.exists()

    def test_delete_checkpoint_without_force_requires_confirmation_callback(self):
        """delete_checkpoint without force should require a confirmation callback."""
        from foothold_checkpoint.core.storage import delete_checkpoint, save_checkpoint
        from tests.conftest import make_simple_campaign, make_test_config

        with tempfile.TemporaryDirectory() as tmpdir:
            source_dir = Path(tmpdir) / "source"
            source_dir.mkdir()
            checkpoint_dir = Path(tmpdir) / "checkpoints"
            checkpoint_dir.mkdir()

            (source_dir / "foothold_test.lua").write_text("-- test")

            config = make_test_config(
                campaigns={"test": make_simple_campaign("Test", ["foothold_test.lua"])}
            )

            checkpoint_path = asyncio.run(
                save_checkpoint(
                    campaign_name="test",
                    server_name="test-server",
                    source_dir=source_dir,
                    output_dir=checkpoint_dir,
                    config=config,
                )
            )

            # Without force and without confirmation callback should raise error
            with pytest.raises(ValueError, match="Confirmation callback required when force=False"):
                asyncio.run(delete_checkpoint(checkpoint_path, force=False))

    def test_delete_checkpoint_calls_confirmation_callback(self):
        """delete_checkpoint should call confirmation callback and respect its result."""
        from foothold_checkpoint.core.storage import delete_checkpoint, save_checkpoint
        from tests.conftest import make_simple_campaign, make_test_config

        with tempfile.TemporaryDirectory() as tmpdir:
            source_dir = Path(tmpdir) / "source"
            source_dir.mkdir()
            checkpoint_dir = Path(tmpdir) / "checkpoints"
            checkpoint_dir.mkdir()

            (source_dir / "foothold_test.lua").write_text("-- test")

            config = make_test_config(
                campaigns={"test": make_simple_campaign("Test", ["foothold_test.lua"])}
            )

            checkpoint_path = asyncio.run(
                save_checkpoint(
                    campaign_name="test",
                    server_name="test-server",
                    source_dir=source_dir,
                    output_dir=checkpoint_dir,
                    config=config,
                )
            )

            # Confirmation callback returns False (user cancels)
            def confirm_no(metadata):
                return False

            result = asyncio.run(
                delete_checkpoint(checkpoint_path, force=False, confirm_callback=confirm_no)
            )

            # File should still exist
            assert checkpoint_path.exists()
            # Should return None when cancelled
            assert result is None

    def test_delete_checkpoint_confirmation_callback_receives_metadata(self):
        """delete_checkpoint should pass metadata dict to confirmation callback."""
        from foothold_checkpoint.core.storage import delete_checkpoint, save_checkpoint
        from tests.conftest import make_simple_campaign, make_test_config

        with tempfile.TemporaryDirectory() as tmpdir:
            source_dir = Path(tmpdir) / "source"
            source_dir.mkdir()
            checkpoint_dir = Path(tmpdir) / "checkpoints"
            checkpoint_dir.mkdir()

            (source_dir / "foothold_test.lua").write_text("-- test")

            config = make_test_config(
                campaigns={"test": make_simple_campaign("Test", ["foothold_test.lua"])}
            )

            checkpoint_path = asyncio.run(
                save_checkpoint(
                    campaign_name="test",
                    server_name="test-server",
                    source_dir=source_dir,
                    output_dir=checkpoint_dir,
                    name="Test Name",
                    config=config,
                )
            )

            received_metadata = {}

            def confirm_yes(metadata):
                received_metadata.update(metadata)
                return True

            asyncio.run(
                delete_checkpoint(checkpoint_path, force=False, confirm_callback=confirm_yes)
            )

            # Callback should have received metadata
            assert received_metadata["campaign_name"] == "test"
            assert received_metadata["server_name"] == "test-server"
            assert received_metadata["name"] == "Test Name"

    def test_delete_checkpoint_deletes_on_confirmation_yes(self):
        """delete_checkpoint should delete file when confirmation callback returns True."""
        from foothold_checkpoint.core.storage import delete_checkpoint, save_checkpoint
        from tests.conftest import make_simple_campaign, make_test_config

        with tempfile.TemporaryDirectory() as tmpdir:
            source_dir = Path(tmpdir) / "source"
            source_dir.mkdir()
            checkpoint_dir = Path(tmpdir) / "checkpoints"
            checkpoint_dir.mkdir()

            (source_dir / "foothold_test.lua").write_text("-- test")

            config = make_test_config(
                campaigns={"test": make_simple_campaign("Test", ["foothold_test.lua"])}
            )

            checkpoint_path = asyncio.run(
                save_checkpoint(
                    campaign_name="test",
                    server_name="test-server",
                    source_dir=source_dir,
                    output_dir=checkpoint_dir,
                    config=config,
                )
            )

            def confirm_yes(metadata):
                return True

            asyncio.run(
                delete_checkpoint(checkpoint_path, force=False, confirm_callback=confirm_yes)
            )

            # File should be deleted
            assert not checkpoint_path.exists()

    def test_delete_checkpoint_raises_error_on_oserror(self):
        """delete_checkpoint should propagate OS Error during deletion."""
        from unittest.mock import patch

        from foothold_checkpoint.core.storage import delete_checkpoint, save_checkpoint
        from tests.conftest import make_simple_campaign, make_test_config

        with tempfile.TemporaryDirectory() as tmpdir:
            source_dir = Path(tmpdir) / "source"
            source_dir.mkdir()
            checkpoint_dir = Path(tmpdir) / "checkpoints"
            checkpoint_dir.mkdir()

            (source_dir / "foothold_test.lua").write_text("-- test")

            config = make_test_config(
                campaigns={"test": make_simple_campaign("Test", ["foothold_test.lua"])}
            )

            checkpoint_path = asyncio.run(
                save_checkpoint(
                    campaign_name="test",
                    server_name="test-server",
                    source_dir=source_dir,
                    output_dir=checkpoint_dir,
                    config=config,
                )
            )

            # Mock Path.unlink to raise OSError
            with (
                patch.object(Path, "unlink", side_effect=OSError("File in use")),
                pytest.raises(OSError, match="File in use"),
            ):
                asyncio.run(delete_checkpoint(checkpoint_path, force=True))


class TestImportCheckpoint:
    """Test suite for import_checkpoint function."""

    def test_import_checkpoint_creates_checkpoint_from_directory(self):
        """import_checkpoint should create a checkpoint from files in directory."""
        from foothold_checkpoint.core.storage import import_checkpoint
        from tests.conftest import make_simple_campaign, make_test_config

        with tempfile.TemporaryDirectory() as tmpdir:
            source_dir = Path(tmpdir) / "source"
            source_dir.mkdir()
            output_dir = Path(tmpdir) / "checkpoints"
            output_dir.mkdir()

            # Create campaign files
            (source_dir / "foothold_test.lua").write_text("-- test campaign")
            (source_dir / "foothold_test_storage.csv").write_text("test,data")

            config = make_test_config(
                campaigns={
                    "test": make_simple_campaign(
                        "Test",
                        ["foothold_test.lua"],
                        storage=["foothold_test_storage.csv"],
                    )
                }
            )

            result = asyncio.run(
                import_checkpoint(
                    source_dir=source_dir,
                    campaign_name="test",
                    server_name="test-server",
                    output_dir=output_dir,
                    config=config,
                )
            )

            assert result.exists()
            assert result.parent == output_dir
            assert result.suffix == ".zip"
            assert result.name.startswith("test_")

    def test_import_checkpoint_accepts_string_paths(self):
        """import_checkpoint should accept string paths for directories."""
        from foothold_checkpoint.core.storage import import_checkpoint
        from tests.conftest import make_simple_campaign, make_test_config

        with tempfile.TemporaryDirectory() as tmpdir:
            source_dir = Path(tmpdir) / "source"
            source_dir.mkdir()
            output_dir = Path(tmpdir) / "checkpoints"
            output_dir.mkdir()

            (source_dir / "foothold_test.lua").write_text("-- test")

            config = make_test_config(
                campaigns={"test": make_simple_campaign("Test", ["foothold_test.lua"])}
            )

            result = asyncio.run(
                import_checkpoint(
                    source_dir=str(source_dir),
                    campaign_name="test",
                    server_name="test-server",
                    output_dir=str(output_dir),
                    config=config,
                )
            )

            assert result.exists()

    def test_import_checkpoint_raises_error_if_source_dir_not_exists(self):
        """import_checkpoint should raise FileNotFoundError if source directory doesn't exist."""
        from foothold_checkpoint.core.storage import import_checkpoint
        from tests.conftest import make_simple_campaign, make_test_config

        with tempfile.TemporaryDirectory() as tmpdir:
            source_dir = Path(tmpdir) / "nonexistent"
            output_dir = Path(tmpdir) / "checkpoints"
            output_dir.mkdir()

            config = make_test_config(
                campaigns={"test": make_simple_campaign("Test", ["foothold_test.lua"])}
            )

            with pytest.raises(FileNotFoundError, match="Import directory not found"):
                asyncio.run(
                    import_checkpoint(
                        source_dir=source_dir,
                        campaign_name="test",
                        server_name="test-server",
                        output_dir=output_dir,
                        config=config,
                    )
                )

    def test_import_checkpoint_raises_error_if_source_is_file(self):
        """import_checkpoint should raise ValueError if source path is a file, not directory."""
        from foothold_checkpoint.core.storage import import_checkpoint
        from tests.conftest import make_simple_campaign, make_test_config

        with tempfile.TemporaryDirectory() as tmpdir:
            source_file = Path(tmpdir) / "file.txt"
            source_file.write_text("not a directory")
            output_dir = Path(tmpdir) / "checkpoints"
            output_dir.mkdir()

            config = make_test_config(
                campaigns={"test": make_simple_campaign("Test", ["foothold_test.lua"])}
            )

            with pytest.raises(ValueError, match="Not a directory"):
                asyncio.run(
                    import_checkpoint(
                        source_dir=source_file,
                        campaign_name="test",
                        server_name="test-server",
                        output_dir=output_dir,
                        config=config,
                    )
                )

    def test_import_checkpoint_raises_error_if_no_campaign_files(self):
        """import_checkpoint should raise ValueError if no campaign files found."""
        from foothold_checkpoint.core.storage import import_checkpoint
        from tests.conftest import make_simple_campaign, make_test_config

        with tempfile.TemporaryDirectory() as tmpdir:
            source_dir = Path(tmpdir) / "source"
            source_dir.mkdir()
            output_dir = Path(tmpdir) / "checkpoints"
            output_dir.mkdir()

            # Create some non-campaign files
            (source_dir / "readme.txt").write_text("not a campaign file")

            config = make_test_config(
                campaigns={"test": make_simple_campaign("Test", ["foothold_test.lua"])}
            )

            with pytest.raises(ValueError, match="No campaign files found"):
                asyncio.run(
                    import_checkpoint(
                        source_dir=source_dir,
                        campaign_name="test",
                        server_name="test-server",
                        output_dir=output_dir,
                        config=config,
                    )
                )

    def test_import_checkpoint_detects_campaign_files_for_specified_campaign(self):
        """import_checkpoint should detect and import only files for specified campaign."""
        import zipfile

        from foothold_checkpoint.core.storage import import_checkpoint
        from tests.conftest import make_simple_campaign, make_test_config

        with tempfile.TemporaryDirectory() as tmpdir:
            source_dir = Path(tmpdir) / "source"
            source_dir.mkdir()
            output_dir = Path(tmpdir) / "checkpoints"
            output_dir.mkdir()

            # Create files for multiple campaigns
            (source_dir / "foothold_test1.lua").write_text("-- campaign 1")
            (source_dir / "foothold_test1_storage.csv").write_text("data1")
            (source_dir / "foothold_test2.lua").write_text("-- campaign 2")
            (source_dir / "foothold_test2_storage.csv").write_text("data2")

            config = make_test_config(
                campaigns={
                    "test1": make_simple_campaign(
                        "Test1",
                        ["foothold_test1.lua"],
                        storage=["foothold_test1_storage.csv"],
                    ),
                    "test2": make_simple_campaign(
                        "Test2",
                        ["foothold_test2.lua"],
                        storage=["foothold_test2_storage.csv"],
                    ),
                }
            )

            result = asyncio.run(
                import_checkpoint(
                    source_dir=source_dir,
                    campaign_name="test1",
                    server_name="test-server",
                    output_dir=output_dir,
                    config=config,
                )
            )

            # Check checkpoint contains only test1 files
            with zipfile.ZipFile(result, "r") as zf:
                files = zf.namelist()
                assert "foothold_test1.lua" in files
                assert "foothold_test1_storage.csv" in files
                assert "foothold_test2.lua" not in files
                assert "foothold_test2_storage.csv" not in files

    def test_import_checkpoint_creates_checkpoint_with_current_timestamp(self):
        """import_checkpoint should use current timestamp, not file modification dates."""
        import json
        import zipfile
        from datetime import datetime, timezone

        from foothold_checkpoint.core.storage import import_checkpoint
        from tests.conftest import make_simple_campaign, make_test_config

        with tempfile.TemporaryDirectory() as tmpdir:
            source_dir = Path(tmpdir) / "source"
            source_dir.mkdir()
            output_dir = Path(tmpdir) / "checkpoints"
            output_dir.mkdir()

            (source_dir / "foothold_test.lua").write_text("-- test")

            config = make_test_config(
                campaigns={"test": make_simple_campaign("Test", ["foothold_test.lua"])}
            )

            before_import = datetime.now(timezone.utc)
            result = asyncio.run(
                import_checkpoint(
                    source_dir=source_dir,
                    campaign_name="test",
                    server_name="test-server",
                    output_dir=output_dir,
                    config=config,
                )
            )
            after_import = datetime.now(timezone.utc)

            # Check metadata has current timestamp
            with zipfile.ZipFile(result, "r") as zf:
                metadata_content = zf.read("metadata.json")
                metadata = json.loads(metadata_content)

                created_at = datetime.fromisoformat(metadata["created_at"].replace("Z", "+00:00"))
                assert before_import <= created_at <= after_import

    def test_import_checkpoint_computes_checksums_for_all_files(self):
        """import_checkpoint should compute SHA-256 checksums for all imported files."""
        import json
        import zipfile

        from foothold_checkpoint.core.storage import import_checkpoint
        from tests.conftest import make_simple_campaign, make_test_config

        with tempfile.TemporaryDirectory() as tmpdir:
            source_dir = Path(tmpdir) / "source"
            source_dir.mkdir()
            output_dir = Path(tmpdir) / "checkpoints"
            output_dir.mkdir()

            (source_dir / "foothold_test.lua").write_text("-- test campaign")
            (source_dir / "foothold_test_storage.csv").write_text("test,data")

            config = make_test_config(
                campaigns={
                    "test": make_simple_campaign(
                        "Test",
                        ["foothold_test.lua"],
                        storage=["foothold_test_storage.csv"],
                    )
                }
            )

            result = asyncio.run(
                import_checkpoint(
                    source_dir=source_dir,
                    campaign_name="test",
                    server_name="test-server",
                    output_dir=output_dir,
                    config=config,
                )
            )

            # Check metadata has checksums
            with zipfile.ZipFile(result, "r") as zf:
                metadata_content = zf.read("metadata.json")
                metadata = json.loads(metadata_content)

                assert "files" in metadata
                assert "foothold_test.lua" in metadata["files"]
                assert "foothold_test_storage.csv" in metadata["files"]
                # Checksums should be in SHA256: format
                assert metadata["files"]["foothold_test.lua"].startswith("sha256:")
                assert metadata["files"]["foothold_test_storage.csv"].startswith("sha256:")

    def test_import_checkpoint_includes_metadata_fields(self):
        """import_checkpoint should include campaign_name, server_name, name, comment in metadata."""
        import json
        import zipfile

        from foothold_checkpoint.core.storage import import_checkpoint
        from tests.conftest import make_simple_campaign, make_test_config

        with tempfile.TemporaryDirectory() as tmpdir:
            source_dir = Path(tmpdir) / "source"
            source_dir.mkdir()
            output_dir = Path(tmpdir) / "checkpoints"
            output_dir.mkdir()

            (source_dir / "foothold_test.lua").write_text("-- test")

            config = make_test_config(
                campaigns={"test": make_simple_campaign("Test", ["foothold_test.lua"])}
            )

            result = asyncio.run(
                import_checkpoint(
                    source_dir=source_dir,
                    campaign_name="test",
                    server_name="test-server",
                    output_dir=output_dir,
                    config=config,
                    name="Imported Backup",
                    comment="Old manual backup",
                )
            )

            # Check metadata
            with zipfile.ZipFile(result, "r") as zf:
                metadata_content = zf.read("metadata.json")
                metadata = json.loads(metadata_content)

                assert metadata["campaign_name"] == "test"
                assert metadata["server_name"] == "test-server"
                assert metadata["name"] == "Imported Backup"
                assert metadata["comment"] == "Old manual backup"
                assert "created_at" in metadata

    def test_import_checkpoint_handles_optional_name_and_comment(self):
        """import_checkpoint should handle None for optional name and comment."""
        import json
        import zipfile

        from foothold_checkpoint.core.storage import import_checkpoint
        from tests.conftest import make_simple_campaign, make_test_config

        with tempfile.TemporaryDirectory() as tmpdir:
            source_dir = Path(tmpdir) / "source"
            source_dir.mkdir()
            output_dir = Path(tmpdir) / "checkpoints"
            output_dir.mkdir()

            (source_dir / "foothold_test.lua").write_text("-- test")

            config = make_test_config(
                campaigns={"test": make_simple_campaign("Test", ["foothold_test.lua"])}
            )

            result = asyncio.run(
                import_checkpoint(
                    source_dir=source_dir,
                    campaign_name="test",
                    server_name="test-server",
                    output_dir=output_dir,
                    config=config,
                )
            )

            with zipfile.ZipFile(result, "r") as zf:
                metadata_content = zf.read("metadata.json")
                metadata = json.loads(metadata_content)

                assert metadata["name"] is None
                assert metadata["comment"] is None

    def test_import_checkpoint_includes_ranks_file_if_present(self):
        """import_checkpoint should include Foothold_Ranks.lua if it exists."""
        import zipfile

        from foothold_checkpoint.core.storage import import_checkpoint
        from tests.conftest import make_simple_campaign, make_test_config

        with tempfile.TemporaryDirectory() as tmpdir:
            source_dir = Path(tmpdir) / "source"
            source_dir.mkdir()
            output_dir = Path(tmpdir) / "checkpoints"
            output_dir.mkdir()

            (source_dir / "foothold_test.lua").write_text("-- test")
            (source_dir / "Foothold_Ranks.lua").write_text("-- ranks data")

            config = make_test_config(
                campaigns={"test": make_simple_campaign("Test", ["foothold_test.lua"])}
            )

            result = asyncio.run(
                import_checkpoint(
                    source_dir=source_dir,
                    campaign_name="test",
                    server_name="test-server",
                    output_dir=output_dir,
                    config=config,
                )
            )

            with zipfile.ZipFile(result, "r") as zf:
                files = zf.namelist()
                assert "Foothold_Ranks.lua" in files

    def test_import_checkpoint_excludes_ranks_file_if_absent(self):
        """import_checkpoint should not fail if Foothold_Ranks.lua doesn't exist."""
        import zipfile

        from foothold_checkpoint.core.storage import import_checkpoint
        from tests.conftest import make_simple_campaign, make_test_config

        with tempfile.TemporaryDirectory() as tmpdir:
            source_dir = Path(tmpdir) / "source"
            source_dir.mkdir()
            output_dir = Path(tmpdir) / "checkpoints"
            output_dir.mkdir()

            (source_dir / "foothold_test.lua").write_text("-- test")

            config = make_test_config(
                campaigns={"test": make_simple_campaign("Test", ["foothold_test.lua"])}
            )

            result = asyncio.run(
                import_checkpoint(
                    source_dir=source_dir,
                    campaign_name="test",
                    server_name="test-server",
                    output_dir=output_dir,
                    config=config,
                )
            )

            with zipfile.ZipFile(result, "r") as zf:
                files = zf.namelist()
                assert "Foothold_Ranks.lua" not in files

    def test_import_checkpoint_with_ctld_files(self):
        """import_checkpoint should include all CTLD CSV files."""
        import zipfile

        from foothold_checkpoint.core.storage import import_checkpoint
        from tests.conftest import make_simple_campaign, make_test_config

        with tempfile.TemporaryDirectory() as tmpdir:
            source_dir = Path(tmpdir) / "source"
            source_dir.mkdir()
            output_dir = Path(tmpdir) / "checkpoints"
            output_dir.mkdir()

            (source_dir / "foothold_test.lua").write_text("-- test")
            (source_dir / "foothold_test_storage.csv").write_text("storage")
            (source_dir / "foothold_test_CTLD_FARPS.csv").write_text("farps")
            (source_dir / "foothold_test_CTLD_Save.csv").write_text("save")

            config = make_test_config(
                campaigns={
                    "test": make_simple_campaign(
                        "Test",
                        ["foothold_test.lua"],
                        storage=["foothold_test_storage.csv"],
                        ctld_farps=["foothold_test_CTLD_FARPS.csv"],
                        ctld_save=["foothold_test_CTLD_Save.csv"],
                    )
                }
            )

            result = asyncio.run(
                import_checkpoint(
                    source_dir=source_dir,
                    campaign_name="test",
                    server_name="test-server",
                    output_dir=output_dir,
                    config=config,
                )
            )

            with zipfile.ZipFile(result, "r") as zf:
                files = zf.namelist()
                assert "foothold_test.lua" in files
                assert "foothold_test_storage.csv" in files
                assert "foothold_test_CTLD_FARPS.csv" in files
                assert "foothold_test_CTLD_Save.csv" in files

    def test_import_checkpoint_with_version_suffixes(self):
        """import_checkpoint should handle files with version suffixes (_v0.2, _V0.1)."""
        import zipfile

        from foothold_checkpoint.core.storage import import_checkpoint
        from tests.conftest import make_simple_campaign, make_test_config

        with tempfile.TemporaryDirectory() as tmpdir:
            source_dir = Path(tmpdir) / "source"
            source_dir.mkdir()
            output_dir = Path(tmpdir) / "checkpoints"
            output_dir.mkdir()

            (source_dir / "FootHold_test_v0.2.lua").write_text("-- test")
            (source_dir / "foothold_test_storage_V0.1.csv").write_text("data")

            config = make_test_config(
                campaigns={
                    "test": make_simple_campaign(
                        "Test",
                        ["FootHold_test_v0.2.lua"],
                        storage=["foothold_test_storage_V0.1.csv"],
                    )
                }
            )

            result = asyncio.run(
                import_checkpoint(
                    source_dir=source_dir,
                    campaign_name="test",
                    server_name="test-server",
                    output_dir=output_dir,
                    config=config,
                )
            )

            with zipfile.ZipFile(result, "r") as zf:
                files = zf.namelist()
                assert "FootHold_test_v0.2.lua" in files
                assert "foothold_test_storage_V0.1.csv" in files

    def test_import_checkpoint_case_insensitive_matching(self):
        """import_checkpoint should match campaign files case-insensitively."""
        import zipfile

        from foothold_checkpoint.core.storage import import_checkpoint
        from tests.conftest import make_simple_campaign, make_test_config

        with tempfile.TemporaryDirectory() as tmpdir:
            source_dir = Path(tmpdir) / "source"
            source_dir.mkdir()
            output_dir = Path(tmpdir) / "checkpoints"
            output_dir.mkdir()

            (source_dir / "FootHold_test.lua").write_text("-- test")
            (source_dir / "FOOTHOLD_test_storage.csv").write_text("data")

            config = make_test_config(
                campaigns={
                    "test": make_simple_campaign(
                        "Test",
                        ["FootHold_test.lua"],
                        storage=["FOOTHOLD_test_storage.csv"],
                    )
                }
            )

            result = asyncio.run(
                import_checkpoint(
                    source_dir=source_dir,
                    campaign_name="test",
                    server_name="test-server",
                    output_dir=output_dir,
                    config=config,
                )
            )

            with zipfile.ZipFile(result, "r") as zf:
                files = zf.namelist()
                assert len(files) >= 3  # metadata.json + 2 campaign files

    def test_import_checkpoint_returns_warnings_for_missing_expected_files(self):
        """import_checkpoint should return list of warnings for missing expected files."""
        from foothold_checkpoint.core.storage import import_checkpoint
        from tests.conftest import make_simple_campaign, make_test_config

        with tempfile.TemporaryDirectory() as tmpdir:
            source_dir = Path(tmpdir) / "source"
            source_dir.mkdir()
            output_dir = Path(tmpdir) / "checkpoints"
            output_dir.mkdir()

            # Only .lua file, missing storage and CTLD files
            (source_dir / "foothold_test.lua").write_text("-- test")

            config = make_test_config(
                campaigns={
                    "test": make_simple_campaign(
                        "Test",
                        ["foothold_test.lua"],
                        storage=["foothold_test_storage.csv"],
                        ctld_save=["foothold_test_CTLD_Save.csv"],
                        ctld_farps=["foothold_test_CTLD_FARPS.csv"],
                    )
                }
            )

            result, warnings = asyncio.run(
                import_checkpoint(
                    source_dir=source_dir,
                    campaign_name="test",
                    server_name="test-server",
                    output_dir=output_dir,
                    return_warnings=True,
                    config=config,
                )
            )

            assert result.exists()
            assert len(warnings) > 0
            # Should have warning for missing shared ranks file
            # Note: Optional files (storage, CTLD) don't generate warnings
            warning_text = " ".join(warnings)
            assert "Foothold_Ranks.lua" in warning_text

    def test_import_checkpoint_no_warnings_for_complete_campaign(self):
        """import_checkpoint should return empty warnings list for complete campaign."""
        from foothold_checkpoint.core.storage import import_checkpoint
        from tests.conftest import make_simple_campaign, make_test_config

        with tempfile.TemporaryDirectory() as tmpdir:
            source_dir = Path(tmpdir) / "source"
            source_dir.mkdir()
            output_dir = Path(tmpdir) / "checkpoints"
            output_dir.mkdir()

            # All expected files including ranks
            (source_dir / "foothold_test.lua").write_text("-- test")
            (source_dir / "foothold_test_storage.csv").write_text("storage")
            (source_dir / "foothold_test_CTLD_FARPS.csv").write_text("farps")
            (source_dir / "foothold_test_CTLD_Save.csv").write_text("save")
            (source_dir / "Foothold_Ranks.lua").write_text("-- ranks")

            config = make_test_config(
                campaigns={"test": make_simple_campaign("Test", ["foothold_test.lua"])}
            )

            result, warnings = asyncio.run(
                import_checkpoint(
                    source_dir=source_dir,
                    campaign_name="test",
                    server_name="test-server",
                    output_dir=output_dir,
                    return_warnings=True,
                    config=config,
                )
            )

            assert result.exists()
            assert len(warnings) == 0

    def test_import_checkpoint_handles_permission_error(self):
        """import_checkpoint should raise PermissionError if source directory not readable."""
        import os
        import platform
        import stat

        from foothold_checkpoint.core.storage import import_checkpoint
        from tests.conftest import make_simple_campaign, make_test_config

        # Skip on Windows where chmod doesn't work the same way
        if platform.system() == "Windows":
            pytest.skip("Cannot test Unix permission errors on Windows")

        with tempfile.TemporaryDirectory() as tmpdir:
            source_dir = Path(tmpdir) / "source"
            source_dir.mkdir()
            output_dir = Path(tmpdir) / "checkpoints"
            output_dir.mkdir()

            (source_dir / "foothold_test.lua").write_text("-- test")

            config = make_test_config(
                campaigns={"test": make_simple_campaign("Test", ["foothold_test.lua"])}
            )

            # Make directory unreadable (Unix only)
            try:
                os.chmod(source_dir, 0o000)
                with pytest.raises(PermissionError):
                    asyncio.run(
                        import_checkpoint(
                            source_dir=source_dir,
                            campaign_name="test",
                            server_name="test-server",
                            output_dir=output_dir,
                            config=config,
                        )
                    )
            finally:
                # Restore permissions for cleanup
                with contextlib.suppress(OSError, PermissionError):
                    os.chmod(source_dir, stat.S_IRWXU)

    def test_import_checkpoint_creates_output_directory_if_not_exists(self):
        """import_checkpoint should create output directory if it doesn't exist."""
        from foothold_checkpoint.core.storage import import_checkpoint
        from tests.conftest import make_simple_campaign, make_test_config

        with tempfile.TemporaryDirectory() as tmpdir:
            source_dir = Path(tmpdir) / "source"
            source_dir.mkdir()
            output_dir = Path(tmpdir) / "checkpoints"  # Not created

            (source_dir / "foothold_test.lua").write_text("-- test")

            config = make_test_config(
                campaigns={"test": make_simple_campaign("Test", ["foothold_test.lua"])}
            )

            result = asyncio.run(
                import_checkpoint(
                    source_dir=source_dir,
                    campaign_name="test",
                    server_name="test-server",
                    output_dir=output_dir,
                    config=config,
                )
            )

            assert result.exists()
            assert output_dir.exists()
            assert output_dir.is_dir()

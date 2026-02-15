"""Tests for campaign detection module."""

from pathlib import Path


class TestSharedFileIdentification:
    """Test suite for shared file identification (Foothold_Ranks.lua)."""

    def test_is_shared_file_foothold_ranks_exact(self):
        """Should identify exact Foothold_Ranks.lua as shared."""
        from foothold_checkpoint.core.campaign import is_shared_file

        assert is_shared_file("Foothold_Ranks.lua") is True

    def test_is_shared_file_case_insensitive(self):
        """Should match Foothold_Ranks.lua case-insensitively."""
        from foothold_checkpoint.core.campaign import is_shared_file

        assert is_shared_file("foothold_ranks.lua") is True
        assert is_shared_file("FOOTHOLD_RANKS.LUA") is True
        assert is_shared_file("FooTHold_RankS.Lua") is True

    def test_is_shared_file_with_path(self):
        """Should handle Path objects and extract filename."""
        from foothold_checkpoint.core.campaign import is_shared_file

        assert is_shared_file(Path("Foothold_Ranks.lua")) is True
        assert is_shared_file(Path("/some/path/Foothold_Ranks.lua")) is True
        # Use forward slashes for cross-platform compatibility
        assert is_shared_file(Path("some/other/path/Foothold_Ranks.lua")) is True

    def test_is_shared_file_not_ranks_file(self):
        """Should not match non-ranks files."""
        from foothold_checkpoint.core.campaign import is_shared_file

        assert is_shared_file("Foothold_CA.lua") is False
        assert is_shared_file("ranks.lua") is False
        assert is_shared_file("Foothold_Ranks.txt") is False


class TestConfigBasedCampaignDetection:
    """Test suite for config-based campaign detection."""

    def test_detect_campaigns_single_complete(self):
        """Should detect a single campaign with all files."""
        from foothold_checkpoint.core.campaign import detect_campaigns
        from foothold_checkpoint.core.config import (
            CampaignConfig,
            CampaignFileList,
            CampaignFileType,
            Config,
            ServerConfig,
        )

        config = Config(
            checkpoints_dir=Path("~/.test"),
            servers={"test": ServerConfig(path=Path("D:/Test"), description="Test")},
            campaigns={
                "ca": CampaignConfig(
                    display_name="Caucasus",
                    files=CampaignFileList(
                        persistence=CampaignFileType(files=["FootHold_CA_v0.2.lua"]),
                        ctld_save=CampaignFileType(files=["FootHold_CA_CTLD_Save_Modern.csv"]),
                        ctld_farps=CampaignFileType(files=["Foothold_CA_CTLD_FARPS_Modern.csv"]),
                        storage=CampaignFileType(files=[], optional=True),
                    ),
                )
            },
        )

        files = [
            "FootHold_CA_v0.2.lua",
            "FootHold_CA_CTLD_Save_Modern.csv",
            "Foothold_CA_CTLD_FARPS_Modern.csv",
        ]

        result = detect_campaigns(files, config)

        assert "ca" in result
        assert len(result["ca"]) == 3
        assert set(result["ca"]) == set(files)

    def test_detect_campaigns_with_era_suffixes(self):
        """Should group files with era suffixes as single campaign."""
        from foothold_checkpoint.core.campaign import detect_campaigns
        from foothold_checkpoint.core.config import (
            CampaignConfig,
            CampaignFileList,
            CampaignFileType,
            Config,
            ServerConfig,
        )

        config = Config(
            checkpoints_dir=Path("~/.test"),
            servers={"test": ServerConfig(path=Path("D:/Test"), description="Test")},
            campaigns={
                "ca": CampaignConfig(
                    display_name="Caucasus",
                    files=CampaignFileList(
                        persistence=CampaignFileType(files=["FootHold_CA_v0.2.lua"]),
                        ctld_save=CampaignFileType(files=["FootHold_CA_CTLD_Save_Modern.csv"]),
                        ctld_farps=CampaignFileType(files=["Foothold_CA_CTLD_FARPS_Modern.csv"]),
                        storage=CampaignFileType(files=[], optional=True),
                    ),
                )
            },
        )

        # Original problem: these were detected as separate campaigns
        files = [
            "FootHold_CA_v0.2.lua",
            "FootHold_CA_CTLD_Save_Modern.csv",
            "Foothold_CA_CTLD_FARPS_Modern.csv",
        ]

        result = detect_campaigns(files, config)

        # Should all be grouped under 'ca', not split by era suffix
        assert len(result) == 1
        assert "ca" in result
        assert len(result["ca"]) == 3

    def test_detect_campaigns_multiple(self):
        """Should detect multiple campaigns correctly."""
        from foothold_checkpoint.core.campaign import detect_campaigns
        from foothold_checkpoint.core.config import (
            CampaignConfig,
            CampaignFileList,
            CampaignFileType,
            Config,
            ServerConfig,
        )

        config = Config(
            checkpoints_dir=Path("~/.test"),
            servers={"test": ServerConfig(path=Path("D:/Test"), description="Test")},
            campaigns={
                "ca": CampaignConfig(
                    display_name="Caucasus",
                    files=CampaignFileList(
                        persistence=CampaignFileType(files=["FootHold_CA.lua"]),
                        ctld_save=CampaignFileType(files=[], optional=True),
                        ctld_farps=CampaignFileType(files=[], optional=True),
                        storage=CampaignFileType(files=[], optional=True),
                    ),
                ),
                "afghan": CampaignConfig(
                    display_name="Afghanistan",
                    files=CampaignFileList(
                        persistence=CampaignFileType(files=["FootHold_Afghanistan.lua"]),
                        ctld_save=CampaignFileType(files=[], optional=True),
                        ctld_farps=CampaignFileType(files=[], optional=True),
                        storage=CampaignFileType(files=[], optional=True),
                    ),
                ),
            },
        )

        files = [
            "FootHold_CA.lua",
            "FootHold_Afghanistan.lua",
        ]

        result = detect_campaigns(files, config)

        assert len(result) == 2
        assert "ca" in result
        assert "afghan" in result
        assert result["ca"] == ["FootHold_CA.lua"]
        assert result["afghan"] == ["FootHold_Afghanistan.lua"]

    def test_detect_campaigns_empty_list(self):
        """Should return empty dict for empty file list."""
        from foothold_checkpoint.core.campaign import detect_campaigns
        from foothold_checkpoint.core.config import (
            CampaignConfig,
            CampaignFileList,
            CampaignFileType,
            Config,
            ServerConfig,
        )

        config = Config(
            checkpoints_dir=Path("~/.test"),
            servers={"test": ServerConfig(path=Path("D:/Test"), description="Test")},
            campaigns={
                "ca": CampaignConfig(
                    display_name="Caucasus",
                    files=CampaignFileList(
                        persistence=CampaignFileType(files=["FootHold_CA.lua"]),
                        ctld_save=CampaignFileType(files=[], optional=True),
                        ctld_farps=CampaignFileType(files=[], optional=True),
                        storage=CampaignFileType(files=[], optional=True),
                    ),
                )
            },
        )

        result = detect_campaigns([], config)
        assert result == {}

    def test_detect_campaigns_no_matches(self):
        """Should return empty dict when no files match config."""
        from foothold_checkpoint.core.campaign import detect_campaigns
        from foothold_checkpoint.core.config import (
            CampaignConfig,
            CampaignFileList,
            CampaignFileType,
            Config,
            ServerConfig,
        )

        config = Config(
            checkpoints_dir=Path("~/.test"),
            servers={"test": ServerConfig(path=Path("D:/Test"), description="Test")},
            campaigns={
                "ca": CampaignConfig(
                    display_name="Caucasus",
                    files=CampaignFileList(
                        persistence=CampaignFileType(files=["FootHold_CA.lua"]),
                        ctld_save=CampaignFileType(files=[], optional=True),
                        ctld_farps=CampaignFileType(files=[], optional=True),
                        storage=CampaignFileType(files=[], optional=True),
                    ),
                )
            },
        )

        files = ["FootHold_Syria.lua", "some_random_file.txt"]

        result = detect_campaigns(files, config)
        assert result == {}

    def test_detect_campaigns_excludes_shared_files(self):
        """Should not include Foothold_Ranks.lua in campaign-specific groups."""
        from foothold_checkpoint.core.campaign import detect_campaigns
        from foothold_checkpoint.core.config import (
            CampaignConfig,
            CampaignFileList,
            CampaignFileType,
            Config,
            ServerConfig,
        )

        config = Config(
            checkpoints_dir=Path("~/.test"),
            servers={"test": ServerConfig(path=Path("D:/Test"), description="Test")},
            campaigns={
                "ca": CampaignConfig(
                    display_name="Caucasus",
                    files=CampaignFileList(
                        persistence=CampaignFileType(files=["FootHold_CA.lua"]),
                        ctld_save=CampaignFileType(files=[], optional=True),
                        ctld_farps=CampaignFileType(files=[], optional=True),
                        storage=CampaignFileType(files=[], optional=True),
                    ),
                )
            },
        )

        files = [
            "FootHold_CA.lua",
            "Foothold_Ranks.lua",  # Shared file
        ]

        result = detect_campaigns(files, config)

        # Ranks file should not be in the campaign group
        assert "ca" in result
        assert "Foothold_Ranks.lua" not in result["ca"]
        assert result["ca"] == ["FootHold_CA.lua"]


class TestBuildFileToCampaignMap:
    """Test suite for building reverse lookup map."""

    def test_build_map_simple(self):
        """Should create correct file-to-campaign mapping."""
        from foothold_checkpoint.core.campaign import build_file_to_campaign_map
        from foothold_checkpoint.core.config import (
            CampaignConfig,
            CampaignFileList,
            CampaignFileType,
            Config,
            ServerConfig,
        )

        config = Config(
            checkpoints_dir=Path("~/.test"),
            servers={"test": ServerConfig(path=Path("D:/Test"), description="Test")},
            campaigns={
                "ca": CampaignConfig(
                    display_name="Caucasus",
                    files=CampaignFileList(
                        persistence=CampaignFileType(files=["FootHold_CA.lua"]),
                        ctld_save=CampaignFileType(files=["FootHold_CA_CTLD_Save.csv"]),
                        ctld_farps=CampaignFileType(files=[], optional=True),
                        storage=CampaignFileType(files=[], optional=True),
                    ),
                )
            },
        )

        file_map = build_file_to_campaign_map(config)

        assert file_map["FootHold_CA.lua"] == "ca"
        assert file_map["FootHold_CA_CTLD_Save.csv"] == "ca"

    def test_build_map_multiple_campaigns(self):
        """Should handle multiple campaigns correctly."""
        from foothold_checkpoint.core.campaign import build_file_to_campaign_map
        from foothold_checkpoint.core.config import (
            CampaignConfig,
            CampaignFileList,
            CampaignFileType,
            Config,
            ServerConfig,
        )

        config = Config(
            checkpoints_dir=Path("~/.test"),
            servers={"test": ServerConfig(path=Path("D:/Test"), description="Test")},
            campaigns={
                "ca": CampaignConfig(
                    display_name="Caucasus",
                    files=CampaignFileList(
                        persistence=CampaignFileType(files=["FootHold_CA.lua"]),
                        ctld_save=CampaignFileType(files=[], optional=True),
                        ctld_farps=CampaignFileType(files=[], optional=True),
                        storage=CampaignFileType(files=[], optional=True),
                    ),
                ),
                "afghan": CampaignConfig(
                    display_name="Afghanistan",
                    files=CampaignFileList(
                        persistence=CampaignFileType(files=["FootHold_Afghanistan.lua"]),
                        ctld_save=CampaignFileType(files=[], optional=True),
                        ctld_farps=CampaignFileType(files=[], optional=True),
                        storage=CampaignFileType(files=[], optional=True),
                    ),
                ),
            },
        )

        file_map = build_file_to_campaign_map(config)

        assert file_map["FootHold_CA.lua"] == "ca"
        assert file_map["FootHold_Afghanistan.lua"] == "afghan"


class TestUnknownFileDetection:
    """Test suite for unknown file detection."""

    def test_detect_unknown_files_none(self):
        """Should return empty list when all files are known."""
        from foothold_checkpoint.core.campaign import detect_unknown_files
        from foothold_checkpoint.core.config import (
            CampaignConfig,
            CampaignFileList,
            CampaignFileType,
            Config,
            ServerConfig,
        )

        config = Config(
            checkpoints_dir=Path("~/.test"),
            servers={"test": ServerConfig(path=Path("D:/Test"), description="Test")},
            campaigns={
                "ca": CampaignConfig(
                    display_name="Caucasus",
                    files=CampaignFileList(
                        persistence=CampaignFileType(files=["FootHold_CA_v0.2.lua"]),
                        ctld_save=CampaignFileType(files=["FootHold_CA_CTLD_Save_Modern.csv"]),
                        ctld_farps=CampaignFileType(files=["Foothold_CA_CTLD_FARPS_Modern.csv"]),
                        storage=CampaignFileType(files=[], optional=True),
                    ),
                )
            },
        )

        files = [
            "FootHold_CA_v0.2.lua",
            "FootHold_CA_CTLD_Save_Modern.csv",
            "Foothold_CA_CTLD_FARPS_Modern.csv",
        ]

        unknown = detect_unknown_files(files, config)
        assert unknown == []

    def test_detect_unknown_files_single(self):
        """Should detect a single unknown file."""
        from foothold_checkpoint.core.campaign import detect_unknown_files
        from foothold_checkpoint.core.config import (
            CampaignConfig,
            CampaignFileList,
            CampaignFileType,
            Config,
            ServerConfig,
        )

        config = Config(
            checkpoints_dir=Path("~/.test"),
            servers={"test": ServerConfig(path=Path("D:/Test"), description="Test")},
            campaigns={
                "ca": CampaignConfig(
                    display_name="Caucasus",
                    files=CampaignFileList(
                        persistence=CampaignFileType(files=["FootHold_CA_v0.2.lua"]),
                        ctld_save=CampaignFileType(files=[], optional=True),
                        ctld_farps=CampaignFileType(files=[], optional=True),
                        storage=CampaignFileType(files=[], optional=True),
                    ),
                )
            },
        )

        files = [
            "FootHold_CA_v0.2.lua",
            "foothold_unknown.txt",
        ]

        unknown = detect_unknown_files(files, config)
        assert unknown == ["foothold_unknown.txt"]

    def test_detect_unknown_files_multiple(self):
        """Should detect multiple unknown files."""
        from foothold_checkpoint.core.campaign import detect_unknown_files
        from foothold_checkpoint.core.config import (
            CampaignConfig,
            CampaignFileList,
            CampaignFileType,
            Config,
            ServerConfig,
        )

        config = Config(
            checkpoints_dir=Path("~/.test"),
            servers={"test": ServerConfig(path=Path("D:/Test"), description="Test")},
            campaigns={
                "ca": CampaignConfig(
                    display_name="Caucasus",
                    files=CampaignFileList(
                        persistence=CampaignFileType(files=["FootHold_CA_v0.2.lua"]),
                        ctld_save=CampaignFileType(files=[], optional=True),
                        ctld_farps=CampaignFileType(files=[], optional=True),
                        storage=CampaignFileType(files=[], optional=True),
                    ),
                )
            },
        )

        files = [
            "FootHold_CA_v0.2.lua",
            "foothold_syria.lua",
            "foothold_nevada.csv",
            "Foothold_Afghanistan.lua",
        ]

        unknown = detect_unknown_files(files, config)
        assert set(unknown) == {
            "foothold_syria.lua",
            "foothold_nevada.csv",
            "Foothold_Afghanistan.lua",
        }

    def test_format_unknown_files_error_single(self):
        """Should format error message for single unknown file."""
        from foothold_checkpoint.core.campaign import format_unknown_files_error
        from foothold_checkpoint.core.config import (
            CampaignConfig,
            CampaignFileList,
            CampaignFileType,
            Config,
            ServerConfig,
        )

        config = Config(
            checkpoints_dir=Path("~/.test"),
            servers={"test": ServerConfig(path=Path("D:/Test"), description="Test")},
            campaigns={
                "ca": CampaignConfig(
                    display_name="Caucasus",
                    files=CampaignFileList(
                        persistence=CampaignFileType(files=["FootHold_CA_v0.2.lua"]),
                        ctld_save=CampaignFileType(files=[], optional=True),
                        ctld_farps=CampaignFileType(files=[], optional=True),
                        storage=CampaignFileType(files=[], optional=True),
                    ),
                )
            },
        )

        unknown_files = ["foothold_syria.lua"]
        result = format_unknown_files_error(unknown_files, config)

        assert "Unknown campaign files detected" in result
        assert "foothold_syria.lua" in result
        assert "under 'campaigns'" in result  # Config suggestion should be present
        assert "display_name:" in result

    def test_format_unknown_files_error_multiple(self):
        """Should format error message for multiple unknown files."""
        from foothold_checkpoint.core.campaign import format_unknown_files_error
        from foothold_checkpoint.core.config import (
            CampaignConfig,
            CampaignFileList,
            CampaignFileType,
            Config,
            ServerConfig,
        )

        config = Config(
            checkpoints_dir=Path("~/.test"),
            servers={"test": ServerConfig(path=Path("D:/Test"), description="Test")},
            campaigns={
                "ca": CampaignConfig(
                    display_name="Caucasus",
                    files=CampaignFileList(
                        persistence=CampaignFileType(files=["FootHold_CA_v0.2.lua"]),
                        ctld_save=CampaignFileType(files=[], optional=True),
                        ctld_farps=CampaignFileType(files=[], optional=True),
                        storage=CampaignFileType(files=[], optional=True),
                    ),
                )
            },
        )

        unknown_files = ["foothold_syria.lua", "foothold_nevada.csv"]
        result = format_unknown_files_error(unknown_files, config)

        assert "Unknown campaign files detected" in result
        assert "foothold_syria.lua" in result
        assert "foothold_nevada.csv" in result
        assert "under 'campaigns'" in result  # Config suggestion should be present
        assert "display_name:" in result

    def test_format_unknown_files_error_includes_suggestion(self):
        """Should include configuration suggestions in error message."""
        from foothold_checkpoint.core.campaign import format_unknown_files_error
        from foothold_checkpoint.core.config import (
            CampaignConfig,
            CampaignFileList,
            CampaignFileType,
            Config,
            ServerConfig,
        )

        config = Config(
            checkpoints_dir=Path("~/.test"),
            servers={"test": ServerConfig(path=Path("D:/Test"), description="Test")},
            campaigns={
                "ca": CampaignConfig(
                    display_name="Caucasus",
                    files=CampaignFileList(
                        persistence=CampaignFileType(files=["FootHold_CA_v0.2.lua"]),
                        ctld_save=CampaignFileType(files=[], optional=True),
                        ctld_farps=CampaignFileType(files=[], optional=True),
                        storage=CampaignFileType(files=[], optional=True),
                    ),
                )
            },
        )

        unknown_files = ["FootHold_Syria_v1.0.lua"]
        result = format_unknown_files_error(unknown_files, config)

        # Should contain YAML config suggestion
        assert "under 'campaigns'" in result
        assert "display_name:" in result
        assert "files:" in result
        assert "persistence:" in result

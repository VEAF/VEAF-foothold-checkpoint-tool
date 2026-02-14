"""Tests for campaign detection module."""

from pathlib import Path


class TestFilePatternMatching:
    """Test suite for campaign file pattern matching."""

    def test_match_lua_file_lowercase(self):
        """Should match .lua files with lowercase 'foothold' prefix."""
        from foothold_checkpoint.core.campaign import is_campaign_file

        assert is_campaign_file("foothold_Afghanistan.lua") is True
        assert is_campaign_file("foothold_CA.lua") is True
        assert is_campaign_file("foothold_syria_extended.lua") is True

    def test_match_lua_file_mixed_case(self):
        """Should match .lua files with mixed case 'FootHold' prefix."""
        from foothold_checkpoint.core.campaign import is_campaign_file

        assert is_campaign_file("FootHold_Afghanistan.lua") is True
        assert is_campaign_file("FootHold_CA.lua") is True
        assert is_campaign_file("FOOTHOLD_Germany.lua") is True

    def test_match_storage_csv(self):
        """Should match _storage.csv files."""
        from foothold_checkpoint.core.campaign import is_campaign_file

        assert is_campaign_file("foothold_Afghanistan_storage.csv") is True
        assert is_campaign_file("FootHold_CA_storage.csv") is True

    def test_match_ctld_farps_csv(self):
        """Should match _CTLD_FARPS.csv files."""
        from foothold_checkpoint.core.campaign import is_campaign_file

        assert is_campaign_file("foothold_Afghanistan_CTLD_FARPS.csv") is True
        assert is_campaign_file("FootHold_CA_CTLD_FARPS.csv") is True

    def test_match_ctld_save_csv(self):
        """Should match _CTLD_Save.csv files."""
        from foothold_checkpoint.core.campaign import is_campaign_file

        assert is_campaign_file("foothold_Afghanistan_CTLD_Save.csv") is True
        assert is_campaign_file("FootHold_CA_CTLD_Save.csv") is True

    def test_match_with_version_suffix(self):
        """Should match files with version suffixes."""
        from foothold_checkpoint.core.campaign import is_campaign_file

        assert is_campaign_file("FootHold_CA_v0.2.lua") is True
        assert is_campaign_file("foothold_Afghanistan_V0.1_storage.csv") is True
        assert is_campaign_file("FootHold_Germany_0.3_CTLD_FARPS.csv") is True

    def test_ignore_status_file(self):
        """Should not match foothold.status file."""
        from foothold_checkpoint.core.campaign import is_campaign_file

        assert is_campaign_file("foothold.status") is False

    def test_ignore_non_foothold_files(self):
        """Should not match files without foothold prefix."""
        from foothold_checkpoint.core.campaign import is_campaign_file

        assert is_campaign_file("afghanistan.lua") is False
        assert is_campaign_file("campaign_data.csv") is False
        assert is_campaign_file("README.txt") is False
        assert is_campaign_file("backup.zip") is False

    def test_ignore_hidden_files(self):
        """Should not match hidden files."""
        from foothold_checkpoint.core.campaign import is_campaign_file

        assert is_campaign_file(".DS_Store") is False
        assert is_campaign_file(".gitignore") is False
        assert is_campaign_file(".foothold_config") is False

    def test_match_case_insensitive_prefix(self):
        """Pattern matching should be case-insensitive for 'foothold' prefix."""
        from foothold_checkpoint.core.campaign import is_campaign_file

        assert is_campaign_file("foothold_test.lua") is True
        assert is_campaign_file("Foothold_test.lua") is True
        assert is_campaign_file("FootHold_test.lua") is True
        assert is_campaign_file("FOOTHOLD_test.lua") is True
        assert is_campaign_file("FoOtHoLd_test.lua") is True

    def test_match_requires_underscore_after_prefix(self):
        """Should require underscore separator after 'foothold' prefix."""
        from foothold_checkpoint.core.campaign import is_campaign_file

        # Valid: has underscore
        assert is_campaign_file("foothold_campaign.lua") is True

        # Invalid: no underscore
        assert is_campaign_file("footholdcampaign.lua") is False
        assert is_campaign_file("foothold.lua") is False

    def test_match_with_path_object(self):
        """Should work with Path objects, not just strings."""
        from foothold_checkpoint.core.campaign import is_campaign_file

        assert is_campaign_file(Path("foothold_Afghanistan.lua")) is True
        assert is_campaign_file(Path("/some/path/foothold_CA.lua")) is True
        assert is_campaign_file(Path("README.txt")) is False


class TestVersionNormalization:
    """Test suite for campaign name version normalization."""

    def test_normalize_lowercase_version_suffix(self):
        """Should remove lowercase version suffix (_v0.2)."""
        from foothold_checkpoint.core.campaign import normalize_campaign_name

        assert normalize_campaign_name("FootHold_CA_v0.2.lua") == "ca"
        assert normalize_campaign_name("foothold_Afghanistan_v1.0.lua") == "afghanistan"
        assert normalize_campaign_name("FootHold_Syria_v0.5_storage.csv") == "syria"

    def test_normalize_uppercase_version_suffix(self):
        """Should remove uppercase version suffix (_V0.1)."""
        from foothold_checkpoint.core.campaign import normalize_campaign_name

        assert normalize_campaign_name("FootHold_Germany_Modern_V0.1.lua") == "germany_modern"
        assert normalize_campaign_name("foothold_CA_V2.3.lua") == "ca"
        assert normalize_campaign_name("FOOTHOLD_Caucasus_V0.9_CTLD_FARPS.csv") == "caucasus"

    def test_normalize_numeric_version_suffix(self):
        """Should remove numeric-only version suffix (_0.1)."""
        from foothold_checkpoint.core.campaign import normalize_campaign_name

        assert normalize_campaign_name("foothold_Syria_Extended_0.1.lua") == "syria_extended"
        assert normalize_campaign_name("foothold_test_1.5.lua") == "test"
        assert normalize_campaign_name("FootHold_PersianGulf_2.0_storage.csv") == "persiangulf"

    def test_normalize_no_version_suffix(self):
        """Should normalize to lowercase when no version suffix."""
        from foothold_checkpoint.core.campaign import normalize_campaign_name

        assert normalize_campaign_name("foothold_Afghanistan.lua") == "afghanistan"
        assert normalize_campaign_name("FootHold_CA.lua") == "ca"
        assert normalize_campaign_name("foothold_Syria_Extended_storage.csv") == "syria_extended"

    def test_normalize_with_file_type_suffix(self):
        """Should handle files with type suffixes (_storage, _CTLD_FARPS, _CTLD_Save)."""
        from foothold_checkpoint.core.campaign import normalize_campaign_name

        assert normalize_campaign_name("foothold_Afghanistan_storage.csv") == "afghanistan"
        assert normalize_campaign_name("FootHold_CA_v0.2_CTLD_FARPS.csv") == "ca"
        assert normalize_campaign_name("foothold_Syria_V1.0_CTLD_Save.csv") == "syria"

    def test_normalize_preserves_underscores_in_name(self):
        """Should preserve underscores within campaign names but normalize to lowercase."""
        from foothold_checkpoint.core.campaign import normalize_campaign_name

        assert normalize_campaign_name("foothold_Syria_Extended.lua") == "syria_extended"
        assert normalize_campaign_name("FootHold_Germany_Modern_v0.1.lua") == "Germany_Modern"
        assert normalize_campaign_name("foothold_Persian_Gulf_2.0.lua") == "persian_gulf"

    def test_normalize_case_insensitive_prefix(self):
        """Should work regardless of 'foothold' prefix casing."""
        from foothold_checkpoint.core.campaign import normalize_campaign_name

        assert normalize_campaign_name("foothold_test.lua") == "test"
        assert normalize_campaign_name("Foothold_test.lua") == "test"
        assert normalize_campaign_name("FootHold_test.lua") == "test"
        assert normalize_campaign_name("FOOTHOLD_test.lua") == "test"

    def test_normalize_with_path_object(self):
        """Should work with Path objects and normalize to lowercase."""
        from foothold_checkpoint.core.campaign import normalize_campaign_name

        assert normalize_campaign_name(Path("foothold_Afghanistan.lua")) == "afghanistan"
        assert normalize_campaign_name(Path("FootHold_CA_v0.2.lua")) == "ca"
        assert normalize_campaign_name(Path("/some/path/foothold_Syria_V1.0.lua")) == "syria"

    def test_normalize_multiple_version_patterns(self):
        """Should handle various version patterns correctly."""
        from foothold_checkpoint.core.campaign import normalize_campaign_name

        # Single digit versions
        assert normalize_campaign_name("foothold_test_v1.lua") == "test"
        assert normalize_campaign_name("foothold_test_V2.lua") == "test"
        assert normalize_campaign_name("foothold_test_3.lua") == "test"

        # Multi-digit versions
        assert normalize_campaign_name("foothold_test_v10.5.lua") == "test"
        assert normalize_campaign_name("foothold_test_V99.99.lua") == "test"
        assert normalize_campaign_name("foothold_test_123.456.lua") == "test"

    def test_normalize_invalid_filename_returns_empty(self):
        """Should return empty string for non-campaign files."""
        from foothold_checkpoint.core.campaign import normalize_campaign_name

        assert normalize_campaign_name("foothold.status") == ""
        assert normalize_campaign_name("README.txt") == ""
        assert normalize_campaign_name("not_a_campaign.lua") == ""
        assert normalize_campaign_name(".hidden_file") == ""


class TestFileGrouping:
    """Test suite for grouping campaign files by campaign."""

    def test_group_complete_campaign_set(self):
        """Should group all files of a complete campaign together."""
        from foothold_checkpoint.core.campaign import group_campaign_files

        files = [
            "foothold_Afghanistan.lua",
            "foothold_Afghanistan_storage.csv",
            "foothold_Afghanistan_CTLD_FARPS.csv",
            "foothold_Afghanistan_CTLD_Save.csv",
        ]

        groups = group_campaign_files(files)

        assert "afghanistan" in groups
        assert len(groups["afghanistan"]) == 4
        assert set(groups["afghanistan"]) == set(files)

    def test_group_incomplete_campaign_set(self):
        """Should group available files even if campaign is incomplete."""
        from foothold_checkpoint.core.campaign import group_campaign_files

        files = ["foothold_CA.lua", "foothold_CA_storage.csv"]

        groups = group_campaign_files(files)

        assert "ca" in groups
        assert len(groups["ca"]) == 2
        assert set(groups["ca"]) == set(files)

    def test_group_multiple_campaigns(self):
        """Should group files from multiple campaigns separately."""
        from foothold_checkpoint.core.campaign import group_campaign_files

        files = [
            "foothold_Afghanistan.lua",
            "foothold_Afghanistan_storage.csv",
            "FootHold_CA.lua",
            "FootHold_CA_CTLD_FARPS.csv",
            "foothold_Syria.lua",
        ]

        groups = group_campaign_files(files)

        assert len(groups) == 3
        assert "afghanistan" in groups
        assert "ca" in groups
        assert "syria" in groups
        assert len(groups["afghanistan"]) == 2
        assert len(groups["ca"]) == 2
        assert len(groups["syria"]) == 1

    def test_group_case_insensitive_matching(self):
        """Should group files with mixed case prefixes together."""
        from foothold_checkpoint.core.campaign import group_campaign_files

        files = [
            "foothold_Afghanistan.lua",
            "Foothold_Afghanistan_storage.csv",
            "FootHold_AFGHANISTAN_CTLD_FARPS.csv",
            "FOOTHOLD_Afghanistan_CTLD_Save.csv",
        ]

        groups = group_campaign_files(files)

        # All should be grouped under the same normalized name
        assert len(groups) == 1
        assert "afghanistan" in groups
        assert len(groups["afghanistan"]) == 4

    def test_group_with_version_suffixes(self):
        """Should group files with different version suffixes together."""
        from foothold_checkpoint.core.campaign import group_campaign_files

        files = [
            "FootHold_CA_v0.2.lua",
            "FootHold_CA_v0.2_storage.csv",
            "foothold_CA_V0.1_CTLD_FARPS.csv",  # Different version
            "FootHold_CA_0.3.lua",  # Another different version
        ]

        groups = group_campaign_files(files)

        # All should be grouped under "ca" despite different versions
        assert len(groups) == 1
        assert "ca" in groups
        assert len(groups["ca"]) == 4

    def test_group_ignores_non_campaign_files(self):
        """Should ignore files that don't match campaign patterns."""
        from foothold_checkpoint.core.campaign import group_campaign_files

        files = [
            "foothold_Afghanistan.lua",
            "foothold_Afghanistan_storage.csv",
            "foothold.status",  # Should be ignored
            "README.txt",  # Should be ignored
            ".gitignore",  # Should be ignored
        ]

        groups = group_campaign_files(files)

        assert len(groups) == 1
        assert "afghanistan" in groups
        assert len(groups["afghanistan"]) == 2

    def test_group_empty_list(self):
        """Should return empty dict for empty file list."""
        from foothold_checkpoint.core.campaign import group_campaign_files

        groups = group_campaign_files([])

        assert groups == {}

    def test_group_no_campaign_files(self):
        """Should return empty dict when no campaign files present."""
        from foothold_checkpoint.core.campaign import group_campaign_files

        files = ["foothold.status", "README.txt", "backup.zip", ".DS_Store"]

        groups = group_campaign_files(files)

        assert groups == {}

    def test_group_preserves_original_filenames(self):
        """Should preserve original filenames in groups, not normalize them."""
        from foothold_checkpoint.core.campaign import group_campaign_files

        files = ["FootHold_CA_v0.2.lua", "foothold_ca_storage.csv"]

        groups = group_campaign_files(files)

        # Filenames should be preserved as-is (but grouped by normalized lowercase key)
        assert "FootHold_CA_v0.2.lua" in groups["ca"]
        assert "foothold_ca_storage.csv" in groups["ca"]

    def test_group_with_path_objects(self):
        """Should work with Path objects."""
        from foothold_checkpoint.core.campaign import group_campaign_files

        files = [
            Path("foothold_Afghanistan.lua"),
            Path("foothold_Afghanistan_storage.csv"),
            Path("/some/path/FootHold_CA.lua"),
        ]

        groups = group_campaign_files(files)

        assert len(groups) == 2
        assert "afghanistan" in groups
        assert "ca" in groups


class TestSharedFileIdentification:
    """Test suite for identifying Foothold_Ranks.lua as a shared file."""

    def test_is_shared_file_foothold_ranks_exact(self):
        """Should identify Foothold_Ranks.lua as a shared file."""
        from foothold_checkpoint.core.campaign import is_shared_file

        assert is_shared_file("Foothold_Ranks.lua") is True

    def test_is_shared_file_case_insensitive(self):
        """Should recognize Foothold_Ranks.lua regardless of case."""
        from foothold_checkpoint.core.campaign import is_shared_file

        assert is_shared_file("Foothold_Ranks.lua") is True
        assert is_shared_file("foothold_ranks.lua") is True
        assert is_shared_file("FOOTHOLD_RANKS.LUA") is True
        assert is_shared_file("FootHold_Ranks.Lua") is True

    def test_is_shared_file_with_path(self):
        """Should work with full paths, not just filenames."""
        from foothold_checkpoint.core.campaign import is_shared_file

        assert is_shared_file(Path("Foothold_Ranks.lua")) is True
        assert is_shared_file(Path("/some/path/Foothold_Ranks.lua")) is True
        assert is_shared_file("D:/Servers/DCS/Missions/Saves/Foothold_Ranks.lua") is True

    def test_is_shared_file_not_ranks_file(self):
        """Should return False for non-ranks files."""
        from foothold_checkpoint.core.campaign import is_shared_file

        assert is_shared_file("foothold_Afghanistan.lua") is False
        assert is_shared_file("Foothold_CA_Ranks.lua") is False  # Campaign-specific ranks
        assert is_shared_file("Ranks.lua") is False
        assert is_shared_file("foothold.status") is False
        assert is_shared_file("README.txt") is False

    def test_group_excludes_shared_file(self):
        """group_campaign_files should exclude Foothold_Ranks.lua from campaign groups."""
        from foothold_checkpoint.core.campaign import group_campaign_files

        files = [
            "foothold_Afghanistan.lua",
            "foothold_Afghanistan_storage.csv",
            "Foothold_Ranks.lua",  # Should be excluded
            "FootHold_CA.lua",
        ]

        groups = group_campaign_files(files)

        # Foothold_Ranks.lua should not appear in any campaign group
        assert len(groups) == 2
        assert "afghanistan" in groups
        assert "ca" in groups
        assert "Foothold_Ranks.lua" not in groups.get("afghanistan", [])
        assert "Foothold_Ranks.lua" not in groups.get("ca", [])

    def test_group_with_only_shared_file(self):
        """group_campaign_files should return empty dict if only shared file present."""
        from foothold_checkpoint.core.campaign import group_campaign_files

        files = ["Foothold_Ranks.lua"]

        groups = group_campaign_files(files)

        assert groups == {}

    def test_group_multiple_files_including_shared(self):
        """Should handle mixed campaign files and shared file correctly."""
        from foothold_checkpoint.core.campaign import group_campaign_files

        files = [
            "foothold_Afghanistan.lua",
            "foothold_Afghanistan_storage.csv",
            "Foothold_Ranks.lua",  # Shared
            "FootHold_CA.lua",
            "foothold.status",  # Non-campaign file
            "FOOTHOLD_RANKS.LUA",  # Duplicate shared (case variation)
        ]

        groups = group_campaign_files(files)

        # Only campaign files should be grouped
        assert len(groups) == 2
        assert len(groups["afghanistan"]) == 2
        assert len(groups["ca"]) == 1
        # Shared files should not appear
        for campaign_files in groups.values():
            assert not any("ranks" in f.lower() for f in campaign_files)


class TestCampaignNameMapping:
    """Test suite for campaign name mapping using config."""

    def test_map_historical_name_to_current(self):
        """Should map historical campaign name to current name from config."""
        from pathlib import Path

        from foothold_checkpoint.core.campaign import map_campaign_name
        from foothold_checkpoint.core.config import Config, ServerConfig

        config = Config(
            checkpoints_dir=Path("~/.test"),
            servers={"test": ServerConfig(path=Path("D:/Test"), description="Test")},
            campaigns={"Germany_Modern": ["gcw_modern", "germany_modern"]},
        )

        # Historical name should map to campaign ID
        assert map_campaign_name("gcw_modern", config) == "Germany_Modern"

    def test_map_current_name_stays_same(self):
        """Should keep current campaign name as-is."""
        from pathlib import Path

        from foothold_checkpoint.core.campaign import map_campaign_name
        from foothold_checkpoint.core.config import Config, ServerConfig

        config = Config(
            checkpoints_dir=Path("~/.test"),
            servers={"test": ServerConfig(path=Path("D:/Test"), description="Test")},
            campaigns={"Germany_Modern": ["gcw_modern", "germany_modern"]},
        )

        # Current name should map to campaign ID
        assert map_campaign_name("germany_modern", config) == "Germany_Modern"

    def test_map_unknown_name_stays_unchanged(self):
        """Should return unchanged name if not in config."""
        from pathlib import Path

        from foothold_checkpoint.core.campaign import map_campaign_name
        from foothold_checkpoint.core.config import Config, ServerConfig

        config = Config(
            checkpoints_dir=Path("~/.test"),
            servers={"test": ServerConfig(path=Path("D:/Test"), description="Test")},
            campaigns={"Germany_Modern": ["gcw_modern", "germany_modern"]},
        )

        # Unknown campaign should stay as-is
        assert map_campaign_name("unknown_campaign", config) == "unknown_campaign"

    def test_map_single_name_in_config(self):
        """Should handle campaigns with only one name in config."""
        from pathlib import Path

        from foothold_checkpoint.core.campaign import map_campaign_name
        from foothold_checkpoint.core.config import Config, ServerConfig

        config = Config(
            checkpoints_dir=Path("~/.test"),
            servers={"test": ServerConfig(path=Path("D:/Test"), description="Test")},
            campaigns={"Afghanistan": ["afghanistan"]},
        )

        assert map_campaign_name("afghanistan", config) == "afghanistan"

    def test_map_multiple_historical_names(self):
        """Should map any historical name to the current (last) name."""
        from pathlib import Path

        from foothold_checkpoint.core.campaign import map_campaign_name
        from foothold_checkpoint.core.config import Config, ServerConfig

        config = Config(
            checkpoints_dir=Path("~/.test"),
            servers={"test": ServerConfig(path=Path("D:/Test"), description="Test")},
            campaigns={"Syria": ["syria_extended", "syria_modern", "syria"]},
        )

        # All historical names should map to current (last)
        assert map_campaign_name("syria_extended", config) == "syria"
        assert map_campaign_name("syria_modern", config) == "syria"
        assert map_campaign_name("syria", config) == "syria"

    def test_map_case_insensitive_matching(self):
        """Should match campaign names case-insensitively in config."""
        from pathlib import Path

        from foothold_checkpoint.core.campaign import map_campaign_name
        from foothold_checkpoint.core.config import Config, ServerConfig

        config = Config(
            checkpoints_dir=Path("~/.test"),
            servers={"test": ServerConfig(path=Path("D:/Test"), description="Test")},
            campaigns={"Germany_Modern": ["GCW_Modern", "Germany_Modern"]},
        )

        # Input is already lowercase from normalize_campaign_name
        # Config names are mixed case, should still match
        assert map_campaign_name("gcw_modern", config) == "Germany_Modern"

    def test_map_empty_config(self):
        """Should return unchanged name when config has no campaigns."""
        from pathlib import Path

        from foothold_checkpoint.core.campaign import map_campaign_name
        from foothold_checkpoint.core.config import Config, ServerConfig

        config = Config(
            checkpoints_dir=Path("~/.test"),
            servers={"test": ServerConfig(path=Path("D:/Test"), description="Test")},
            campaigns={},
        )

        assert map_campaign_name("afghanistan", config) == "afghanistan"

    def test_detect_campaigns_with_mapping(self):
        """detect_campaigns should use name mapping from config."""
        from pathlib import Path

        from foothold_checkpoint.core.campaign import detect_campaigns
        from foothold_checkpoint.core.config import Config, ServerConfig

        config = Config(
            checkpoints_dir=Path("~/.test"),
            servers={"test": ServerConfig(path=Path("D:/Test"), description="Test")},
            campaigns={"Germany_Modern": ["gcw_modern", "germany_modern"]},
        )

        files = ["FootHold_GCW_Modern.lua", "FootHold_GCW_Modern_storage.csv"]  # Historical name

        campaigns = detect_campaigns(files, config)

        # Should be grouped under current name "germany_modern", not "gcw_modern"
        assert "germany_modern" in campaigns
        assert "gcw_modern" not in campaigns
        assert len(campaigns["germany_modern"]) == 2


class TestCampaignDetectionReport:
    """Test suite for campaign detection report generation."""

    def test_report_single_campaign(self):
        """Should generate report for single campaign."""
        from pathlib import Path

        from foothold_checkpoint.core.campaign import create_campaign_report
        from foothold_checkpoint.core.config import Config, ServerConfig

        config = Config(
            checkpoints_dir=Path("~/.test"),
            servers={"test": ServerConfig(path=Path("D:/Test"), description="Test")},
            campaigns={"Afghanistan": ["afghanistan"]},
        )

        files = ["foothold_Afghanistan.lua", "foothold_Afghanistan_storage.csv"]

        report = create_campaign_report(files, config)

        assert report == {"afghanistan": 2}

    def test_report_multiple_campaigns(self):
        """Should generate report for multiple campaigns."""
        from pathlib import Path

        from foothold_checkpoint.core.campaign import create_campaign_report
        from foothold_checkpoint.core.config import Config, ServerConfig

        config = Config(
            checkpoints_dir=Path("~/.test"),
            servers={"test": ServerConfig(path=Path("D:/Test"), description="Test")},
            campaigns={"Afghanistan": ["afghanistan"], "Caucasus": ["ca"]},
        )

        files = [
            "foothold_Afghanistan.lua",
            "foothold_Afghanistan_storage.csv",
            "FootHold_CA.lua",
            "FootHold_CA_CTLD_FARPS.csv",
        ]

        report = create_campaign_report(files, config)

        assert report == {"afghanistan": 2, "ca": 2}

    def test_report_empty_list(self):
        """Should return empty report for empty file list."""
        from pathlib import Path

        from foothold_checkpoint.core.campaign import create_campaign_report
        from foothold_checkpoint.core.config import Config, ServerConfig

        config = Config(
            checkpoints_dir=Path("~/.test"),
            servers={"test": ServerConfig(path=Path("D:/Test"), description="Test")},
            campaigns={},
        )

        report = create_campaign_report([], config)

        assert report == {}

    def test_report_ignores_non_campaign_files(self):
        """Should ignore non-campaign files in report."""
        from pathlib import Path

        from foothold_checkpoint.core.campaign import create_campaign_report
        from foothold_checkpoint.core.config import Config, ServerConfig

        config = Config(
            checkpoints_dir=Path("~/.test"),
            servers={"test": ServerConfig(path=Path("D:/Test"), description="Test")},
            campaigns={"Afghanistan": ["afghanistan"]},
        )

        files = ["foothold_Afghanistan.lua", "README.txt", "foothold.status", ".hidden_file"]

        report = create_campaign_report(files, config)

        # Only the campaign file should be counted
        assert report == {"afghanistan": 1}

    def test_report_with_name_mapping(self):
        """Should use current campaign names in report."""
        from pathlib import Path

        from foothold_checkpoint.core.campaign import create_campaign_report
        from foothold_checkpoint.core.config import Config, ServerConfig

        config = Config(
            checkpoints_dir=Path("~/.test"),
            servers={"test": ServerConfig(path=Path("D:/Test"), description="Test")},
            campaigns={"Germany_Modern": ["gcw_modern", "germany_modern"]},
        )

        files = ["FootHold_GCW_Modern.lua", "FootHold_GCW_Modern_storage.csv"]  # Historical name

        report = create_campaign_report(files, config)

        # Should use current name "germany_modern", not historical "gcw_modern"
        assert report == {"germany_modern": 2}
        assert "gcw_modern" not in report

    def test_report_excludes_shared_files(self):
        """Should exclude shared files (Foothold_Ranks.lua) from report."""
        from pathlib import Path

        from foothold_checkpoint.core.campaign import create_campaign_report
        from foothold_checkpoint.core.config import Config, ServerConfig

        config = Config(
            checkpoints_dir=Path("~/.test"),
            servers={"test": ServerConfig(path=Path("D:/Test"), description="Test")},
            campaigns={"Afghanistan": ["afghanistan"]},
        )

        files = ["foothold_Afghanistan.lua", "Foothold_Ranks.lua"]  # Shared file

        report = create_campaign_report(files, config)

        # Ranks file should not be counted
        assert report == {"afghanistan": 1}

    def test_report_with_varying_file_counts(self):
        """Should correctly count different numbers of files per campaign."""
        from pathlib import Path

        from foothold_checkpoint.core.campaign import create_campaign_report
        from foothold_checkpoint.core.config import Config, ServerConfig

        config = Config(
            checkpoints_dir=Path("~/.test"),
            servers={"test": ServerConfig(path=Path("D:/Test"), description="Test")},
            campaigns={"Afghanistan": ["afghanistan"], "Caucasus": ["ca"], "Syria": ["syria"]},
        )

        files = [
            # Afghanistan: 4 files
            "foothold_Afghanistan.lua",
            "foothold_Afghanistan_storage.csv",
            "foothold_Afghanistan_CTLD_FARPS.csv",
            "foothold_Afghanistan_CTLD_Save.csv",
            # CA: 1 file
            "FootHold_CA.lua",
            # Syria: 2 files
            "foothold_Syria.lua",
            "foothold_syria_storage.csv",
        ]

        report = create_campaign_report(files, config)

        assert report == {"afghanistan": 4, "ca": 1, "syria": 2}


class TestRenameCampaignFile:
    """Test suite for campaign file renaming during restoration."""

    def test_rename_lua_file_with_evolved_name(self):
        """Should rename .lua file to use current campaign name."""
        from pathlib import Path

        from foothold_checkpoint.core.campaign import rename_campaign_file
        from foothold_checkpoint.core.config import Config, ServerConfig

        config = Config(
            checkpoints_dir=Path("~/.test"),
            servers={"test": ServerConfig(path=Path("D:/Test"), description="Test")},
            campaigns={"Germany_Modern": ["gcw_modern", "germany_modern"]},
        )

        # Historical filename should be renamed to current name
        original = "FootHold_GCW_Modern.lua"
        renamed = rename_campaign_file(original, config)

        # map_campaign_name returns lowercase by design
        assert renamed == "FootHold_Germany_Modern.lua"

    def test_rename_lua_file_with_version_suffix(self):
        """Should rename .lua file with version suffix."""
        from pathlib import Path

        from foothold_checkpoint.core.campaign import rename_campaign_file
        from foothold_checkpoint.core.config import Config, ServerConfig

        config = Config(
            checkpoints_dir=Path("~/.test"),
            servers={"test": ServerConfig(path=Path("D:/Test"), description="Test")},
            campaigns={
                # Campaign names in config should NOT include version suffixes
                "Germany_Modern": ["gcw_modern", "germany_modern"]
            },
        )

        # File has version suffix in original name
        original = "FootHold_GCW_Modern_V0.1.lua"
        renamed = rename_campaign_file(original, config)

        # Should remove version suffix and use current name
        assert renamed == "FootHold_Germany_Modern.lua"

    def test_rename_storage_csv_file(self):
        """Should rename _storage.csv file with current campaign name."""
        from pathlib import Path

        from foothold_checkpoint.core.campaign import rename_campaign_file
        from foothold_checkpoint.core.config import Config, ServerConfig

        config = Config(
            checkpoints_dir=Path("~/.test"),
            servers={"test": ServerConfig(path=Path("D:/Test"), description="Test")},
            campaigns={"Germany_Modern": ["gcw_modern", "germany_modern"]},
        )

        original = "FootHold_GCW_Modern_storage.csv"
        renamed = rename_campaign_file(original, config)

        assert renamed == "FootHold_Germany_Modern_storage.csv"

    def test_rename_ctld_farps_csv_file(self):
        """Should rename _CTLD_FARPS.csv file with current campaign name."""
        from pathlib import Path

        from foothold_checkpoint.core.campaign import rename_campaign_file
        from foothold_checkpoint.core.config import Config, ServerConfig

        config = Config(
            checkpoints_dir=Path("~/.test"),
            servers={"test": ServerConfig(path=Path("D:/Test"), description="Test")},
            campaigns={"Germany_Modern": ["gcw_modern", "germany_modern"]},
        )

        original = "FootHold_GCW_Modern_CTLD_FARPS.csv"
        renamed = rename_campaign_file(original, config)

        assert renamed == "FootHold_Germany_Modern_CTLD_FARPS.csv"

    def test_rename_ctld_save_csv_file(self):
        """Should rename _CTLD_Save.csv file with current campaign name."""
        from pathlib import Path

        from foothold_checkpoint.core.campaign import rename_campaign_file
        from foothold_checkpoint.core.config import Config, ServerConfig

        config = Config(
            checkpoints_dir=Path("~/.test"),
            servers={"test": ServerConfig(path=Path("D:/Test"), description="Test")},
            campaigns={"Germany_Modern": ["gcw_modern", "germany_modern"]},
        )

        original = "FootHold_GCW_Modern_CTLD_Save.csv"
        renamed = rename_campaign_file(original, config)

        assert renamed == "FootHold_Germany_Modern_CTLD_Save.csv"

    def test_rename_unchanged_campaign_name(self):
        """Should keep filename unchanged if campaign name hasn't evolved."""
        from pathlib import Path

        from foothold_checkpoint.core.campaign import rename_campaign_file
        from foothold_checkpoint.core.config import Config, ServerConfig

        config = Config(
            checkpoints_dir=Path("~/.test"),
            servers={"test": ServerConfig(path=Path("D:/Test"), description="Test")},
            campaigns={"Afghanistan": ["afghanistan"]},
        )

        original = "foothold_Afghanistan.lua"
        renamed = rename_campaign_file(original, config)

        # Name hasn't changed, should stay the same
        assert renamed == "foothold_Afghanistan.lua"

    def test_rename_campaign_not_in_config(self):
        """Should keep filename unchanged if campaign not found in config."""
        from pathlib import Path

        from foothold_checkpoint.core.campaign import rename_campaign_file
        from foothold_checkpoint.core.config import Config, ServerConfig

        config = Config(
            checkpoints_dir=Path("~/.test"),
            servers={"test": ServerConfig(path=Path("D:/Test"), description="Test")},
            campaigns={},
        )

        original = "foothold_unknown.lua"
        renamed = rename_campaign_file(original, config)

        # Unknown campaign, should stay unchanged
        assert renamed == "foothold_unknown.lua"

    def test_rename_non_campaign_file_unchanged(self):
        """Should keep non-campaign files unchanged."""
        from pathlib import Path

        from foothold_checkpoint.core.campaign import rename_campaign_file
        from foothold_checkpoint.core.config import Config, ServerConfig

        config = Config(
            checkpoints_dir=Path("~/.test"),
            servers={"test": ServerConfig(path=Path("D:/Test"), description="Test")},
            campaigns={"Germany_Modern": ["gcw_modern", "germany_modern"]},
        )

        # Shared file should not be renamed
        assert rename_campaign_file("Foothold_Ranks.lua", config) == "Foothold_Ranks.lua"

        # Non-campaign files should not be renamed
        assert rename_campaign_file("README.txt", config) == "README.txt"
        assert rename_campaign_file("foothold.status", config) == "foothold.status"

    def test_rename_preserves_case_prefix(self):
        """Should preserve the case of the 'foothold' prefix."""
        from pathlib import Path

        from foothold_checkpoint.core.campaign import rename_campaign_file
        from foothold_checkpoint.core.config import Config, ServerConfig

        config = Config(
            checkpoints_dir=Path("~/.test"),
            servers={"test": ServerConfig(path=Path("D:/Test"), description="Test")},
            campaigns={"Germany_Modern": ["gcw_modern", "germany_modern"]},
        )

        # Original has "FootHold" (mixed case)
        original = "FootHold_GCW_Modern.lua"
        renamed = rename_campaign_file(original, config)

        # Should preserve "FootHold" prefix, not change to "foothold"
        assert renamed.startswith("FootHold_")

    def test_rename_complex_evolution_chain(self):
        """Should handle complex campaign name evolution chains."""
        from pathlib import Path

        from foothold_checkpoint.core.campaign import rename_campaign_file
        from foothold_checkpoint.core.config import Config, ServerConfig

        config = Config(
            checkpoints_dir=Path("~/.test"),
            servers={"test": ServerConfig(path=Path("D:/Test"), description="Test")},
            campaigns={"Syria": ["syria_extended", "syria_modern", "syria"]},
        )

        # Old name → current name
        assert rename_campaign_file("foothold_syria_extended.lua", config) == "foothold_Syria.lua"
        # Middle name → current name
        assert rename_campaign_file("foothold_syria_modern.lua", config) == "foothold_Syria.lua"
        # Current name → stays same
        assert rename_campaign_file("foothold_Syria.lua", config) == "foothold_Syria.lua"

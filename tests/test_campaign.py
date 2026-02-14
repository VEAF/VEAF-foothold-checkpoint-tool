"""Tests for campaign detection module."""

import pytest
from pathlib import Path


class TestFilePatternMatching:
    """Test suite for campaign file pattern matching."""

    def test_match_lua_file_lowercase(self):
        """Should match .lua files with lowercase 'foothold' prefix."""
        from foothold_checkpoint.core.campaign import is_campaign_file

        assert is_campaign_file("foothold_afghanistan.lua") is True
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

        assert is_campaign_file("foothold_afghanistan_storage.csv") is True
        assert is_campaign_file("FootHold_CA_storage.csv") is True

    def test_match_ctld_farps_csv(self):
        """Should match _CTLD_FARPS.csv files."""
        from foothold_checkpoint.core.campaign import is_campaign_file

        assert is_campaign_file("foothold_afghanistan_CTLD_FARPS.csv") is True
        assert is_campaign_file("FootHold_CA_CTLD_FARPS.csv") is True

    def test_match_ctld_save_csv(self):
        """Should match _CTLD_Save.csv files."""
        from foothold_checkpoint.core.campaign import is_campaign_file

        assert is_campaign_file("foothold_afghanistan_CTLD_Save.csv") is True
        assert is_campaign_file("FootHold_CA_CTLD_Save.csv") is True

    def test_match_with_version_suffix(self):
        """Should match files with version suffixes."""
        from foothold_checkpoint.core.campaign import is_campaign_file

        assert is_campaign_file("FootHold_CA_v0.2.lua") is True
        assert is_campaign_file("foothold_afghanistan_V0.1_storage.csv") is True
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

        assert is_campaign_file(Path("foothold_afghanistan.lua")) is True
        assert is_campaign_file(Path("/some/path/foothold_CA.lua")) is True
        assert is_campaign_file(Path("README.txt")) is False


class TestVersionNormalization:
    """Test suite for campaign name version normalization."""

    def test_normalize_lowercase_version_suffix(self):
        """Should remove lowercase version suffix (_v0.2)."""
        from foothold_checkpoint.core.campaign import normalize_campaign_name

        assert normalize_campaign_name("FootHold_CA_v0.2.lua") == "CA"
        assert normalize_campaign_name("foothold_afghanistan_v1.0.lua") == "afghanistan"
        assert normalize_campaign_name("FootHold_Syria_v0.5_storage.csv") == "Syria"

    def test_normalize_uppercase_version_suffix(self):
        """Should remove uppercase version suffix (_V0.1)."""
        from foothold_checkpoint.core.campaign import normalize_campaign_name

        assert normalize_campaign_name("FootHold_Germany_Modern_V0.1.lua") == "Germany_Modern"
        assert normalize_campaign_name("foothold_CA_V2.3.lua") == "CA"
        assert normalize_campaign_name("FOOTHOLD_Caucasus_V0.9_CTLD_FARPS.csv") == "Caucasus"

    def test_normalize_numeric_version_suffix(self):
        """Should remove numeric-only version suffix (_0.1)."""
        from foothold_checkpoint.core.campaign import normalize_campaign_name

        assert normalize_campaign_name("foothold_Syria_Extended_0.1.lua") == "Syria_Extended"
        assert normalize_campaign_name("foothold_test_1.5.lua") == "test"
        assert normalize_campaign_name("FootHold_PersianGulf_2.0_storage.csv") == "PersianGulf"

    def test_normalize_no_version_suffix(self):
        """Should keep campaign name unchanged when no version suffix."""
        from foothold_checkpoint.core.campaign import normalize_campaign_name

        assert normalize_campaign_name("foothold_afghanistan.lua") == "afghanistan"
        assert normalize_campaign_name("FootHold_CA.lua") == "CA"
        assert normalize_campaign_name("foothold_Syria_Extended_storage.csv") == "Syria_Extended"

    def test_normalize_with_file_type_suffix(self):
        """Should handle files with type suffixes (_storage, _CTLD_FARPS, _CTLD_Save)."""
        from foothold_checkpoint.core.campaign import normalize_campaign_name

        assert normalize_campaign_name("foothold_afghanistan_storage.csv") == "afghanistan"
        assert normalize_campaign_name("FootHold_CA_v0.2_CTLD_FARPS.csv") == "CA"
        assert normalize_campaign_name("foothold_Syria_V1.0_CTLD_Save.csv") == "Syria"

    def test_normalize_preserves_underscores_in_name(self):
        """Should preserve underscores within campaign names."""
        from foothold_checkpoint.core.campaign import normalize_campaign_name

        assert normalize_campaign_name("foothold_Syria_Extended.lua") == "Syria_Extended"
        assert normalize_campaign_name("FootHold_Germany_Modern_v0.1.lua") == "Germany_Modern"
        assert normalize_campaign_name("foothold_Persian_Gulf_2.0.lua") == "Persian_Gulf"

    def test_normalize_case_insensitive_prefix(self):
        """Should work regardless of 'foothold' prefix casing."""
        from foothold_checkpoint.core.campaign import normalize_campaign_name

        assert normalize_campaign_name("foothold_test.lua") == "test"
        assert normalize_campaign_name("Foothold_test.lua") == "test"
        assert normalize_campaign_name("FootHold_test.lua") == "test"
        assert normalize_campaign_name("FOOTHOLD_test.lua") == "test"

    def test_normalize_with_path_object(self):
        """Should work with Path objects."""
        from foothold_checkpoint.core.campaign import normalize_campaign_name

        assert normalize_campaign_name(Path("foothold_afghanistan.lua")) == "afghanistan"
        assert normalize_campaign_name(Path("FootHold_CA_v0.2.lua")) == "CA"
        assert normalize_campaign_name(Path("/some/path/foothold_Syria_V1.0.lua")) == "Syria"

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

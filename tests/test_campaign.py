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

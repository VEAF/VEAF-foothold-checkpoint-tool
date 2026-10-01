"""Tests for reading foothold.status, the mission's own record of what it writes.

Foothold names its persistence file after the mission version, so every mission
update invents a filename the configuration does not know. That has already
happened four times on the VEAF servers, twice without anyone noticing: the
campaign simply stopped being captured, in silence.

The mission writes foothold.status next to its saves, holding the absolute path
of the file it is actually using, and rewrites it on every save. That makes it
the one source of truth that follows version bumps on its own.
"""

import pytest


@pytest.fixture
def saves_dir(tmp_path):
    saves = tmp_path / "Saves"
    saves.mkdir()
    return saves


def write_status(saves, lua_name):
    """Write a foothold.status in the shape the mission produces."""
    (saves / "foothold.status").write_text(
        f"C:\\Users\\veaf\\Saved Games\\srv\\Missions/Saves/{lua_name}",
        encoding="utf-8",
    )


class TestReadLivePersistenceFile:
    """The live filename is read from the mission's own status file."""

    def test_returns_the_filename_the_mission_is_writing(self, saves_dir):
        from foothold_checkpoint.core.campaign import read_live_persistence_file

        write_status(saves_dir, "FootHold_CA_v0.3.lua")

        assert read_live_persistence_file(saves_dir) == "FootHold_CA_v0.3.lua"

    def test_handles_the_mixed_separators_the_mission_writes(self, saves_dir):
        """The real file mixes backslashes and forward slashes in one path."""
        from foothold_checkpoint.core.campaign import read_live_persistence_file

        (saves_dir / "foothold.status").write_text(
            "C:\\Users\\veaf\\Saved Games\\foothold1_server\\Missions/Saves/FootHold_CA_v0.3.lua",
            encoding="utf-8",
        )

        assert read_live_persistence_file(saves_dir) == "FootHold_CA_v0.3.lua"

    def test_reads_a_syria_style_name(self, saves_dir):
        from foothold_checkpoint.core.campaign import read_live_persistence_file

        write_status(saves_dir, "footholdSyria_Extended_0.1.lua")

        assert read_live_persistence_file(saves_dir) == "footholdSyria_Extended_0.1.lua"

    def test_ignores_trailing_whitespace_and_newlines(self, saves_dir):
        from foothold_checkpoint.core.campaign import read_live_persistence_file

        (saves_dir / "foothold.status").write_text(
            "C:/Saves/FootHold_CA_v0.3.lua\r\n", encoding="utf-8"
        )

        assert read_live_persistence_file(saves_dir) == "FootHold_CA_v0.3.lua"

    def test_returns_none_when_there_is_no_status_file(self, saves_dir):
        from foothold_checkpoint.core.campaign import read_live_persistence_file

        assert read_live_persistence_file(saves_dir) is None

    def test_returns_none_for_a_missing_directory(self, tmp_path):
        from foothold_checkpoint.core.campaign import read_live_persistence_file

        assert read_live_persistence_file(tmp_path / "nope") is None

    def test_returns_none_when_the_file_is_empty(self, saves_dir):
        from foothold_checkpoint.core.campaign import read_live_persistence_file

        (saves_dir / "foothold.status").write_text("", encoding="utf-8")

        assert read_live_persistence_file(saves_dir) is None

    def test_returns_none_when_the_content_is_not_a_lua_path(self, saves_dir):
        """Defensive: the format is Foothold's, not ours, and it may change."""
        from foothold_checkpoint.core.campaign import read_live_persistence_file

        (saves_dir / "foothold.status").write_text("something else entirely", encoding="utf-8")

        assert read_live_persistence_file(saves_dir) is None

    def test_accepts_a_string_path(self, saves_dir):
        from foothold_checkpoint.core.campaign import read_live_persistence_file

        write_status(saves_dir, "FootHold_CA_v0.3.lua")

        assert read_live_persistence_file(str(saves_dir)) == "FootHold_CA_v0.3.lua"


class TestFindCampaignForLiveFile:
    """Which campaign, if any, declares the file the mission is writing."""

    @pytest.fixture
    def config(self, tmp_path):
        from tests.conftest import make_simple_campaign, make_test_config

        return make_test_config(
            checkpoints_dir=tmp_path / "cp",
            campaigns={
                "caucasus": make_simple_campaign(
                    "Caucasus", persistence_files=["FootHold_CA_v0.3.lua"]
                ),
                "syria": make_simple_campaign(
                    "Syria", persistence_files=["footholdSyria_Extended_0.1.lua"]
                ),
            },
        )

    def test_names_the_campaign_that_declares_it(self, config):
        from foothold_checkpoint.core.campaign import find_campaign_for_file

        assert find_campaign_for_file("FootHold_CA_v0.3.lua", config) == "caucasus"

    def test_returns_none_when_no_campaign_declares_it(self, config):
        from foothold_checkpoint.core.campaign import find_campaign_for_file

        assert find_campaign_for_file("FootHold_CA_v0.4.lua", config) is None

    def test_matches_a_legacy_name_too(self, tmp_path):
        from foothold_checkpoint.core.campaign import find_campaign_for_file
        from tests.conftest import make_simple_campaign, make_test_config

        config = make_test_config(
            checkpoints_dir=tmp_path / "cp",
            campaigns={
                "caucasus": make_simple_campaign(
                    "Caucasus",
                    persistence_files=["FootHold_CA_v0.3.lua", "FootHold_CA_v0.2.lua"],
                )
            },
        )

        assert find_campaign_for_file("FootHold_CA_v0.2.lua", config) == "caucasus"


class TestDetectingAnUndeclaredLiveCampaign:
    """Naming the campaign that is being played but has no checkpoint."""

    @pytest.fixture
    def config(self, tmp_path):
        from tests.conftest import make_simple_campaign, make_test_config

        return make_test_config(
            checkpoints_dir=tmp_path / "cp",
            campaigns={
                "caucasus": make_simple_campaign(
                    "Caucasus", persistence_files=["FootHold_CA_v0.3.lua"]
                )
            },
        )

    def test_names_the_live_file_when_no_campaign_declares_it(self, saves_dir, config):
        from foothold_checkpoint.core.storage import check_undeclared_live_campaign

        write_status(saves_dir, "FootHold_CA_v0.4.lua")

        assert check_undeclared_live_campaign(saves_dir, config) == "FootHold_CA_v0.4.lua"

    def test_says_nothing_when_the_live_file_is_declared(self, saves_dir, config):
        from foothold_checkpoint.core.storage import check_undeclared_live_campaign

        write_status(saves_dir, "FootHold_CA_v0.3.lua")

        assert check_undeclared_live_campaign(saves_dir, config) is None

    def test_says_nothing_without_a_status_file(self, saves_dir, config):
        """Older missions, or a server that has never run: nothing to check against."""
        from foothold_checkpoint.core.storage import check_undeclared_live_campaign

        assert check_undeclared_live_campaign(saves_dir, config) is None


class TestSavingStillWorksWhenTheLiveCampaignIsUndeclared:
    """The campaigns that ARE configured must keep being backed up.

    An earlier version of this guard refused the save outright. Because a save
    runs once per campaign, that refused *every* campaign on the server - so a
    single Foothold version bump turned one unprotected campaign into an entirely
    unprotected server. These tests pin the behaviour that replaced it.
    """

    @pytest.fixture
    def config(self, tmp_path):
        from tests.conftest import make_simple_campaign, make_test_config

        return make_test_config(
            checkpoints_dir=tmp_path / "cp",
            campaigns={
                "caucasus": make_simple_campaign(
                    "Caucasus", persistence_files=["FootHold_CA_v0.3.lua"]
                ),
                "sinai": make_simple_campaign("Sinai", persistence_files=["FootHold_SI_v0.3.lua"]),
            },
        )

    def test_other_campaigns_are_still_saved(self, saves_dir, config):
        """The regression this design exists to prevent."""
        import asyncio

        from foothold_checkpoint.core.storage import save_all_campaigns

        (saves_dir / "FootHold_CA_v0.4.lua").write_text("live, undeclared", encoding="utf-8")
        (saves_dir / "FootHold_SI_v0.3.lua").write_text("declared", encoding="utf-8")
        write_status(saves_dir, "FootHold_CA_v0.4.lua")

        saved = asyncio.run(
            save_all_campaigns(
                server_name="foothold1",
                source_dir=saves_dir,
                output_dir=config.checkpoints_dir,
                config=config,
            )
        )

        assert sorted(saved) == ["sinai"]

    def test_a_single_campaign_save_is_not_blocked(self, saves_dir, config):
        import asyncio

        from foothold_checkpoint.core.storage import save_checkpoint

        (saves_dir / "FootHold_CA_v0.4.lua").write_text("live, undeclared", encoding="utf-8")
        (saves_dir / "FootHold_SI_v0.3.lua").write_text("declared", encoding="utf-8")
        write_status(saves_dir, "FootHold_CA_v0.4.lua")

        checkpoint = asyncio.run(
            save_checkpoint(
                campaign_name="sinai",
                server_name="foothold1",
                source_dir=saves_dir,
                output_dir=config.checkpoints_dir,
                config=config,
            )
        )

        assert checkpoint.exists()


class TestTheWarningNamesRealFiles:
    """The suggested names are read from disk, never derived from the stem.

    Foothold's CSV naming is not uniform: the Cold War campaigns use
    FootHold_CA_CTLD_Save_Coldwar.csv, which stem arithmetic cannot produce.
    Inventing names would send the operator to edit a configuration with files
    that do not exist.
    """

    def test_lists_the_sibling_files_that_actually_exist(self, saves_dir):
        from foothold_checkpoint.core.storage import format_undeclared_live_campaign_warning

        (saves_dir / "FootHold_CA_v0.4.lua").write_text("x", encoding="utf-8")
        (saves_dir / "FootHold_CA_v0.4_storage.csv").write_text("x", encoding="utf-8")
        (saves_dir / "FootHold_CA_v0.4_CTLD_Save.csv").write_text("x", encoding="utf-8")

        message = format_undeclared_live_campaign_warning(
            "FootHold_CA_v0.4.lua", "foothold1", saves_dir
        )

        assert "FootHold_CA_v0.4.lua" in message
        assert "FootHold_CA_v0.4_storage.csv" in message
        assert "FootHold_CA_v0.4_CTLD_Save.csv" in message

    def test_does_not_invent_files_that_are_absent(self, saves_dir):
        from foothold_checkpoint.core.storage import format_undeclared_live_campaign_warning

        (saves_dir / "FootHold_CA_v0.4.lua").write_text("x", encoding="utf-8")

        message = format_undeclared_live_campaign_warning(
            "FootHold_CA_v0.4.lua", "foothold1", saves_dir
        )

        assert "_CTLD_FARPS.csv" not in message
        assert "_storage.csv" not in message

    def test_names_the_server_and_the_status_file(self, saves_dir):
        from foothold_checkpoint.core.campaign import STATUS_FILENAME
        from foothold_checkpoint.core.storage import format_undeclared_live_campaign_warning

        (saves_dir / "FootHold_CA_v0.4.lua").write_text("x", encoding="utf-8")

        message = format_undeclared_live_campaign_warning(
            "FootHold_CA_v0.4.lua", "foothold1", saves_dir
        )

        assert "foothold1" in message
        assert STATUS_FILENAME in message

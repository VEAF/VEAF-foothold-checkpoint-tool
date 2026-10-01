"""Tests for the guards that prevent silent save/restore failures.

These guards exist because of a real incident: a campaign's persistence file was
renamed on the server (FootHold_CA_v0.2.lua -> FootHold_CA_v0.3.lua) without the
configuration being updated. Every save silently captured nothing, and a restore
reported success while writing files the running mission no longer reads.
"""

import asyncio
import logging
from datetime import datetime, timezone

import pytest

# Timestamp shared by checkpoints that must not collide, and old enough that a
# backup taken during a test can never land on the same one-second filename.
SAME_INSTANT = datetime(2026, 4, 30, 22, 18, 58, tzinfo=timezone.utc)


@pytest.fixture
def caucasus_config(tmp_path):
    """Config declaring the OLD caucasus filenames (as the incident had it)."""
    from tests.conftest import make_simple_campaign, make_test_config

    return make_test_config(
        checkpoints_dir=tmp_path / "checkpoints",
        campaigns={
            "caucasus": make_simple_campaign(
                "Caucasus",
                persistence_files=["FootHold_CA_v0.2.lua"],
                ctld_save=["FootHold_CA_v0.2_CTLD_Save.csv"],
            )
        },
    )


@pytest.fixture
def renamed_saves_dir(tmp_path):
    """A Saves directory holding the NEW filenames the config does not know."""
    saves = tmp_path / "Saves"
    saves.mkdir()
    (saves / "FootHold_CA_v0.3.lua").write_text("campaign state", encoding="utf-8")
    (saves / "FootHold_CA_v0.3_CTLD_Save.csv").write_text("ctld", encoding="utf-8")
    return saves


@pytest.fixture
def caucasus_checkpoint(tmp_path, caucasus_config):
    """A valid caucasus checkpoint, built from the OLD filenames."""
    from foothold_checkpoint.core.storage import save_checkpoint

    old_saves = tmp_path / "old_saves"
    old_saves.mkdir()
    (old_saves / "FootHold_CA_v0.2.lua").write_text("archived state", encoding="utf-8")

    return asyncio.run(
        save_checkpoint(
            campaign_name="caucasus",
            server_name="srv",
            source_dir=old_saves,
            output_dir=caucasus_config.checkpoints_dir,
            config=caucasus_config,
            created_at=SAME_INSTANT,
        )
    )


class TestCheckUnknownCampaignFiles:
    """check_unknown_campaign_files() reports files the configuration ignores."""

    def test_reports_files_the_config_does_not_know(self, renamed_saves_dir, caucasus_config):
        from foothold_checkpoint.core.storage import check_unknown_campaign_files

        unknown = check_unknown_campaign_files(renamed_saves_dir, caucasus_config)

        assert unknown == ["FootHold_CA_v0.3.lua", "FootHold_CA_v0.3_CTLD_Save.csv"]

    def test_returns_empty_list_when_every_file_is_configured(self, tmp_path, caucasus_config):
        from foothold_checkpoint.core.storage import check_unknown_campaign_files

        saves = tmp_path / "Saves"
        saves.mkdir()
        (saves / "FootHold_CA_v0.2.lua").write_text("state", encoding="utf-8")

        assert check_unknown_campaign_files(saves, caucasus_config) == []

    def test_ignores_files_that_are_not_foothold_files(self, tmp_path, caucasus_config):
        from foothold_checkpoint.core.storage import check_unknown_campaign_files

        saves = tmp_path / "Saves"
        saves.mkdir()
        (saves / "FootHold_CA_v0.2.lua").write_text("state", encoding="utf-8")
        (saves / "mission.miz").write_text("not a campaign file", encoding="utf-8")
        (saves / "notes.txt").write_text("not a campaign file", encoding="utf-8")

        assert check_unknown_campaign_files(saves, caucasus_config) == []

    def test_ignores_the_shared_ranks_file(self, tmp_path, caucasus_config):
        from foothold_checkpoint.core.storage import check_unknown_campaign_files

        saves = tmp_path / "Saves"
        saves.mkdir()
        (saves / "Foothold_Ranks.lua").write_text("ranks", encoding="utf-8")

        assert check_unknown_campaign_files(saves, caucasus_config) == []

    def test_ignores_subdirectories(self, tmp_path, caucasus_config):
        """A directory named like a campaign file is not a campaign file."""
        from foothold_checkpoint.core.storage import check_unknown_campaign_files

        saves = tmp_path / "Saves"
        saves.mkdir()
        (saves / "FootHold_CA_v0.3_backup").mkdir()

        assert check_unknown_campaign_files(saves, caucasus_config) == []

    def test_returns_empty_list_for_a_missing_directory(self, tmp_path, caucasus_config):
        from foothold_checkpoint.core.storage import check_unknown_campaign_files

        assert check_unknown_campaign_files(tmp_path / "does-not-exist", caucasus_config) == []

    def test_returns_empty_list_when_handed_a_file(self, tmp_path, caucasus_config):
        from foothold_checkpoint.core.storage import check_unknown_campaign_files

        a_file = tmp_path / "not-a-directory.txt"
        a_file.write_text("x", encoding="utf-8")

        assert check_unknown_campaign_files(a_file, caucasus_config) == []

    def test_accepts_a_string_path(self, renamed_saves_dir, caucasus_config):
        from foothold_checkpoint.core.storage import check_unknown_campaign_files

        unknown = check_unknown_campaign_files(str(renamed_saves_dir), caucasus_config)

        assert "FootHold_CA_v0.3.lua" in unknown


class TestCheckpointsNeverOverwriteEachOther:
    """Two checkpoints of one campaign in the same second must both survive.

    Checkpoint filenames carry a one-second timestamp, and the archive used to be
    opened in truncating write mode. An auto-backup taken just before a restore
    lands in the same directory with the same naming scheme, so it could destroy
    the very checkpoint being restored.
    """

    def test_a_second_checkpoint_does_not_destroy_the_first(self, tmp_path, caucasus_config):
        from foothold_checkpoint.core.storage import save_checkpoint

        saves = tmp_path / "Saves"
        saves.mkdir()

        (saves / "FootHold_CA_v0.2.lua").write_text("first state", encoding="utf-8")
        first = asyncio.run(
            save_checkpoint(
                campaign_name="caucasus",
                server_name="srv",
                source_dir=saves,
                output_dir=caucasus_config.checkpoints_dir,
                config=caucasus_config,
                created_at=SAME_INSTANT,
            )
        )

        (saves / "FootHold_CA_v0.2.lua").write_text("second state", encoding="utf-8")
        second = asyncio.run(
            save_checkpoint(
                campaign_name="caucasus",
                server_name="srv",
                source_dir=saves,
                output_dir=caucasus_config.checkpoints_dir,
                config=caucasus_config,
                created_at=SAME_INSTANT,
            )
        )

        assert first != second, "the second checkpoint must get its own filename"
        assert first.exists(), "the first checkpoint must still be there"
        assert second.exists()

    def test_a_third_checkpoint_gets_its_own_name_too(self, tmp_path, caucasus_config):
        from foothold_checkpoint.core.storage import save_checkpoint

        saves = tmp_path / "Saves"
        saves.mkdir()
        (saves / "FootHold_CA_v0.2.lua").write_text("state", encoding="utf-8")

        paths = [
            asyncio.run(
                save_checkpoint(
                    campaign_name="caucasus",
                    server_name="srv",
                    source_dir=saves,
                    output_dir=caucasus_config.checkpoints_dir,
                    config=caucasus_config,
                    created_at=SAME_INSTANT,
                )
            )
            for _ in range(3)
        ]

        assert len({p.name for p in paths}) == 3
        assert all(p.exists() for p in paths)

    def test_both_checkpoints_keep_their_own_contents(self, tmp_path, caucasus_config):
        from foothold_checkpoint.core.storage import restore_checkpoint, save_checkpoint

        saves = tmp_path / "Saves"
        saves.mkdir()
        target = tmp_path / "target"
        target.mkdir()

        (saves / "FootHold_CA_v0.2.lua").write_text("first state", encoding="utf-8")
        first = asyncio.run(
            save_checkpoint(
                campaign_name="caucasus",
                server_name="srv",
                source_dir=saves,
                output_dir=caucasus_config.checkpoints_dir,
                config=caucasus_config,
                created_at=SAME_INSTANT,
            )
        )

        (saves / "FootHold_CA_v0.2.lua").write_text("second state", encoding="utf-8")
        asyncio.run(
            save_checkpoint(
                campaign_name="caucasus",
                server_name="srv",
                source_dir=saves,
                output_dir=caucasus_config.checkpoints_dir,
                config=caucasus_config,
                created_at=SAME_INSTANT,
            )
        )

        asyncio.run(
            restore_checkpoint(
                checkpoint_path=first,
                target_dir=target,
                config=caucasus_config,
                server_name="srv",
                auto_backup=False,
                skip_overwrite_check=True,
            )
        )

        restored = (target / "FootHold_CA_v0.2.lua").read_text(encoding="utf-8")
        assert restored == "first state", "the first checkpoint's contents must be intact"


class TestRestoreRefusesToCollapseTwoFilesIntoOne:
    """Aliased names must not silently overwrite each other on restore.

    A campaign's file list doubles as a rename history: every name in it is
    rewritten to the first one. That is right when the old file is gone, and
    destructive when both exist - the checkpoint then holds two distinct states
    that would both be written to the same target, last one winning.

    The caucasus campaign is in exactly that position: v0.2 leftovers sit beside
    the live v0.3 files on the servers.
    """

    @pytest.fixture
    def two_era_config(self, tmp_path):
        from tests.conftest import make_simple_campaign, make_test_config

        return make_test_config(
            checkpoints_dir=tmp_path / "checkpoints",
            campaigns={
                "caucasus": make_simple_campaign(
                    "Caucasus",
                    persistence_files=["FootHold_CA_v0.3.lua", "FootHold_CA_v0.2.lua"],
                )
            },
        )

    @pytest.fixture
    def two_era_checkpoint(self, tmp_path, two_era_config):
        """A checkpoint holding both eras, as a save of the real servers would."""
        from foothold_checkpoint.core.storage import save_checkpoint

        saves = tmp_path / "Saves"
        saves.mkdir()
        (saves / "FootHold_CA_v0.3.lua").write_text("live state", encoding="utf-8")
        (saves / "FootHold_CA_v0.2.lua").write_text("dead leftover", encoding="utf-8")

        return asyncio.run(
            save_checkpoint(
                campaign_name="caucasus",
                server_name="srv",
                source_dir=saves,
                output_dir=two_era_config.checkpoints_dir,
                config=two_era_config,
                created_at=SAME_INSTANT,
            )
        )

    def test_refuses_rather_than_overwriting_one_with_the_other(
        self, two_era_checkpoint, two_era_config, tmp_path
    ):
        from foothold_checkpoint.core.storage import AmbiguousRestoreError, restore_checkpoint

        target = tmp_path / "target"
        target.mkdir()

        with pytest.raises(AmbiguousRestoreError) as exc_info:
            asyncio.run(
                restore_checkpoint(
                    checkpoint_path=two_era_checkpoint,
                    target_dir=target,
                    config=two_era_config,
                    server_name="srv",
                    auto_backup=False,
                    skip_overwrite_check=True,
                )
            )

        message = str(exc_info.value)
        assert "FootHold_CA_v0.3.lua" in message
        assert "FootHold_CA_v0.2.lua" in message

    def test_writes_nothing_when_it_refuses(self, two_era_checkpoint, two_era_config, tmp_path):
        from foothold_checkpoint.core.storage import AmbiguousRestoreError, restore_checkpoint

        target = tmp_path / "target"
        target.mkdir()

        with pytest.raises(AmbiguousRestoreError):
            asyncio.run(
                restore_checkpoint(
                    checkpoint_path=two_era_checkpoint,
                    target_dir=target,
                    config=two_era_config,
                    server_name="srv",
                    auto_backup=False,
                    skip_overwrite_check=True,
                )
            )

        assert list(target.iterdir()) == [], "nothing must be written"

    def test_a_single_era_checkpoint_still_restores_and_is_renamed(self, two_era_config, tmp_path):
        """The rename itself must keep working: that is what the list is for."""
        from foothold_checkpoint.core.storage import restore_checkpoint, save_checkpoint

        legacy_saves = tmp_path / "legacy"
        legacy_saves.mkdir()
        (legacy_saves / "FootHold_CA_v0.2.lua").write_text("april state", encoding="utf-8")
        checkpoint = asyncio.run(
            save_checkpoint(
                campaign_name="caucasus",
                server_name="srv",
                source_dir=legacy_saves,
                output_dir=two_era_config.checkpoints_dir,
                config=two_era_config,
                created_at=SAME_INSTANT,
            )
        )
        target = tmp_path / "target"
        target.mkdir()

        restored = asyncio.run(
            restore_checkpoint(
                checkpoint_path=checkpoint,
                target_dir=target,
                config=two_era_config,
                server_name="srv",
                auto_backup=False,
                skip_overwrite_check=True,
            )
        )

        assert [p.name for p in restored] == ["FootHold_CA_v0.3.lua"]
        assert (target / "FootHold_CA_v0.3.lua").read_text(encoding="utf-8") == "april state"


class TestSaveAllCampaignsReportsFailures:
    """save_all_campaigns() must never discard a failure without a trace."""

    def test_logs_an_error_when_a_campaign_cannot_be_saved(self, tmp_path, caplog, monkeypatch):
        from foothold_checkpoint.core.storage import save_all_campaigns
        from tests.conftest import make_simple_campaign, make_test_config

        source = tmp_path / "Saves"
        source.mkdir()
        (source / "foothold_test.lua").write_text("state", encoding="utf-8")
        config = make_test_config(
            campaigns={"test": make_simple_campaign("Test", ["foothold_test.lua"])}
        )

        async def exploding_save(**_kwargs):
            raise OSError("disk full")

        monkeypatch.setattr("foothold_checkpoint.core.storage.save_checkpoint", exploding_save)

        with caplog.at_level(logging.ERROR, logger="foothold_checkpoint.core.storage"):
            results = asyncio.run(
                save_all_campaigns(
                    server_name="srv",
                    source_dir=source,
                    output_dir=tmp_path / "out",
                    config=config,
                )
            )

        assert results == {}
        assert "disk full" in caplog.text
        assert "test" in caplog.text

    def test_the_logged_failure_carries_a_traceback(self, tmp_path, caplog, monkeypatch):
        from foothold_checkpoint.core.storage import save_all_campaigns
        from tests.conftest import make_simple_campaign, make_test_config

        source = tmp_path / "Saves"
        source.mkdir()
        (source / "foothold_test.lua").write_text("state", encoding="utf-8")
        config = make_test_config(
            campaigns={"test": make_simple_campaign("Test", ["foothold_test.lua"])}
        )

        async def exploding_save(**_kwargs):
            raise OSError("disk full")

        monkeypatch.setattr("foothold_checkpoint.core.storage.save_checkpoint", exploding_save)

        with caplog.at_level(logging.ERROR, logger="foothold_checkpoint.core.storage"):
            asyncio.run(
                save_all_campaigns(
                    server_name="srv",
                    source_dir=source,
                    output_dir=tmp_path / "out",
                    config=config,
                )
            )

        assert any(record.exc_info for record in caplog.records), "expected a traceback"

    def test_still_raises_when_continue_on_error_is_disabled(self, tmp_path, monkeypatch):
        from foothold_checkpoint.core.storage import save_all_campaigns
        from tests.conftest import make_simple_campaign, make_test_config

        source = tmp_path / "Saves"
        source.mkdir()
        (source / "foothold_test.lua").write_text("state", encoding="utf-8")
        config = make_test_config(
            campaigns={"test": make_simple_campaign("Test", ["foothold_test.lua"])}
        )

        async def exploding_save(**_kwargs):
            raise OSError("disk full")

        monkeypatch.setattr("foothold_checkpoint.core.storage.save_checkpoint", exploding_save)

        with pytest.raises(OSError, match="disk full"):
            asyncio.run(
                save_all_campaigns(
                    server_name="srv",
                    source_dir=source,
                    output_dir=tmp_path / "out",
                    config=config,
                    continue_on_error=False,
                )
            )


class TestRestoreRefusesWhenBackupCapturedNothing:
    """A restore must not proceed when its safety net caught nothing.

    This is the exact shape of the incident: the auto-backup found no campaign
    files (because the config was stale), returned None, and the restore carried
    on and reported success.
    """

    def test_raises_when_the_auto_backup_captured_nothing(
        self, caucasus_checkpoint, renamed_saves_dir, caucasus_config
    ):
        from foothold_checkpoint.core.storage import EmptyBackupError, restore_checkpoint

        with pytest.raises(EmptyBackupError) as exc_info:
            asyncio.run(
                restore_checkpoint(
                    checkpoint_path=caucasus_checkpoint,
                    target_dir=renamed_saves_dir,
                    config=caucasus_config,
                    server_name="srv",
                    auto_backup=True,
                    skip_overwrite_check=True,
                )
            )

        message = str(exc_info.value)
        assert "FootHold_CA_v0.3.lua" in message, "the message must name the unknown files"

    def test_allows_restoring_into_an_empty_directory(
        self, caucasus_checkpoint, tmp_path, caucasus_config
    ):
        """Seeding a fresh server is legitimate: there is nothing to protect.

        The guard exists to stop a restore from overwriting state the tool cannot
        see. An empty Saves directory holds no state at all, so refusing would
        block the normal way of deploying a campaign to a new server.
        """
        from foothold_checkpoint.core.storage import restore_checkpoint

        empty_target = tmp_path / "empty_target"
        empty_target.mkdir()

        restored = asyncio.run(
            restore_checkpoint(
                checkpoint_path=caucasus_checkpoint,
                target_dir=empty_target,
                config=caucasus_config,
                server_name="srv",
                auto_backup=True,
                skip_overwrite_check=True,
            )
        )

        assert [p.name for p in restored] == ["FootHold_CA_v0.2.lua"]

    def test_allows_restoring_when_only_unrelated_files_are_present(
        self, caucasus_checkpoint, tmp_path, caucasus_config
    ):
        """Non-campaign files are not state this tool is responsible for."""
        from foothold_checkpoint.core.storage import restore_checkpoint

        target = tmp_path / "target"
        target.mkdir()
        (target / "mission.miz").write_text("a mission", encoding="utf-8")
        (target / "Foothold_Ranks.lua").write_text("ranks", encoding="utf-8")

        restored = asyncio.run(
            restore_checkpoint(
                checkpoint_path=caucasus_checkpoint,
                target_dir=target,
                config=caucasus_config,
                server_name="srv",
                auto_backup=True,
                skip_overwrite_check=True,
            )
        )

        assert [p.name for p in restored] == ["FootHold_CA_v0.2.lua"]

    def test_the_refusal_message_names_no_command_line_flag(
        self, caucasus_checkpoint, renamed_saves_dir, caucasus_config
    ):
        """The message is shown in Discord too, where CLI flags do not exist."""
        from foothold_checkpoint.core.storage import EmptyBackupError, restore_checkpoint

        with pytest.raises(EmptyBackupError) as exc_info:
            asyncio.run(
                restore_checkpoint(
                    checkpoint_path=caucasus_checkpoint,
                    target_dir=renamed_saves_dir,
                    config=caucasus_config,
                    server_name="srv",
                    auto_backup=True,
                    skip_overwrite_check=True,
                )
            )

        assert "--" not in str(exc_info.value), "no CLI flag in a message shared by both front ends"

    def test_leaves_the_target_directory_untouched_when_it_refuses(
        self, caucasus_checkpoint, renamed_saves_dir, caucasus_config
    ):
        from foothold_checkpoint.core.storage import EmptyBackupError, restore_checkpoint

        before = sorted(p.name for p in renamed_saves_dir.iterdir())

        with pytest.raises(EmptyBackupError):
            asyncio.run(
                restore_checkpoint(
                    checkpoint_path=caucasus_checkpoint,
                    target_dir=renamed_saves_dir,
                    config=caucasus_config,
                    server_name="srv",
                    auto_backup=True,
                    skip_overwrite_check=True,
                )
            )

        after = sorted(p.name for p in renamed_saves_dir.iterdir())
        assert after == before, "nothing must be written when the restore is refused"

    def test_proceeds_when_the_caller_explicitly_waives_the_backup(
        self, caucasus_checkpoint, renamed_saves_dir, caucasus_config
    ):
        from foothold_checkpoint.core.storage import restore_checkpoint

        restored = asyncio.run(
            restore_checkpoint(
                checkpoint_path=caucasus_checkpoint,
                target_dir=renamed_saves_dir,
                config=caucasus_config,
                server_name="srv",
                auto_backup=True,
                require_backup=False,
                skip_overwrite_check=True,
            )
        )

        assert [p.name for p in restored] == ["FootHold_CA_v0.2.lua"]

    def test_does_not_interfere_when_the_backup_succeeds(
        self, caucasus_checkpoint, tmp_path, caucasus_config
    ):
        from foothold_checkpoint.core.storage import restore_checkpoint

        target = tmp_path / "good_saves"
        target.mkdir()
        (target / "FootHold_CA_v0.2.lua").write_text("current state", encoding="utf-8")

        restored = asyncio.run(
            restore_checkpoint(
                checkpoint_path=caucasus_checkpoint,
                target_dir=target,
                config=caucasus_config,
                server_name="srv",
                auto_backup=True,
                skip_overwrite_check=True,
            )
        )

        assert [p.name for p in restored] == ["FootHold_CA_v0.2.lua"]
        assert (target / "FootHold_CA_v0.2.lua").read_text(encoding="utf-8") == "archived state"

    def test_does_not_apply_when_auto_backup_is_disabled(
        self, caucasus_checkpoint, renamed_saves_dir, caucasus_config
    ):
        from foothold_checkpoint.core.storage import restore_checkpoint

        restored = asyncio.run(
            restore_checkpoint(
                checkpoint_path=caucasus_checkpoint,
                target_dir=renamed_saves_dir,
                config=caucasus_config,
                server_name="srv",
                auto_backup=False,
                skip_overwrite_check=True,
            )
        )

        assert [p.name for p in restored] == ["FootHold_CA_v0.2.lua"]

    def test_does_not_apply_when_no_config_is_given(self, caucasus_checkpoint, renamed_saves_dir):
        """Without a config there is no auto-backup to require in the first place."""
        from foothold_checkpoint.core.storage import restore_checkpoint

        restored = asyncio.run(
            restore_checkpoint(
                checkpoint_path=caucasus_checkpoint,
                target_dir=renamed_saves_dir,
                auto_backup=True,
                skip_overwrite_check=True,
            )
        )

        assert [p.name for p in restored] == ["FootHold_CA_v0.2.lua"]

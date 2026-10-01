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

from foothold_checkpoint.core.storage import (
    EmptyBackupError,
    check_unknown_campaign_files,
    restore_checkpoint,
    save_all_campaigns,
    save_checkpoint,
)
from tests.conftest import make_simple_campaign, make_test_config


@pytest.fixture
def caucasus_config(tmp_path):
    """Config declaring the OLD caucasus filenames (as the incident had it)."""
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
    """A valid caucasus checkpoint, built from the OLD filenames.

    Dated in the past so that the auto-backup taken during a restore cannot land
    on the same timestamped filename.
    """
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
            created_at=datetime(2026, 4, 30, 22, 18, 58, tzinfo=timezone.utc),
        )
    )


class TestCheckUnknownCampaignFiles:
    """check_unknown_campaign_files() reports files the configuration ignores."""

    def test_reports_files_the_config_does_not_know(self, renamed_saves_dir, caucasus_config):
        unknown = check_unknown_campaign_files(renamed_saves_dir, caucasus_config)

        assert unknown == ["FootHold_CA_v0.3.lua", "FootHold_CA_v0.3_CTLD_Save.csv"]

    def test_returns_empty_list_when_every_file_is_configured(self, tmp_path, caucasus_config):
        saves = tmp_path / "Saves"
        saves.mkdir()
        (saves / "FootHold_CA_v0.2.lua").write_text("state", encoding="utf-8")

        assert check_unknown_campaign_files(saves, caucasus_config) == []

    def test_ignores_files_that_are_not_foothold_files(self, tmp_path, caucasus_config):
        saves = tmp_path / "Saves"
        saves.mkdir()
        (saves / "FootHold_CA_v0.2.lua").write_text("state", encoding="utf-8")
        (saves / "mission.miz").write_text("not a campaign file", encoding="utf-8")
        (saves / "notes.txt").write_text("not a campaign file", encoding="utf-8")

        assert check_unknown_campaign_files(saves, caucasus_config) == []

    def test_ignores_the_shared_ranks_file(self, tmp_path, caucasus_config):
        saves = tmp_path / "Saves"
        saves.mkdir()
        (saves / "Foothold_Ranks.lua").write_text("ranks", encoding="utf-8")

        assert check_unknown_campaign_files(saves, caucasus_config) == []

    def test_returns_empty_list_for_a_missing_directory(self, tmp_path, caucasus_config):
        assert check_unknown_campaign_files(tmp_path / "does-not-exist", caucasus_config) == []

    def test_accepts_a_string_path(self, renamed_saves_dir, caucasus_config):
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
        saves = tmp_path / "Saves"
        saves.mkdir()
        same_instant = datetime(2026, 4, 30, 22, 18, 58, tzinfo=timezone.utc)

        (saves / "FootHold_CA_v0.2.lua").write_text("first state", encoding="utf-8")
        first = asyncio.run(
            save_checkpoint(
                campaign_name="caucasus",
                server_name="srv",
                source_dir=saves,
                output_dir=caucasus_config.checkpoints_dir,
                config=caucasus_config,
                created_at=same_instant,
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
                created_at=same_instant,
            )
        )

        assert first != second, "the second checkpoint must get its own filename"
        assert first.exists(), "the first checkpoint must still be there"
        assert second.exists()

    def test_both_checkpoints_keep_their_own_contents(self, tmp_path, caucasus_config):
        saves = tmp_path / "Saves"
        saves.mkdir()
        same_instant = datetime(2026, 4, 30, 22, 18, 58, tzinfo=timezone.utc)
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
                created_at=same_instant,
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
                created_at=same_instant,
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


class TestSaveAllCampaignsReportsFailures:
    """save_all_campaigns() must never discard a failure without a trace."""

    def test_logs_an_error_when_a_campaign_cannot_be_saved(self, tmp_path, caplog, monkeypatch):
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

    def test_still_raises_when_continue_on_error_is_disabled(self, tmp_path, monkeypatch):
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

    def test_leaves_the_target_directory_untouched_when_it_refuses(
        self, caucasus_checkpoint, renamed_saves_dir, caucasus_config
    ):
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

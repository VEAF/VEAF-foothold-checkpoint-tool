"""Tests for the operational trace left by save and restore.

The incident that prompted these tests was impossible to diagnose from the bot's
log: it recorded the campaign, the user and the checkpoint, but neither the
target server nor the directory the files actually landed in.
"""

import asyncio
import logging
from datetime import datetime, timezone

import pytest

from foothold_checkpoint.core.storage import restore_checkpoint, save_checkpoint
from tests.conftest import make_simple_campaign, make_test_config

STORAGE_LOGGER = "foothold_checkpoint.core.storage"


@pytest.fixture
def config(tmp_path):
    """Config whose canonical caucasus name is v0.2, with v0.1 accepted as legacy."""
    return make_test_config(
        checkpoints_dir=tmp_path / "checkpoints",
        campaigns={
            "caucasus": make_simple_campaign(
                "Caucasus",
                persistence_files=["FootHold_CA_v0.2.lua", "FootHold_CA_v0.1.lua"],
            )
        },
    )


@pytest.fixture
def saves_dir(tmp_path):
    saves = tmp_path / "Saves"
    saves.mkdir()
    (saves / "FootHold_CA_v0.2.lua").write_text("state", encoding="utf-8")
    return saves


@pytest.fixture
def checkpoint(config, saves_dir):
    return asyncio.run(
        save_checkpoint(
            campaign_name="caucasus",
            server_name="foothold1",
            source_dir=saves_dir,
            output_dir=config.checkpoints_dir,
            config=config,
            created_at=datetime(2026, 4, 30, 22, 18, 58, tzinfo=timezone.utc),
        )
    )


class TestSaveLeavesATrace:
    """A save records what it took, from where, and for which server."""

    def test_logs_the_campaign_server_and_source_directory(self, config, saves_dir, caplog):
        with caplog.at_level(logging.INFO, logger=STORAGE_LOGGER):
            asyncio.run(
                save_checkpoint(
                    campaign_name="caucasus",
                    server_name="foothold1",
                    source_dir=saves_dir,
                    output_dir=config.checkpoints_dir,
                    config=config,
                )
            )

        assert "caucasus" in caplog.text
        assert "foothold1" in caplog.text
        assert str(saves_dir) in caplog.text

    def test_logs_the_checkpoint_it_produced(self, config, saves_dir, caplog):
        with caplog.at_level(logging.INFO, logger=STORAGE_LOGGER):
            checkpoint = asyncio.run(
                save_checkpoint(
                    campaign_name="caucasus",
                    server_name="foothold1",
                    source_dir=saves_dir,
                    output_dir=config.checkpoints_dir,
                    config=config,
                )
            )

        assert checkpoint.name in caplog.text

    def test_logs_a_failure_with_its_traceback(self, config, tmp_path, caplog):
        empty = tmp_path / "empty"
        empty.mkdir()

        with (
            caplog.at_level(logging.ERROR, logger=STORAGE_LOGGER),
            pytest.raises(ValueError),
        ):
            asyncio.run(
                save_checkpoint(
                    campaign_name="caucasus",
                    server_name="foothold1",
                    source_dir=empty,
                    output_dir=config.checkpoints_dir,
                    config=config,
                )
            )

        assert any(record.exc_info for record in caplog.records), "expected a traceback"
        assert "caucasus" in caplog.text


class TestRestoreLeavesATrace:
    """A restore records where the files actually went."""

    def test_logs_the_server_and_target_directory(self, checkpoint, config, tmp_path, caplog):
        target = tmp_path / "target"
        target.mkdir()

        with caplog.at_level(logging.INFO, logger=STORAGE_LOGGER):
            asyncio.run(
                restore_checkpoint(
                    checkpoint_path=checkpoint,
                    target_dir=target,
                    config=config,
                    server_name="foothold1",
                    auto_backup=False,
                    skip_overwrite_check=True,
                )
            )

        assert "foothold1" in caplog.text, "the target server must be recorded"
        assert str(target) in caplog.text, "the target directory must be recorded"

    def test_logs_the_checkpoint_being_restored(self, checkpoint, config, tmp_path, caplog):
        target = tmp_path / "target"
        target.mkdir()

        with caplog.at_level(logging.INFO, logger=STORAGE_LOGGER):
            asyncio.run(
                restore_checkpoint(
                    checkpoint_path=checkpoint,
                    target_dir=target,
                    config=config,
                    server_name="foothold1",
                    auto_backup=False,
                    skip_overwrite_check=True,
                )
            )

        assert checkpoint.name in caplog.text

    def test_logs_when_a_file_is_written_under_a_different_name(
        self, config, tmp_path, saves_dir, caplog
    ):
        """Canonical renaming is a silent decision; it has to be visible."""
        legacy_saves = tmp_path / "legacy"
        legacy_saves.mkdir()
        (legacy_saves / "FootHold_CA_v0.1.lua").write_text("old state", encoding="utf-8")
        legacy_checkpoint = asyncio.run(
            save_checkpoint(
                campaign_name="caucasus",
                server_name="foothold1",
                source_dir=legacy_saves,
                output_dir=config.checkpoints_dir,
                config=config,
            )
        )
        target = tmp_path / "target"
        target.mkdir()

        with caplog.at_level(logging.INFO, logger=STORAGE_LOGGER):
            asyncio.run(
                restore_checkpoint(
                    checkpoint_path=legacy_checkpoint,
                    target_dir=target,
                    config=config,
                    server_name="foothold1",
                    auto_backup=False,
                    skip_overwrite_check=True,
                )
            )

        assert "FootHold_CA_v0.1.lua" in caplog.text
        assert "FootHold_CA_v0.2.lua" in caplog.text

    def test_logs_a_failure_with_its_traceback(self, config, tmp_path, caplog):
        missing = tmp_path / "nope.zip"
        target = tmp_path / "target"
        target.mkdir()

        with (
            caplog.at_level(logging.ERROR, logger=STORAGE_LOGGER),
            pytest.raises(FileNotFoundError),
        ):
            asyncio.run(
                restore_checkpoint(
                    checkpoint_path=missing,
                    target_dir=target,
                    config=config,
                    server_name="foothold1",
                    auto_backup=False,
                )
            )

        assert any(record.exc_info for record in caplog.records), "expected a traceback"

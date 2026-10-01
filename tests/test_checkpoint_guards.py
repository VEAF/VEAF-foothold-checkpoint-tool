"""Tests for checkpoint creation safety and traceability.

create_checkpoint is the one function both front ends go through: the plugin
reaches it via save_checkpoint, the CLI calls it directly. Anything that has to
hold for every checkpoint belongs here rather than one layer up.
"""

import logging
from datetime import datetime, timezone

import pytest

CHECKPOINT_LOGGER = "foothold_checkpoint.core.checkpoint"
SAME_INSTANT = datetime(2026, 4, 30, 22, 18, 58, tzinfo=timezone.utc)


@pytest.fixture
def campaign_file(tmp_path):
    saves = tmp_path / "Saves"
    saves.mkdir()
    lua = saves / "FootHold_CA_v0.2.lua"
    lua.write_text("campaign state", encoding="utf-8")
    return lua


class TestCheckpointsAreCreatedExclusively:
    """Resolving a free name and opening the archive must not be two decisions.

    The name carries a one-second timestamp, so a scheduled save and a restore's
    automatic backup can resolve the same free name in the same instant. If the
    archive is then opened in truncating mode, the second one destroys the first.
    """

    def test_does_not_truncate_a_file_that_appeared_after_the_name_was_chosen(
        self, tmp_path, campaign_file, monkeypatch
    ):
        from foothold_checkpoint.core import checkpoint as checkpoint_module

        output_dir = tmp_path / "checkpoints"
        output_dir.mkdir()
        taken = output_dir / "caucasus_2026-04-30_22-18-58.zip"

        real_resolve = checkpoint_module.resolve_free_checkpoint_path
        calls = {"n": 0}

        def race(output_dir, filename):
            """Let another process grab the first name we pick, once."""
            calls["n"] += 1
            if calls["n"] == 1:
                taken.write_text("another process got here first", encoding="utf-8")
                return taken
            return real_resolve(output_dir, filename)

        monkeypatch.setattr(checkpoint_module, "resolve_free_checkpoint_path", race)

        result = checkpoint_module.create_checkpoint(
            campaign_name="caucasus",
            server_name="srv",
            campaign_files=[campaign_file],
            output_dir=output_dir,
            created_at=SAME_INSTANT,
        )

        assert result != taken, "must not write over a file that appeared meanwhile"
        assert taken.read_text(encoding="utf-8") == "another process got here first"
        assert result.exists()

    def test_gives_up_rather_than_spinning_when_it_keeps_losing_the_race(
        self, tmp_path, campaign_file, monkeypatch
    ):
        """Losing every attempt must end, not loop forever."""
        from foothold_checkpoint.core import checkpoint as checkpoint_module

        output_dir = tmp_path / "checkpoints"
        output_dir.mkdir()
        always_taken = output_dir / "always.zip"

        def always_lose(_output_dir, _filename):
            always_taken.write_text("lost again", encoding="utf-8")
            return always_taken

        monkeypatch.setattr(checkpoint_module, "resolve_free_checkpoint_path", always_lose)

        with pytest.raises(FileExistsError):
            checkpoint_module.create_checkpoint(
                campaign_name="caucasus",
                server_name="srv",
                campaign_files=[campaign_file],
                output_dir=output_dir,
                created_at=SAME_INSTANT,
            )


class TestResolveFreeCheckpointPath:
    """The name resolver skips names already on disk."""

    def test_returns_the_plain_name_when_it_is_free(self, tmp_path):
        from foothold_checkpoint.core.checkpoint import resolve_free_checkpoint_path

        assert resolve_free_checkpoint_path(tmp_path, "ca.zip") == tmp_path / "ca.zip"

    def test_adds_a_suffix_when_the_name_is_taken(self, tmp_path):
        from foothold_checkpoint.core.checkpoint import resolve_free_checkpoint_path

        (tmp_path / "ca.zip").write_text("x", encoding="utf-8")

        assert resolve_free_checkpoint_path(tmp_path, "ca.zip") == tmp_path / "ca_2.zip"

    def test_keeps_counting_while_names_are_taken(self, tmp_path):
        from foothold_checkpoint.core.checkpoint import resolve_free_checkpoint_path

        (tmp_path / "ca.zip").write_text("x", encoding="utf-8")
        (tmp_path / "ca_2.zip").write_text("x", encoding="utf-8")

        assert resolve_free_checkpoint_path(tmp_path, "ca.zip") == tmp_path / "ca_3.zip"


class TestCheckpointCreationIsLogged:
    """A CLI save must leave the same trace as a plugin save.

    The CLI calls create_checkpoint directly rather than going through
    save_checkpoint, so logging only in the latter would record half the saves.
    """

    def test_logs_the_campaign_the_server_and_the_result(self, tmp_path, campaign_file, caplog):
        from foothold_checkpoint.core.checkpoint import create_checkpoint

        output_dir = tmp_path / "checkpoints"

        with caplog.at_level(logging.INFO, logger=CHECKPOINT_LOGGER):
            result = create_checkpoint(
                campaign_name="caucasus",
                server_name="foothold1",
                campaign_files=[campaign_file],
                output_dir=output_dir,
                created_at=SAME_INSTANT,
            )

        assert "caucasus" in caplog.text
        assert "foothold1" in caplog.text
        assert result.name in caplog.text

    def test_logs_when_a_name_collision_forced_a_different_filename(
        self, tmp_path, campaign_file, caplog
    ):
        from foothold_checkpoint.core.checkpoint import create_checkpoint

        output_dir = tmp_path / "checkpoints"
        output_dir.mkdir()
        (output_dir / "caucasus_2026-04-30_22-18-58.zip").write_text("taken", encoding="utf-8")

        with caplog.at_level(logging.WARNING, logger=CHECKPOINT_LOGGER):
            create_checkpoint(
                campaign_name="caucasus",
                server_name="foothold1",
                campaign_files=[campaign_file],
                output_dir=output_dir,
                created_at=SAME_INSTANT,
            )

        assert "caucasus_2026-04-30_22-18-58.zip" in caplog.text

"""Tests for the Discord plugin command helpers.

The plugin half of the product had no automated verification at all: it cannot
be imported from the repository (it expects DCSServerBot's own modules and the
flattened layout produced by scripts/build_plugin.py), mypy is configured to
ignore its errors, and discord.py is an optional group. That is also exactly
where the incident happened.

These tests close the cheapest part of that gap: they stand up the three host
symbols the plugin needs, import it, and exercise the pure helpers. Anything
touching Discord interactions stays out of reach and is deliberately not
pretended to be covered here.
"""

import sys
import types
from pathlib import Path

import pytest

pytest.importorskip("discord", reason="plugin dependency group is optional")


@pytest.fixture(scope="module")
def plugin_commands():
    """Import the plugin module with its DCSServerBot host stubbed out."""
    import foothold_checkpoint.core as real_core
    import foothold_checkpoint.core.campaign
    import foothold_checkpoint.core.config
    import foothold_checkpoint.core.events
    import foothold_checkpoint.core.storage

    added: list[str] = []

    def install(name, module):
        if name not in sys.modules:
            sys.modules[name] = module
            added.append(name)

    # DCSServerBot supplies these at runtime.
    host_core = types.ModuleType("core")

    class _Plugin:
        """Stand-in for DCSServerBot's generic Plugin base class."""

        def __class_getitem__(cls, _item):
            return cls

    class _EventListener:
        """Stand-in for DCSServerBot's EventListener base class."""

        def __class_getitem__(cls, _item):
            return cls

    host_core.Plugin = _Plugin
    host_core.EventListener = _EventListener
    install("core", host_core)

    services = types.ModuleType("services")
    services_bot = types.ModuleType("services.bot")
    services_bot.DCSServerBot = type("DCSServerBot", (), {})
    services.bot = services_bot
    install("services", services)
    install("services.bot", services_bot)

    # build_plugin.py flattens core/ inside the plugin package; mirror that so
    # the plugin's `from .core.x import y` imports resolve.
    for suffix, module in [
        ("", real_core),
        (".campaign", foothold_checkpoint.core.campaign),
        (".config", foothold_checkpoint.core.config),
        (".events", foothold_checkpoint.core.events),
        (".storage", foothold_checkpoint.core.storage),
    ]:
        install(f"foothold_checkpoint.plugin.core{suffix}", module)

    from foothold_checkpoint.plugin import commands

    yield commands

    for name in added:
        del sys.modules[name]


class TestPluginImports:
    """The module must at least load: nothing else checks it."""

    def test_the_plugin_module_imports(self, plugin_commands):
        assert plugin_commands.FootholdCheckpoint is not None

    def test_it_uses_the_shared_guard_from_core(self, plugin_commands):
        from foothold_checkpoint.core.storage import check_unknown_campaign_files

        assert plugin_commands.check_unknown_campaign_files is check_unknown_campaign_files

    def test_it_handles_the_empty_backup_error_from_core(self, plugin_commands):
        from foothold_checkpoint.core.storage import EmptyBackupError

        assert plugin_commands.EmptyBackupError is EmptyBackupError


class TestFindCampaign:
    """Campaign names in checkpoint metadata outlive the config they came from."""

    @pytest.fixture
    def plugin(self, plugin_commands):
        plugin = object.__new__(plugin_commands.FootholdCheckpoint)
        plugin.campaigns = {"caucasus": object(), "germany_modern": object()}
        return plugin

    def test_finds_an_exact_match(self, plugin):
        assert plugin._find_campaign("caucasus") == "caucasus"

    def test_finds_a_match_ignoring_case(self, plugin):
        assert plugin._find_campaign("Caucasus") == "caucasus"

    def test_finds_an_upper_case_match(self, plugin):
        assert plugin._find_campaign("GERMANY_MODERN") == "germany_modern"

    def test_returns_none_for_an_unknown_campaign(self, plugin):
        assert plugin._find_campaign("kola") is None

    def test_prefers_the_exact_match_when_one_exists(self, plugin_commands):
        plugin = object.__new__(plugin_commands.FootholdCheckpoint)
        plugin.campaigns = {"ca": object(), "CA": object()}

        assert plugin._find_campaign("CA") == "CA"


class TestUnknownFilesWarning:
    """The refusal message has to name the files and say nothing was changed."""

    def test_names_every_unknown_file(self, plugin_commands):
        message = plugin_commands.FootholdCheckpoint._format_unknown_files_warning(
            "foothold1",
            Path("C:/Saves"),
            ["FootHold_CA_v0.3.lua", "FootHold_CA_v0.3_CTLD_Save.csv"],
        )

        assert "FootHold_CA_v0.3.lua" in message
        assert "FootHold_CA_v0.3_CTLD_Save.csv" in message

    def test_warns_without_claiming_the_operation_was_refused(self, plugin_commands):
        """It is a warning, not a refusal: the save it accompanies did run."""
        message = plugin_commands.FootholdCheckpoint._format_unknown_files_warning(
            "foothold1", Path("C:/Saves"), ["FootHold_CA_v0.3.lua"]
        )

        assert "aborted" not in message.lower()
        assert "nothing was changed" not in message.lower()

    def test_explains_that_those_files_are_not_protected(self, plugin_commands):
        message = plugin_commands.FootholdCheckpoint._format_unknown_files_warning(
            "foothold1", Path("C:/Saves"), ["FootHold_CA_v0.3.lua"]
        )

        assert "never backed up" in message.lower()

    def test_names_the_server_and_the_directory(self, plugin_commands):
        message = plugin_commands.FootholdCheckpoint._format_unknown_files_warning(
            "foothold1", Path("C:/Saves"), ["FootHold_CA_v0.3.lua"]
        )

        assert "foothold1" in message
        assert "Saves" in message

    def test_says_what_to_do_about_it(self, plugin_commands):
        message = plugin_commands.FootholdCheckpoint._format_unknown_files_warning(
            "foothold1", Path("C:/Saves"), ["FootHold_CA_v0.3.lua"]
        )

        assert "campaigns.yaml" in message

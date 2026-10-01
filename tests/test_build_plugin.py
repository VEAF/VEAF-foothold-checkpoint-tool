"""Tests for the DCSServerBot plugin build script.

DCSServerBot migrates a plugin from the version stored in its database to the
one the plugin declares, one step at a time, with ``ver, rev = installed.split('.')``.
The plugin used to declare "2.0.0"; the next release, "2.2.0", crashed that
split and the plugin was not loaded in production. These tests pin the form
DCSServerBot can digest, on the ZIP actually shipped.
"""

import importlib.util
import zipfile
from pathlib import Path

import pytest

SCRIPT = Path(__file__).parent.parent / "scripts" / "build_plugin.py"


@pytest.fixture(scope="module")
def build_plugin():
    spec = importlib.util.spec_from_file_location("build_plugin", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def dcssb_upgrade(installed: str, target: str) -> str:
    """Replay DCSServerBot's Plugin._init_db upgrade walk (core/plugin.py)."""
    from packaging.version import parse

    while parse(installed) < parse(target):
        ver, rev = installed.split(".")
        installed = ver + "." + str(int(rev) + 1)
    return installed


@pytest.mark.parametrize(
    ("version", "expected"),
    [("2.2.0", "2.2"), ("2.10.3", "2.10"), ("3.0", "3.0"), ("2.2.0rc1", "2.2")],
)
def test_dcssb_version_keeps_major_minor(build_plugin, version, expected):
    assert build_plugin.dcssb_version(version) == expected


@pytest.mark.parametrize("version", ["2", "two.one", ""])
def test_dcssb_version_rejects_unusable_versions(build_plugin, version):
    with pytest.raises(ValueError):
        build_plugin.dcssb_version(version)


def test_shipped_version_survives_dcssb_upgrade(build_plugin, tmp_path):
    zip_path = build_plugin.build_plugin_zip(dist_dir=tmp_path)

    with zipfile.ZipFile(zip_path) as zipf:
        init_source = zipf.read("foothold-checkpoint/__init__.py").decode("utf-8")
    namespace: dict = {}
    exec(init_source, namespace)
    declared = namespace["__version__"]

    assert len(declared.split(".")) == 2
    assert dcssb_upgrade("2.0", declared) == declared

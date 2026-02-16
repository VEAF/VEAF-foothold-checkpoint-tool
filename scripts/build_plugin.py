#!/usr/bin/env python3
"""Build script for creating DCSServerBot plugin distribution ZIP."""

import zipfile
from pathlib import Path


def build_plugin_zip() -> None:
    """Create plugin distribution ZIP with all required files for DCSSB installation."""
    # Define paths
    repo_root = Path(__file__).parent.parent
    foothold_src = repo_root / "src" / "foothold_checkpoint"
    dist_dir = repo_root / "dist"

    # Read version from pyproject.toml
    pyproject = repo_root / "pyproject.toml"
    version = "2.0.0"  # default
    if pyproject.exists():
        for line in pyproject.read_text().split("\n"):
            if line.startswith("version = "):
                version = line.split('"')[1]
                break

    # Create dist directory
    dist_dir.mkdir(exist_ok=True)

    # Output ZIP path
    zip_path = dist_dir / f"foothold-checkpoint-plugin-v{version}.zip"

    print(f"Building DCSSB plugin distribution: {zip_path}")

    # Create ZIP with foothold-checkpoint/ as root directory
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
        # DCSSB expects commands.py directly in plugin root, not in plugin/ subdirectory
        # So we flatten the plugin/ folder structure to the root

        # Add __init__.py (version import only, setup is in commands.py)
        init_content = '''"""DCSServerBot plugin for Foothold Checkpoint management."""

from .version import __version__

__all__ = ["__version__"]
'''
        zipf.writestr("foothold-checkpoint/__init__.py", init_content)
        print("  Added: foothold-checkpoint/__init__.py (generated)")

        # Add all Python files from plugin/ directly to root (NOT in plugin/ subdir)
        # EXCEPT __init__.py which we already generated above
        plugin_dir = foothold_src / "plugin"
        for py_file in plugin_dir.glob("*.py"):
            if py_file.name == "__init__.py":
                continue  # Skip, we already generated a custom one
            arcname = Path("foothold-checkpoint") / py_file.name
            zipf.write(py_file, arcname)
            print(f"  Added: {arcname}")

        # Add plugin/schemas/ as schemas/
        schemas_dir = plugin_dir / "schemas"
        if schemas_dir.exists():
            for py_file in schemas_dir.rglob("*.py"):
                arcname = Path("foothold-checkpoint") / "schemas" / py_file.relative_to(schemas_dir)
                zipf.write(py_file, arcname)
                print(f"  Added: {arcname}")

        # Add all files from core directory
        core_dir = foothold_src / "core"
        for py_file in core_dir.rglob("*.py"):
            arcname = Path("foothold-checkpoint") / "core" / py_file.relative_to(core_dir)
            zipf.write(py_file, arcname)
            print(f"  Added: {arcname}")

        # Add py.typed marker
        py_typed = foothold_src / "py.typed"
        if py_typed.exists():
            zipf.write(py_typed, "foothold-checkpoint/py.typed")
            print("  Added: foothold-checkpoint/py.typed")

        # Add example configuration files from plugin folder
        config_example = plugin_dir / "foothold-checkpoint.yaml.example"
        if config_example.exists():
            zipf.write(config_example, "foothold-checkpoint.yaml.example")
            print("  Added: foothold-checkpoint.yaml.example")
        else:
            print("  Warning: foothold-checkpoint.yaml.example not found in plugin folder")

        # Add campaigns.yaml example from plugin folder
        campaigns_example = plugin_dir / "campaigns.yaml.example"
        if campaigns_example.exists():
            zipf.write(campaigns_example, "campaigns.yaml.example")
            print("  Added: campaigns.yaml.example")
        else:
            print("  Warning: campaigns.yaml.example not found in plugin folder")

        # Add README from plugin folder
        readme = plugin_dir / "README.md"
        if readme.exists():
            zipf.write(readme, "README.md")
            print("  Added: README.md")
        else:
            print("  Warning: README.md not found in plugin folder")

        # Add user manuals from plugin folder
        user_manual_en = plugin_dir / "PLUGIN_USER_MANUAL_EN.md"
        if user_manual_en.exists():
            zipf.write(user_manual_en, "PLUGIN_USER_MANUAL_EN.md")
            print("  Added: PLUGIN_USER_MANUAL_EN.md")
        else:
            print("  Warning: PLUGIN_USER_MANUAL_EN.md not found in plugin folder")

        user_manual_fr = plugin_dir / "PLUGIN_USER_MANUAL_FR.md"
        if user_manual_fr.exists():
            zipf.write(user_manual_fr, "PLUGIN_USER_MANUAL_FR.md")
            print("  Added: PLUGIN_USER_MANUAL_FR.md")
        else:
            print("  Warning: PLUGIN_USER_MANUAL_FR.md not found in plugin folder")

    print(f"\nPlugin ZIP created successfully: {zip_path}")
    print(f"Size: {zip_path.stat().st_size / 1024:.1f} KB")
    print("\nTo install:")
    print("  1. Extract to D:\\dev\\_VEAF\\VEAF-DCSServerBot\\plugins\\")
    print("  2. Configure config\\plugins\\foothold-checkpoint.yaml")
    print("  3. Configure config\\campaigns.yaml")
    print("  4. Restart DCSServerBot")


if __name__ == "__main__":
    build_plugin_zip()

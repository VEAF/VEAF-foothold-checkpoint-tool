#!/usr/bin/env python3
"""Build script for creating DCSServerBot plugin distribution ZIP."""

import zipfile
from pathlib import Path


def build_plugin_zip() -> None:
    """Create plugin distribution ZIP with all required files."""
    # Define paths
    repo_root = Path(__file__).parent.parent
    plugin_src = repo_root / "src" / "foothold_checkpoint" / "plugin"
    dist_dir = repo_root / "dist"
    version_file = plugin_src / "version.py"

    # Read version
    version_text = version_file.read_text()
    version = version_text.split('"')[1]  # Extract version from __version__ = "2.0.0"

    # Create dist directory
    dist_dir.mkdir(exist_ok=True)

    # Output ZIP path
    zip_path = dist_dir / f"foothold-plugin-v{version}.zip"

    print(f"Building plugin distribution: {zip_path}")

    # Create ZIP
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        # Add all Python files from plugin directory
        for py_file in plugin_src.rglob("*.py"):
            arcname = py_file.relative_to(plugin_src.parent)
            zipf.write(py_file, arcname)
            print(f"  Added: {arcname}")

        # Add YAML schema
        schema_file = plugin_src / "foothold_schema.yaml"
        if schema_file.exists():
            arcname = schema_file.relative_to(plugin_src.parent)
            zipf.write(schema_file, arcname)
            print(f"  Added: {arcname}")

        # Add README
        readme = repo_root / "README_PLUGIN.md"
        if readme.exists():
            zipf.write(readme, "README.md")
            print("  Added: README.md")

        # Create requirements.txt content in memory
        requirements = "discord.py>=2.3.0\nfoothold-checkpoint>=2.0.0\n"
        zipf.writestr("requirements.txt", requirements)
        print("  Added: requirements.txt")

    print(f"\nPlugin ZIP created successfully: {zip_path}")
    print(f"Size: {zip_path.stat().st_size / 1024:.1f} KB")


if __name__ == "__main__":
    build_plugin_zip()

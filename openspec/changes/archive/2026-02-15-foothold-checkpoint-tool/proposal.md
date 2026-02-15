## Why

VEAF runs multiple DCS servers hosting Foothold dynamic campaigns. Currently, there's no reliable way to save, restore, and manage campaign snapshots across servers. This prevents recovery from mistakes, testing scenarios on different servers, and maintaining campaign history. The tool addresses this gap by providing checkpoint management with integrity verification and cross-server restoration capabilities.

## What Changes

- **New CLI tool** `foothold-checkpoint` for managing Foothold campaign saves
- **Checkpoint operations**: save (single/all campaigns), restore, list, delete, import from manual backups
- **Integrity verification**: SHA-256 checksums for all saved files
- **Cross-server support**: restore checkpoints from one server to another
- **Campaign name normalization**: handle version suffixes (_v0.2, _V0.1) automatically
- **YAML configuration**: server paths, campaign name mappings, checkpoint storage location
- **Interactive mode**: Rich-based TUI with guided workflows
- **Metadata tracking**: server, campaign, timestamp, custom names/comments, original filenames
- **Plugin structure**: prepared for future DCSServerBot integration

## Capabilities

### New Capabilities

- `configuration-management`: Load, validate, and auto-create YAML configuration with server paths, campaign mappings, and checkpoint storage location
- `campaign-detection`: Detect and normalize campaign names from filesystem (handle version suffixes, group related files)
- `checkpoint-storage`: Create timestamped ZIP archives with metadata (checksums, server, campaign, custom fields)
- `checkpoint-restoration`: Restore checkpoints with integrity verification, cross-server support, and optional Foothold_Ranks.lua inclusion (excluded by default)
- `checkpoint-listing`: List and filter checkpoints by server/campaign with metadata display
- `checkpoint-deletion`: Delete checkpoints with confirmation prompts
- `checkpoint-import`: Import existing manual backups into checkpoint format with campaign detection, metadata collection, and file validation warnings
- `cli-interface`: Typer-based CLI with Rich UI, supporting both command-line options and interactive guided mode

### Modified Capabilities

<!-- No existing capabilities are being modified -->

## Impact

**New Components:**
- `foothold_checkpoint/` Python package (core logic)
- `foothold_checkpoint/core/` modules: config, campaign, checkpoint, storage
- `foothold_checkpoint/cli.py` CLI entry point
- `plugin/` directory structure for future DCSServerBot integration
- `~/.foothold-checkpoint/config.yaml` user configuration
- `~/.foothold-checkpoints/` default checkpoint storage

**Dependencies:**
- Python 3.10+ (type hints)
- Typer (CLI framework)
- Rich (terminal UI)
- PyYAML (configuration)
- Pydantic (config validation)
- Standard library: zipfile, hashlib, pathlib, datetime

**Development Tools:**
- pytest (testing)
- ruff (linting)
- black (formatting)
- mypy (type checking)

**No Breaking Changes:** This is a new standalone tool with no existing integrations.

# VEAF Foothold Checkpoint Tool

[![CI](https://github.com/VEAF/VEAF-foothold-checkpoint-tool/actions/workflows/ci.yml/badge.svg)](https://github.com/VEAF/VEAF-foothold-checkpoint-tool/actions/workflows/ci.yml)

A CLI tool for managing DCS Foothold campaign checkpoints with integrity verification and cross-server restoration.

## 🚀 Features

- **Save checkpoints**: Create timestamped backups of Foothold campaign saves with SHA-256 integrity verification
- **Restore checkpoints**: Restore campaigns with automatic integrity checks and auto-backup
- **Auto-backup before restore**: Automatically creates a backup before overwriting files (v1.1.0+)
- **Automatic file renaming**: Transparently rename files when restoring old checkpoints (v1.1.0+)
- **Unknown file detection**: Helpful error messages with YAML snippets for unconfigured files (v1.1.0+)
- **Cross-server support**: Move checkpoints between different DCS servers
- **Campaign evolution**: Automatically handle campaign name changes (e.g., `GCW_Modern` → `Germany_Modern`)
- **Import**: Convert existing manual backups to checkpoint format
- **Flexible CLI**: Use command-line flags or interactive prompts
- **Rich terminal UI**: Progress bars, tables, colored output, and `--details` flag for file lists
- **DCSServerBot Plugin**: Discord slash commands for checkpoint management (see [Plugin Guide](src/foothold_checkpoint/plugin/README.md))

## 🎮 DCSServerBot Integration

The tool can be used as a plugin for [DCSServerBot](https://github.com/Special-K-s-Flightsim-Bots/DCSServerBot), providing Discord slash commands for checkpoint management:

- `/foothold-checkpoint save` - Create checkpoints from Discord
- `/foothold-checkpoint restore` - Restore checkpoints via Discord UI
- `/foothold-checkpoint list` - Browse available checkpoints
- `/foothold-checkpoint delete` - Remove old checkpoints

**See the [Plugin Guide](src/foothold_checkpoint/plugin/README.md) for installation and configuration.**

## 📋 Status

🎉 **Version 2.0.0 Released!** - February 16, 2026

**All Features Complete**:

- ✅ **DCSServerBot plugin** with full Discord UI integration
- ✅ All core features implemented and tested (save, restore, list, delete, import)
- ✅ Explicit file list configuration with optional files support
- ✅ Auto-backup and automatic file renaming on restore
- ✅ Checkpoint grouping and sorting (manual first, auto-backups last)
- ✅ External campaigns configuration for shared CLI/plugin setup
- ✅ Unknown file detection with helpful configuration suggestions
- ✅ Complete CLI with error handling, interactive prompts, and quiet mode
- ✅ 306 tests (302 passing) with core coverage 76-100%
- ✅ Comprehensive documentation (user guide, plugin guide EN/FR, contributing guide)
- ✅ Real campaign data integration testing
- ✅ Code quality checks (ruff, black, mypy)
- ✅ Cross-platform testing (Windows + Linux/WSL)
- ✅ Ready for production use!

**New in v2.0.0**: DCSServerBot plugin integration, external campaigns configuration, checkpoint grouping UI

⚠️ **Breaking Change**: Configuration format changed. See [CHANGELOG.md](CHANGELOG.md) for migration guide.

## 📖 Documentation

- **[User Guide](USERS.md)** - Installation and usage instructions
- **[Contributing Guide](CONTRIBUTING.md)** - Development setup and guidelines
- **[OpenSpec Proposal](openspec/changes/foothold-checkpoint-tool/proposal.md)** - Project vision
- **[OpenSpec Design](openspec/changes/foothold-checkpoint-tool/design.md)** - Technical architecture
- **[OpenSpec Specs](openspec/changes/foothold-checkpoint-tool/specs/)** - Detailed requirements
- **[OpenSpec Tasks](openspec/changes/foothold-checkpoint-tool/tasks.md)** - Implementation checklist

## 🎯 Quick Start

```powershell
# Installation (when available)
poetry install

# Fully interactive mode
poetry run foothold-checkpoint

# Save a checkpoint
poetry run foothold-checkpoint save --server production-1 --campaign afghanistan

# List checkpoints
poetry run foothold-checkpoint list

# Restore a checkpoint
poetry run foothold-checkpoint restore afghanistan_2024-02-13_14-30-00.zip --server test-server
```

See **[USERS.md](USERS.md)** for detailed usage instructions.

## 🤝 Contributing

We welcome contributions! See **[CONTRIBUTING.md](CONTRIBUTING.md)** for:
- Development setup with Poetry
- Coding standards and guidelines
- Testing requirements
- Pull request process

## 📄 License

TBD

## 🏢 Credits

Developed for [VEAF](https://www.veaf.org/) - Virtual European Air Force

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/VEAF/VEAF-foothold-checkpoint-tool/issues)
- **Repository**: [GitHub](https://github.com/VEAF/VEAF-foothold-checkpoint-tool)

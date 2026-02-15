# VEAF Foothold Checkpoint Tool

[![CI](https://github.com/VEAF/VEAF-foothold-checkpoint-tool/actions/workflows/ci.yml/badge.svg)](https://github.com/VEAF/VEAF-foothold-checkpoint-tool/actions/workflows/ci.yml)

A CLI tool for managing DCS Foothold campaign checkpoints with integrity verification and cross-server restoration.

## 🚀 Features

- **Save checkpoints**: Create timestamped backups of Foothold campaign saves with SHA-256 integrity verification
- **Restore checkpoints**: Restore campaigns with automatic integrity checks and auto-backup
- **Auto-backup before restore**: Automatically creates a backup before overwriting files (new in v1.1.0)
- **Automatic file renaming**: Transparently rename files when restoring old checkpoints (new in v1.1.0)
- **Unknown file detection**: Helpful error messages with YAML snippets for unconfigured files (new in v1.1.0)
- **Cross-server support**: Move checkpoints between different DCS servers
- **Campaign evolution**: Automatically handle campaign name changes (e.g., `GCW_Modern` → `Germany_Modern`)
- **Import**: Convert existing manual backups to checkpoint format
- **Flexible CLI**: Use command-line flags or interactive prompts
- **Rich terminal UI**: Progress bars, tables, colored output, and `--details` flag for file lists

## 📋 Status

🎉 **Version 1.1.0 Released!** - February 15, 2026

**All Features Complete**:

- ✅ All core features implemented and tested (save, restore, list, delete, import)
- ✅ Explicit file list configuration with optional files support
- ✅ Auto-backup and automatic file renaming on restore
- ✅ Unknown file detection with helpful configuration suggestions
- ✅ Complete CLI with error handling, interactive prompts, and quiet mode
- ✅ 304 tests passing with 79% code coverage (100% on core modules)
- ✅ Comprehensive documentation (user guide, contributing guide, release notes)
- ✅ Real campaign data integration testing
- ✅ Code quality checks (ruff, black, mypy)
- ✅ Cross-platform testing (Windows + Linux/WSL)
- ✅ Ready for production use!

**New in v1.1.0**: Structured campaign configuration, auto-backup protection, file renaming on restore, unknown file detection

⚠️ **Breaking Change**: Configuration format changed in v1.1.0. See [CHANGELOG.md](CHANGELOG.md) for migration guide.

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

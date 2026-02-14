# VEAF Foothold Checkpoint Tool

A CLI tool for managing DCS Foothold campaign checkpoints with integrity verification and cross-server restoration.

## 🚀 Features

- **Save checkpoints**: Create timestamped backups of Foothold campaign saves with SHA-256 integrity verification
- **Restore checkpoints**: Restore campaigns with automatic integrity checks
- **Cross-server support**: Move checkpoints between different DCS servers
- **Campaign evolution**: Automatically handle campaign name changes (e.g., `GCW` → `Germany_Modern`)
- **Import**: Convert existing manual backups to checkpoint format
- **Flexible CLI**: Use command-line flags or interactive prompts
- **Rich terminal UI**: Progress bars, tables, and colored output

## 📋 Status

🎉 **Version 1.0.0 Released!** - February 14, 2026

**All Features Complete**:

- ✅ All core features implemented and tested (save, restore, list, delete, import)
- ✅ Complete CLI with error handling, interactive prompts, and quiet mode
- ✅ 347 tests passing with 86% code coverage
- ✅ Comprehensive documentation (user guide, contributing guide, release notes)
- ✅ Real campaign data integration testing
- ✅ Code quality checks (ruff, black, mypy)
- ✅ Manual testing completed with user feedback
- ✅ Ready for production use!

**Features**: Numeric checkpoint selection, case-insensitive matching, batch operations, auto-clearing spinners, and more!

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
pip install foothold-checkpoint

# Save a checkpoint
foothold-checkpoint save --server production-1 --campaign afghanistan

# List checkpoints
foothold-checkpoint list

# Restore a checkpoint
foothold-checkpoint restore afghanistan_2024-02-13_14-30-00.zip --server test-server
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

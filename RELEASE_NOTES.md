# Release Notes - v1.0.0

## 🎉 VEAF Foothold Checkpoint Tool v1.0.0

**Release Date**: February 14, 2026

We're excited to announce the first stable release of the VEAF Foothold Checkpoint Tool! This tool provides a robust, user-friendly way to manage DCS Foothold campaign checkpoints with integrity verification and cross-server restoration capabilities.

## ✨ Highlights

### Complete Checkpoint Management
- **Save**: Create timestamped, verified backups of your Foothold campaigns
- **Restore**: Restore checkpoints with automatic integrity verification
- **List**: Browse checkpoints with beautiful table formatting
- **Delete**: Safely remove old checkpoints with confirmation
- **Import**: Convert existing manual backups to checkpoint format

### Smart Features
- **SHA-256 Integrity Verification**: Every file is checksummed to ensure data integrity
- **Campaign Evolution Tracking**: Automatically handles campaign name changes (e.g., GCW → Germany_Modern)
- **Cross-Server Support**: Move checkpoints between different DCS servers seamlessly
- **Shared File Management**: Intelligently handles Foothold_Ranks.lua

### User-Friendly CLI
- **Interactive Mode**: Beautiful terminal UI with colors, progress bars, and tables
- **Quiet Mode**: Perfect for automation and scripting
- **Numeric Selection**: Use `restore 1` instead of typing long filenames
- **Multiple Selection**: Restore or delete multiple checkpoints at once (e.g., `1,3,5` or `1-3`)
- **Case-Insensitive**: No more case sensitivity issues with server/campaign names
- **Smart Prompts**: Interactive menus when you leave out required options

### Quality Assurance
- **347 Comprehensive Tests**: 86% code coverage ensures reliability
- **Type-Safe**: Full mypy compliance for type safety
- **Well-Documented**: Complete user and developer guides
- **Professional Code**: Black formatting, Ruff linting

## 📦 Installation

### From Source (Development)
```powershell
# Clone the repository
git clone https://github.com/VEAF/VEAF-foothold-checkpoint-tool.git
cd VEAF-foothold-checkpoint-tool

# Install with Poetry
poetry install

# Run the tool
poetry run foothold-checkpoint --help
```

### Requirements
- Python 3.10 or higher
- Windows, Linux, or macOS

## 🚀 Quick Start

### 1. Create Configuration File
```powershell
# First run creates config.yaml with prompts
foothold-checkpoint save
```

### 2. Save Your First Checkpoint
```powershell
# Interactive mode
foothold-checkpoint save

# Command-line flags
foothold-checkpoint save --server my-server --campaign afghanistan
```

### 3. List Your Checkpoints
```powershell
# Beautiful table view
foothold-checkpoint list

# Filter by campaign
foothold-checkpoint list --campaign afghanistan

# Quiet mode for scripts
foothold-checkpoint --quiet list
```

### 4. Restore a Checkpoint
```powershell
# By number (from list)
foothold-checkpoint restore 1 --server my-server

# By filename
foothold-checkpoint restore checkpoint.zip --server my-server

# Multiple checkpoints
foothold-checkpoint restore 1,3,5 --server my-server
```

## 🎯 Use Cases

### Regular Backups
Create scheduled checkpoints before server restarts:
```powershell
foothold-checkpoint --quiet save --server prod-1 --campaign afghanistan --name "Pre-restart"
```

### Cross-Server Migration
Move campaigns between test and production servers:
```powershell
# Save from test server
foothold-checkpoint save --server test-1 --campaign afghanistan

# List to get checkpoint number
foothold-checkpoint list --server test-1

# Restore to production (with verification)
foothold-checkpoint restore 1 --server prod-1
```

### Campaign Updates
Before updating Foothold, create a safety checkpoint:
```powershell
foothold-checkpoint save --server prod-1 --all --name "Before v1.2 update"
```

### Import Existing Backups
Convert your manual backups to checkpoint format:
```powershell
foothold-checkpoint import /path/to/backup --server prod-1
```

## 📚 Documentation

- **[User Guide](USERS.md)**: Complete usage instructions
- **[Contributing Guide](CONTRIBUTING.md)**: How to contribute
- **[Changelog](CHANGELOG.md)**: Detailed version history

## 🔧 Configuration

The tool uses a YAML configuration file (`config.yaml`):

```yaml
# Checkpoint storage directory
checkpoints_directory: "~/foothold-checkpoints"

# Server configurations
servers:
  production-1:
    path: "C:/Users/Admin/Saved Games/DCS.openbeta_server/Missions/Saves"
    
  test-server:
    path: "C:/Users/Admin/DCS Test Server/Missions/Saves"

# Campaign name evolution tracking
campaign_names:
  GCW_Modern: Germany_Modern
  GCW_Coldwar: Germany_Coldwar
```

## 🐛 Known Issues

None! This is the first stable release with comprehensive testing.

## 🤝 Contributing

We welcome contributions! See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## 📝 License

[License information to be added]

## 🙏 Acknowledgments

- **DCS Community**: For the amazing Foothold campaign
- **VEAF Team**: For project support and testing
- **Contributors**: Everyone who provided feedback and bug reports

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/VEAF/VEAF-foothold-checkpoint-tool/issues)
- **Discord**: [VEAF Discord Server](https://discord.gg/veaf)

---

**Enjoy managing your Foothold campaigns!** 🎮✈️

# Release Notes

## Version 2.0.0 - February 16, 2026

### ⚠️ Breaking Changes

**This is a major release with breaking changes.** Your configuration file requires migration.

See **[MIGRATION_v1.1.0.md](MIGRATION_v1.1.0.md)** for detailed upgrade instructions.

### 🎯 What's New

#### 🤖 DCSServerBot Plugin Integration
**Major new feature:** Full integration as a DCSServerBot plugin with Discord UI!

- 📦 **Plugin package** ready for deployment (`foothold-checkpoint-plugin-v2.0.0.zip`)
- 🏗️ **Plugin architecture** using DCSServerBot's `Plugin` base class
- 🔌 **Event listener** integration for DCS events
- ⚙️ **Auto-configuration** via `self.locals` and `self.get_config(server)`
- 📢 **Notification system** with per-server channels and toggles
- 🎮 **Discord commands** with interactive UI dropdowns and buttons
- 📚 **Comprehensive documentation** in English and French

**Plugin Features:**
- `/foothold-checkpoint save` - Create checkpoints from Discord
- `/foothold-checkpoint restore` - Restore with interactive selection
- `/foothold-checkpoint list` - View checkpoints with filtering
- `/foothold-checkpoint delete` - Delete with confirmation dialogs
- Auto-backup protection before restores (enabled by default)
- Visual separator between manual checkpoints and auto-backups
- Server and campaign selection via dropdowns
- Permission controls (administrator-only by default)

#### 🗂️ External Campaigns Configuration
Share campaign definitions between CLI and plugin:

```yaml
# config.yaml
campaigns_file: campaigns.yaml
```

- ✅ **DRY principle**: Single source of truth for campaign configuration
- ✅ **Shared config**: Used by both CLI tool and DCSServerBot plugin
- ✅ **Backward compatible**: Inline campaigns still supported
- ✅ **Validation**: Clear errors if configuration is invalid

#### 🔧 Explicit File Configuration
The most significant change in v1.1.0 is the new **structured file list** configuration format, replacing regex-based pattern matching:

**Before (v1.0.x):**
```yaml
campaigns:
  Afghanistan: ["afghanistan"]
  Caucasus: ["CA"]
```

**After (v1.1.0):**
```yaml
campaigns:
  afghanistan:
    display_name: "Afghanistan"
    files:
      persistence:
        - "FootHold_afghanistan.lua"
      ctld_save:
        - "FootHold_afghanistan_CTLD_Save.csv"
      storage:
        files:
          - "foothold_afghanistan_storage.csv"
        optional: true
```

**Benefits:**
- ✅ **Explicit control**: Define exactly which files belong to each campaign
- ✅ **Optional files**: Mark storage/CTLD files as optional (no warnings if missing)
- ✅ **Better errors**: See exactly what's configured vs. what's found
- ✅ **File renaming support**: Handle campaign name evolution transparently
- ✅ **No false positives**: No more regex guessing errors

#### 🔍 Unknown File Detection
Automatic detection and helpful error messages for unconfigured campaign files:

```
Error: Found 2 files that don't match any configured campaign:
  - FootHold_new_campaign.lua
  - FootHold_new_campaign_storage.csv

Suggested configuration:
────────────────────────────────────────
  new_campaign:
    display_name: "New Campaign"
    files:
      persistence:
        - "FootHold_new_campaign.lua"
      storage:
        files:
          - "FootHold_new_campaign_storage.csv"
        optional: true
────────────────────────────────────────
```

- 📋 Lists all unknown files found
- 💡 Generates ready-to-use YAML configuration snippets
- 🛡️ Prevents accidental data loss from untracked files

#### 💾 Auto-Backup Before Restore
Protects your data with automatic backups before any restore operation:

```powershell
# Enabled by default
foothold-checkpoint restore checkpoint.zip --server prod-1

# Creates: afghanistan_backup_2026-02-15_14-30-00.zip
```

- 🔄 Automatic backup creation with `--auto-backup` flag (default: enabled)
- 📝 Backup filename includes full campaign name and timestamp
- ⚙️ Can be disabled with `--no-auto-backup` if needed
- 🛡️ Protects against accidental overwrites

#### 🔄 Automatic File Renaming
Transparent handling of campaign name evolution:

- 🏷️ Files automatically renamed to canonical names from configuration
- 📦 Preserves compatibility with old checkpoints
- ✨ No user intervention needed
- 🔀 Example: `FootHold_GCW_Modern.lua` → `FootHold_germany_modern.lua`

The first name in your file list becomes the canonical name used during restore.

#### 📊 Enhanced List Command
New `--details` flag to inspect checkpoint contents:

```powershell
foothold-checkpoint list --details
```

Output:
```
Checkpoint: afghanistan_2026-02-15_10-30-00.zip
  Server: production-1
  Campaign: afghanistan
  Files:
    - FootHold_afghanistan.lua
    - FootHold_afghanistan_CTLD_Save.csv
    - foothold_afghanistan_storage.csv
    - Foothold_Ranks.lua
```

- 📁 Shows all files contained in each checkpoint
- 🔍 Helps verify checkpoint contents before restore
- 🎨 Formatted output with proper indentation

#### � Checkpoint Grouping and Sorting
Improved organization of checkpoint lists for better user experience:

- 📑 **Manual checkpoints listed first**, auto-backups listed last
- ➖ **Visual separator** ("AUTO-BACKUPS") in both CLI and Discord UI
- 📅 **Chronological sorting** within each group (oldest first, newest last)
- 🎯 **Easier selection** in dropdown menus (most recent at bottom)

Example output:
```
Checkpoints for Afghanistan:
  1. campaign_save_morning.zip      (2024-02-10)  2.1 MB
  2. weekend_snapshot.zip            (2024-02-14)  2.2 MB
  ────────────── AUTO-BACKUPS ──────────────
  3. auto-backup-20240216-201000.zip (2024-02-16)  2.3 MB
  4. auto-backup-20240216-221045.zip (2024-02-16)  2.3 MB
```

#### �💬 Improved Error Messages
More helpful and actionable error messages throughout:

- 🔧 Unknown file errors include YAML configuration snippets
- 📍 Campaign/server not found errors list available options
- ✅ Config validation errors show specific field locations
- 🎯 Clearer guidance on how to fix issues

### 🔒 Quality Assurance

- ✅ **304 tests passing** (comprehensive test coverage)
- ✅ **95% code coverage** on core modules
- ✅ **Type-safe**: Full mypy compliance
- ✅ **Cross-platform**: Windows, Linux, macOS support
- ✅ **Code quality**: Black formatting, Ruff linting

### 📦 Installation

No changes to installation process:

```powershell
# From source
git clone https://github.com/VEAF/VEAF-foothold-checkpoint-tool.git
cd VEAF-foothold-checkpoint-tool
poetry install
```

### 🚀 Upgrading from v1.0.x

**Required:** Update your `config.yaml` file to the new format.

See **[MIGRATION_v1.1.0.md](MIGRATION_v1.1.0.md)** for:
- Step-by-step migration instructions
- Configuration examples for each campaign
- Automated migration helper tool
- Common pitfalls and solutions

### 📚 Documentation

- **[Migration Guide](MIGRATION_v1.1.0.md)**: v1.0.x → v1.1.0 upgrade instructions
- **[User Guide](USERS.md)**: Updated with new features
- **[Changelog](CHANGELOG.md)**: Complete version history
- **[Config Example](config.yaml.example)**: New configuration format

### 🙏 Acknowledgments

- **VEAF Team**: Testing and feedback on the new configuration format
- **Contributors**: Bug reports and feature suggestions
- **Community**: Patience during the breaking change

---

## Version 1.0.1 - February 14, 2026

**Patch release** - Cross-platform compatibility fixes.

### 🐛 Bug Fixes

- **Campaign name mapping**: Fixed `map_campaign_name()` to correctly return the last (current) name from the campaign names list, ensuring files are restored with correct naming
- **Linux/WSL compatibility**: 
  - Marked Windows-specific tests appropriately
  - Fixed path handling for Unix systems
- **Code quality**: Fixed ruff linting error in campaign mapping

### 📦 Installation

```powershell
git clone https://github.com/VEAF/VEAF-foothold-checkpoint-tool.git
cd VEAF-foothold-checkpoint-tool
git checkout v1.0.1
poetry install
```

### 🔒 Quality Assurance

- ✅ **350 tests passing** (3 skipped on Windows as expected)
- ✅ **83% code coverage**
- ✅ All quality checks pass

---

## Version 1.0.0 - February 14, 2026

**Initial stable release** of the VEAF Foothold Checkpoint Tool.

### ✨ Features

#### Complete Checkpoint Management
- **Save**: Create timestamped, verified backups of your Foothold campaigns
- **Restore**: Restore checkpoints with automatic integrity verification
- **List**: Browse checkpoints with beautiful table formatting
- **Delete**: Safely remove old checkpoints with confirmation
- **Import**: Convert existing manual backups to checkpoint format

#### Smart Features
- **SHA-256 Integrity Verification**: Every file is checksummed to ensure data integrity
- **Campaign Evolution Tracking**: Automatically handles campaign name changes (e.g., GCW → Germany_Modern)
- **Cross-Server Support**: Move checkpoints between different DCS servers seamlessly
- **Shared File Management**: Intelligently handles Foothold_Ranks.lua

#### User-Friendly CLI
- **Interactive Mode**: Beautiful terminal UI with colors, progress bars, and tables
- **Quiet Mode**: Perfect for automation and scripting
- **Numeric Selection**: Use `restore 1` instead of typing long filenames
- **Multiple Selection**: Restore or delete multiple checkpoints at once (e.g., `1,3,5` or `1-3`)
- **Case-Insensitive**: No more case sensitivity issues with server/campaign names
- **Smart Prompts**: Interactive menus when you leave out required options

### 🔒 Quality Assurance
- **347 tests passing**: 86% code coverage
- **Type-safe**: Full mypy compliance
- **Well-documented**: Complete user and developer guides
- **Professional code**: Black formatting, Ruff linting

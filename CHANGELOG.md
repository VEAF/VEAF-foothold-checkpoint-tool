# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [1.1.0] - 2026-02-15

### Added
- **Explicit file list configuration**: Campaigns now use structured file lists instead of regex patterns
  - Separate configuration for persistence files, CTLD saves, CTLD FARPs, and storage files
  - Optional file types with `optional: true` flag
  - Improved validation prevents empty required file lists
  - Better support for campaign evolution (multiple accepted names per file)
- **Unknown file detection**: Automatic detection and helpful error messages for unconfigured campaign files
  - Generates YAML configuration snippets for quick setup
  - Lists all unknown files with suggested configuration
  - Prevents accidental data loss from untracked files
- **Auto-backup before restore**: Creates timestamped backup before overwriting files
  - Automatic backup creation with `--auto-backup` flag (default: enabled)
  - Backup includes full campaign name in filename for clarity
  - Can be disabled with `--no-auto-backup` flag
  - Protects against accidental overwrites
- **Automatic file renaming on restore**: Files are renamed to canonical names from configuration
  - Supports campaign name evolution (e.g., `FootHold_GCW_Modern.lua` → `FootHold_germany_modern.lua`)
  - First name in file list is used as canonical name
  - Preserves compatibility with old checkpoints
  - Transparent handling - no user intervention needed
- **Enhanced list command**: Added `--details` flag to display file lists in checkpoints
  - Shows all files contained in each checkpoint
  - Helps verify checkpoint contents before restore
  - Formatted output with proper indentation
- **Improved error messages**: More helpful and actionable error messages throughout
  - Unknown file errors include YAML configuration snippets
  - Campaign/server not found errors list available options
  - Config validation errors provide specific field locations

### Changed
- **Configuration structure**: Campaign configuration now uses explicit file lists instead of name patterns
  - Migration required: old `campaigns: {"Afghanistan": ["afghanistan"]}` format replaced with structured `CampaignConfig` objects
  - See `config.yaml.example` for new format
  - Breaking change: requires configuration file update
- **Campaign detection**: Uses configured file lists instead of regex patterns
  - More predictable and explicit behavior
  - Better error messages when files don't match configuration
  - No more false positives from similar file names

### Fixed
- **Type safety**: Fixed mypy type checking error in `load_config()` for checkpoints_dir parameter
- **Code quality**: Cleaned up unused imports and simplified dict iteration
- **Cross-platform**: Fixed test compatibility issues for Linux/WSL
  - Path handling now works correctly on both Windows and Unix systems
  - Tests skip gracefully on incompatible platforms

## [1.0.1] - 2026-02-14

### Fixed
- **Cross-platform compatibility**: Fixed 3 tests that were failing under Linux/WSL
  - `map_campaign_name()` now correctly returns the last (current) name from the campaign name list instead of the dictionary key, ensuring files are restored with the correct naming convention as documented
  - Marked `test_path_expansion_with_windows_style_envvar` as Windows-only (Windows `%VAR%` syntax not supported on Linux)
  - Marked `test_delete_checkpoint_handles_permission_error` as Windows-only (Linux allows deletion of read-only files when parent directory is writable)
- **Campaign name restoration**: Files are now restored using the exact name specified as the last entry in the campaign names list (config.yaml), preserving case sensitivity as intended
- **Code quality**: Fixed ruff linting error (unused loop variable)

## [1.0.0] - 2026-02-14

Initial release of the VEAF Foothold Checkpoint Tool.

### Added

#### Core Features
- **Configuration Management**
  - YAML-based configuration with Pydantic validation
  - Auto-creation of default configuration file
  - Path expansion for tilde (~) and environment variables
  - Campaign name evolution tracking (e.g., GCW_Modern → Germany_Modern)
  - Server configuration with mission directory paths

- **Campaign Detection**
  - Automatic detection of Foothold campaign files
  - Smart grouping by campaign name (case-insensitive, version-aware)
  - Support for version suffixes (v0.1, v1.0, etc.)
  - Recognition of shared files (Foothold_Ranks.lua)
  - Campaign name mapping for historical evolution

- **Checkpoint Management**
  - Create timestamped checkpoint archives (ZIP format)
  - SHA-256 checksum verification for file integrity
  - Optional checkpoint names and comments
  - Metadata preservation (campaign, server, timestamp, file hashes)
  - Progress tracking for long operations

- **Checkpoint Operations**
  - **Save**: Create checkpoints from mission directories
  - **Restore**: Restore checkpoints with integrity verification
  - **List**: View checkpoints with filtering (server, campaign)
  - **Delete**: Remove checkpoints with confirmation
  - **Import**: Import external checkpoint files

#### Command-Line Interface
- Interactive mode with rich formatting and colors
- Quiet mode for automation and scripting
- Comprehensive error messages with actionable guidance
- Progress indicators for long operations
- Tab completion support
- **Numeric selection** for restore and delete commands (e.g., `restore 1` or `restore 1,3,5`)
- **Case-insensitive** server and campaign matching
- Interactive command menu when no command specified
- Comment column display in list command
- Multiple checkpoint selection for batch operations
- Auto-clearing progress spinners with proper lifecycle management

#### Plugin System
- DCSServerBot plugin integration
- Discord bot commands for checkpoint management
- Administrator-only access controls

#### Quality & Testing
- 347 comprehensive tests with 86% code coverage
- Test-Driven Development (TDD) approach
- Type checking with mypy (strict mode)
- Code formatting with Black
- Linting with Ruff
- Pre-commit hooks configuration

#### Documentation
- Complete user guide (USERS.md)
- Developer guide (CONTRIBUTING.md)
- OpenSpec design artifacts
- Inline code documentation with examples
- Example configuration files

### Technical Details
- **Language**: Python 3.10+
- **Package Manager**: Poetry
- **Key Dependencies**: Pydantic, Typer, Rich, PyYAML
- **Testing**: pytest with comprehensive coverage
- **Type Safety**: Full mypy compliance
- **Code Quality**: Black formatting, Ruff linting

[Unreleased]: https://github.com/VEAF/VEAF-foothold-checkpoint-tool/compare/v1.0.0...HEAD
[1.0.0]: https://github.com/VEAF/VEAF-foothold-checkpoint-tool/releases/tag/v1.0.0

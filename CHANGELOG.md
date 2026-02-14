# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [1.0.0] - TBD

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

#### Plugin System
- DCSServerBot plugin integration
- Discord bot commands for checkpoint management
- Administrator-only access controls

#### Quality & Testing
- 350+ comprehensive tests with 94% code coverage
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

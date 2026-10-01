# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- **The tool now asks the mission what it is writing**, instead of trusting the configuration alone.
  Foothold names its persistence file after the mission version, so every mission update invents a
  filename no campaign declares and the campaign silently stops being captured. That had already
  happened four times on the VEAF servers, twice unnoticed.
  - `foothold.status`, written by the mission beside its saves on every save, holds the path of the
    file actually in use. It is read once per server, around the save rather than inside it
  - Everything that *is* configured is still saved. The report then names the live campaign and
    lists the files to add, read from the directory rather than guessed from the file name - the
    Cold War campaigns use a CSV naming that no amount of stem arithmetic produces. Files another
    campaign already declares are left out: the modern and Cold War campaigns share a name prefix
    and must never be folded into one
  - It is reported as a failure, not a footnote: the Discord command sends a separate error message
    and the CLI exits non-zero, after the checkpoints are safely written
  - It deliberately does not abort the save. A save runs once per campaign, so aborting would have
    refused every campaign on the server - turning one unprotected campaign into an unprotected
    server on the very event this feature exists to catch, a Foothold version bump
  - Degrades quietly: a missing, empty or unexpected `foothold.status` leaves the previous behaviour
    untouched. The format belongs to Foothold, not to this tool

### Fixed
- **DCSServerBot refused to load the plugin after an upgrade**: the plugin declared a three-part
  version, which DCSServerBot stores in its `plugins` table and later walks with
  `ver, rev = installed.split('.')`. The first install worked, the first upgrade (2.0.0 to 2.2.0)
  crashed with `too many values to unpack` and left the plugin unloaded
  - The ZIP built by `scripts/build_plugin.py` now declares `MAJOR.MINOR` (`2.2`) to DCSServerBot.
    `pyproject.toml` and `version.py` keep the full release number
  - A server that already recorded `2.0.0` must be corrected once before starting the new version:
    `UPDATE plugins SET version = '2.2' WHERE plugin = 'foothold-checkpoint';`
- **Silent data loss when campaign files are renamed on the server**: a campaign whose files were
  renamed without `campaigns.yaml` following became invisible to the tool. Saves captured nothing,
  restores reported success while writing files the running mission no longer reads, and nothing
  anywhere said so.
  - `save` and `restore` now warn, on both the CLI and Discord, when the server's `Missions/Saves`
    holds Foothold files that no campaign in the configuration lists, and name them. This warns
    rather than blocks: an unconfigured campaign on the server is no reason to stop backing up the
    configured ones
  - `restore` aborts with `EmptyBackupError` when its automatic backup captured nothing *and*
    unrecognised campaign files are present, instead of overwriting a state it could not protect and
    reporting success. Nothing is written in that case. Restoring into a directory holding no
    campaign file at all stays allowed: seeding a fresh server has nothing to lose
  - `save --all` no longer discards per-campaign failures without a trace
- **Checkpoints could overwrite each other**: filenames carry a one-second timestamp and the archive
  was opened in truncating mode, so two checkpoints of one campaign taken in the same second
  collided and the first was destroyed. Since the pre-restore backup lands in the same directory
  with the same naming scheme, it could wipe the very checkpoint being restored. A numeric suffix is
  now added rather than overwriting, and the archive is created exclusively so that two processes
  racing for the same name cannot both win
- **DCSServerBot plugin success message never named the backup**: it searched for `auto-backup-*.zip`
  while checkpoints are always named after their campaign, so the search matched nothing. The name
  now comes from the operation itself
- **DCSServerBot plugin rejected campaigns on letter case**: a checkpoint whose campaign was renamed
  to a different case became unrestorable. Lookup is now case-insensitive, as it already was in the CLI
- **Deliberate CLI exits were reported as crashes**: `typer.Exit` subclasses `RuntimeError`, so a
  normal exit inside a command was caught by that command's own error handler and echoed back as
  `Error: 1` or `Warning: 1` on top of the real message

### Added
- **Log file**: the tool wrote nothing to disk, so a misbehaving operation left no trace once the
  console scrolled. Saves and restores now record the campaign, the server, the source or target
  directory, the resulting files, and failures with their traceback. Checkpoint creation is logged
  in `create_checkpoint`, which both front ends go through, so a CLI save leaves the same trace as a
  Discord one
  - CLI: `--log-file PATH`, defaulting to `~/.foothold-checkpoint/logs/foothold-checkpoint.log`,
    rotating at 5 MB over three files
  - DCSServerBot plugin: records go to the bot's own log; the plugin installs no handler of its own
  - Restoring a file under a different canonical name is logged, since that silent rename is how a
    restore ends up writing files the running mission does not read
- **CLI `--debug`**: prints the full traceback on failure and raises the log level to `DEBUG`.
  Without it, failures now at least tell the user the flag exists
- **First automated tests for the DCSServerBot plugin**, which had none. CI installs the plugin
  dependency group so they run

## [2.2.0] - 2026-03-13

### Fixed
- **DCSServerBot plugin checkpoint browser**: Fixed Discord API error when more than 25 checkpoints exist
  - Previous error: `400 Bad Request - Must be between 1 and 25 in length` when dropdown exceeded Discord's 25-option limit
  - Implemented paginated browser with 20 checkpoints per page (safety margin)
  - Added type filters: Manual, Auto-backups, All
  - Added campaign filter dropdown (when multiple campaigns exist)
  - Pagination controls: Previous/Next buttons with page indicator
  - Applies to `/foothold-checkpoint list`, `/foothold-checkpoint delete`, and `/foothold-checkpoint restore` commands

### Improved
- **DCSServerBot plugin UI**: Enhanced checkpoint browser with advanced filtering
  - Filter by type: Manual checkpoints, Auto-backups, or All
  - Filter by campaign: Dropdown with all detected campaigns
  - Dynamic header showing active filters and result count
  - Example: `📦 **Showing 1-20 of 47 checkpoints** (Type: Manual, Campaign: afghanistan)`
  - Cleaner separation of manual saves vs automatic backups

## [2.1.0] - 2026-02-17

### Changed
- **DCSServerBot plugin UI simplified**: All Discord commands now use interactive-only mode
  - `/foothold-checkpoint save`: Only `server` parameter required (removed `campaign`, `name`, `comment`)
  - `/foothold-checkpoint restore`: Only `server` parameter required (removed `checkpoint`, `campaign`, `auto_backup`)
  - `/foothold-checkpoint list`: No parameters required (removed `campaign` filter)
  - `/foothold-checkpoint delete`: No parameters required (removed `checkpoint`, `campaign` filters)
  - Interactive selection now the only workflow - simpler and more consistent UX
  - Auto-backup always enabled for restore operations (safety first)
  - Metadata (name, comment) can be added via modal in interactive workflow

### Fixed
- **DCSServerBot plugin schema validation**: Added proper YAML schema file for configuration validation
  - Schema file: `schemas/foothold-checkpoint_schema.yaml` (pykwalify format)
  - Fixes "No schema files found" warning at plugin startup
  - Validates plugin configuration structure against expected format
- **Notification channel configuration**: Fixed channel field type from string to integer
  - `notifications.channel` now correctly accepts Discord channel ID (integer)
  - Updated schema, Pydantic model, and documentation to reflect channel ID requirement
  - Resolves schema validation error when using numeric channel IDs
- **Discord UI message cleanup**: Restore command now uses single updating message
  - Previous behavior: Multiple messages remained visible after completion
  - New behavior: Single message updates through selection → confirmation → result
  - Cleaner Discord interface with less clutter
- **Auto-backup visibility**: Restore success message now always shows backup creation status
  - Displays backup filename when available
  - Shows confirmation message when backup created but filename not returned
  - Ensures users are aware of safety backup before restoration

### Improved
- **Plugin build script**: Updated to include all file types from `schemas/` directory
  - Previously only included `.py` files
  - Now includes `.yaml` schema files required for validation
- **Documentation**: Updated plugin README and examples to reflect interactive-only workflow
  - Removed references to optional command parameters
  - Clarified that channel must be a Discord channel ID (integer)
  - Updated all command examples to show simplified syntax

## [2.0.0] - 2026-02-16

### Added
- **DCSServerBot plugin improvements**:
  - Plugin renamed to `foothold-checkpoint` for better identification
  - Plugin files reorganized into `src/foothold_checkpoint/plugin/` directory structure
  - Build script (`scripts/build_plugin.py`) updated to package plugin from organized structure
  - Plugin distribution ZIP includes all necessary files (config examples, campaigns example, README)
  - Documentation updated with DCSServerBot integration sections in README.md and USERS.md
  - **ARCHITECTURE: Plugin now uses DCSServerBot's Plugin base class**:
    - `FootholdCheckpoint` inherits from `Plugin[FootholdEventListener]` instead of `commands.Cog`
    - `FootholdEventListener` inherits from `EventListener` for DCS event integration
    - Plugin configuration automatically loaded via `self.locals` (DEFAULT section)
    - Server-specific config support via `self.get_config(server)` with automatic merge
    - Access to bot infrastructure: `self.log`, `self.pool`, `self.apool`, etc.
    - Follows DCSServerBot plugin conventions and best practices
  - **CONFIGURATION: Improved notification system**:
    - Channel accepts both numeric ID (recommended) or channel name (fallback)
    - Simplified notification toggles: `on_save`, `on_restore`, `on_delete`, `on_error`
    - Per-server notification channels via server-specific config sections
  - **DOCUMENTATION: Comprehensive plugin installation guide**:
    - Step-by-step activation via `opt_plugins` in `main.yaml` (critical first step)
    - Detailed configuration with DEFAULT and server-specific sections
    - Common troubleshooting scenarios and solutions
- **External campaigns configuration**: Campaigns can now be defined in separate `campaigns.yaml` file
  - Enables DRY configuration shared between CLI and DCSServerBot plugin
  - `campaigns_file` field in config.yaml references external campaigns file
  - `load_campaigns()` function loads and validates external campaigns
  - Backward compatible: inline campaigns still supported (mutually exclusive with campaigns_file)
  - Validation ensures at least one of campaigns or campaigns_file is provided

### Changed
- **BREAKING**: Config model changes for plugin support
  - `servers` field is now optional (`dict[str, ServerConfig] | None`) to support plugin mode
  - `campaigns` field is now optional when `campaigns_file` is specified
  - Cannot specify both `campaigns` and `campaigns_file` simultaneously
- **Config validation**: Enhanced error messages for configuration issues
  - Clear error when neither campaigns nor campaigns_file is provided
  - Error when both campaigns and campaigns_file are specified
  - Helpful guidance for migration to campaigns_file format

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
- **Checkpoint grouping and sorting**: Manual checkpoints and auto-backups are now separated for better UX
  - Manual checkpoints listed first, auto-backups listed last
  - Visual separator line ("AUTO-BACKUPS") in both CLI and Discord UI
  - Chronological sorting within each group (oldest first, newest last)
  - Dropdown menus show most recent checkpoint at the bottom for easier selection
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

[Unreleased]: https://github.com/VEAF/VEAF-foothold-checkpoint-tool/compare/v2.0.0...HEAD
[2.0.0]: https://github.com/VEAF/VEAF-foothold-checkpoint-tool/releases/tag/v2.0.0
[1.1.0]: https://github.com/VEAF/VEAF-foothold-checkpoint-tool/releases/tag/v1.1.0
[1.0.1]: https://github.com/VEAF/VEAF-foothold-checkpoint-tool/releases/tag/v1.0.1
[1.0.0]: https://github.com/VEAF/VEAF-foothold-checkpoint-tool/releases/tag/v1.0.0

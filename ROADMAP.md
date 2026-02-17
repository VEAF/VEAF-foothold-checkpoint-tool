# Roadmap

This document outlines the past, present, and future development of the VEAF Foothold Checkpoint Tool.

## Legend

- ✅ **Completed** - Feature is implemented and released
- 🚧 **In Progress** - Actively being developed
- 📋 **Planned** - Scheduled for future development
- 💡 **Proposed** - Under consideration, not yet committed

---

## Completed Releases

### ✅ v2.0.0 - DCSServerBot Plugin Integration (February 16, 2026)

**Status:** Released

**Key Features:**
- **DCSServerBot plugin** with full Discord UI integration
  - Plugin architecture using DCSServerBot's `Plugin` base class
  - Discord commands: `/foothold-checkpoint save`, `restore`, `list`, `delete`
  - Interactive UI with dropdowns and buttons
  - Per-server notification channels with configurable toggles
  - Comprehensive English and French documentation
- **External campaigns configuration** via separate `campaigns.yaml` file
  - Shared between CLI and plugin (DRY principle)
  - Backward compatible with inline campaigns
- **Checkpoint grouping and sorting**
  - Manual checkpoints listed first, auto-backups last
  - Visual separator ("AUTO-BACKUPS") in CLI and Discord
  - Chronological sorting (oldest first, newest last)
- **Configuration improvements**
  - Optional `servers` field (for plugin-only mode)
  - Optional `campaigns` field (when using `campaigns_file`)
  - Enhanced validation with helpful error messages

**Breaking Changes:**
- Configuration format migration required (same as v1.1.0)
- `servers` field now optional (for plugin mode)
- `campaigns` and `campaigns_file` are mutually exclusive

**Quality Metrics:**
- 306 tests (302 passing, 3 skipped)
- 46% overall coverage (core: 76-100%)
- Full mypy type checking
- Cross-platform support (Windows, Linux, macOS)

**Related:**
- OpenSpec change: `dcsserverbot-integration` (archived 2026-02-16)
- Plugin package: `foothold-checkpoint-plugin-v2.0.0.zip`
- GitHub Release: [v2.0.0](https://github.com/VEAF/VEAF-foothold-checkpoint-tool/releases/tag/v2.0.0)

---

### ✅ v1.1.0 - Explicit File Configuration (February 15, 2026)

**Status:** Released

**Key Features:**
- Explicit file list configuration (replaces regex-based pattern matching)
- Unknown file detection with auto-generated YAML snippets
- Auto-backup before restore operations
- Automatic file renaming on restore
- Enhanced list command with `--details` flag
- Improved error messages throughout

**Breaking Changes:**
- Configuration format migration required (see `MIGRATION_v1.1.0.md`)

**Quality Metrics:**
- 304 tests passing
- 95% code coverage
- Full mypy type checking
- Cross-platform support (Windows, Linux, macOS)

**Related:**
- OpenSpec change: `foothold-checkpoint-tool` (archived 2026-02-15)
- PR #19: Merged into develop
- GitHub Release: [v1.1.0](https://github.com/VEAF/VEAF-foothold-checkpoint-tool/releases/tag/v1.1.0)

---

### ✅ v1.0.1 - Cross-Platform Compatibility (February 14, 2026)

**Status:** Released

**Key Fixes:**
- Fixed campaign name restoration to use correct current name
- Linux/WSL compatibility improvements
- Platform-specific test handling
- Code quality improvements (ruff compliance)

**Quality Metrics:**
- 350 tests passing (3 skipped on Windows as expected)
- 83% code coverage

**Related:**
- GitHub Release: [v1.0.1](https://github.com/VEAF/VEAF-foothold-checkpoint-tool/releases/tag/v1.0.1)

---

### ✅ v1.0.0 - Initial Release (February 14, 2026)

**Status:** Released

**Key Features:**
- CLI tool for managing Foothold campaign checkpoints
- YAML-based configuration with Pydantic validation
- Campaign detection and file grouping
- Checkpoint operations: `save`, `restore`, `list`, `delete`, `import`
- SHA-256 integrity verification
- Cross-server checkpoint restoration
- Campaign name evolution tracking
- Rich terminal UI with progress indicators
- Interactive and command-line modes

**Core Capabilities:**
- Configuration management
- Campaign detection
- Checkpoint storage (ZIP format with metadata)
- Checkpoint restoration (with integrity verification)
- Checkpoint listing and filtering
- Checkpoint deletion with confirmation
- Manual backup import

**Quality Metrics:**
- 304 tests with comprehensive coverage
- mypy type checking
- Cross-platform support

**Related:**
- OpenSpec change: `foothold-checkpoint-tool` (initial implementation)
- GitHub Release: [v1.0.0](https://github.com/VEAF/VEAF-foothold-checkpoint-tool/releases/tag/v1.0.0)

---

## In Progress

### 🚧 v2.0.0 - DCSServerBot Integration

**Status:** In active development

**Completed Work:**
- ✅ Plugin structure reorganized into `src/foothold_checkpoint/plugin/` directory
- ✅ Plugin renamed to `foothold-checkpoint` for better identification  
- ✅ Build script created (`scripts/build_plugin.py`) for plugin distribution
- ✅ Plugin configuration examples (`foothold-checkpoint.yaml.example`, `campaigns.yaml.example`)
- ✅ Plugin documentation (`README.md` in plugin folder)
- ✅ Documentation updated (README.md and USERS.md) with DCSServerBot integration sections
- ✅ External campaigns configuration support (shared between CLI and plugin)

**Key Features (Implemented):**
- Native plugin for [DCSServerBot](https://github.com/Special-K-s-Flightsim-Bots/DCSServerBot)
- Discord slash commands for checkpoint operations (`/checkpoint save`, `/checkpoint restore`, `/checkpoint list`, `/checkpoint delete`)
- Role-based access control (administrator-only by default)
- Shared campaign configuration between CLI and plugin modes

**Next Steps:**
- Discord notifications for checkpoint events
- Enhanced error reporting in Discord
- Plugin testing and user feedback
- Documentation improvements based on usage

---

## Planned

### 💡 v2.1.0 - Webapp version

#### Web Dashboard
- Web-based UI for checkpoint management
- Visual timeline of checkpoints
- Checkpoint preview and metadata viewer
- Drag-and-drop restore interface
- Multi-server management dashboard

#### API and Integrations
- REST API for checkpoint operations
- Webhook support for external integrations
- Export/import API for third-party tools
- Prometheus metrics endpoint

**Breaking Changes:**
- Potential configuration format updates for plugin support
- API versioning and compatibility layer

---

### 📋 v2.2.0 - Enhanced Checkpoint Management

**Potential Features:**

#### Checkpoint Comparison
- `diff` command to compare two checkpoints
- Show file changes, additions, deletions
- Compare metadata and file hashes
- Visual diff output with color coding

#### Checkpoint Tagging and Metadata
- Add custom tags to checkpoints (e.g., `stable`, `v1.0-beta`, `pre-update`)
- Search/filter checkpoints by tags
- Enhanced metadata: add author, notes, linked issues
- Tag management commands (`tag add`, `tag remove`, `tag list`)

#### Improved List and Search
- Advanced filtering (date ranges, size ranges, tags)
- Sort options (by date, size, name, campaign)
- Text search in checkpoint names and comments
- Export checkpoint list to CSV/JSON

**Quality Goals:**
- Maintain 95%+ code coverage
- Full mypy compliance
- Performance benchmarks for large checkpoint repositories

---

### 📋 v2.3.0 - Automation and Scheduling

**Potential Features:**

#### Checkpoint Rotation
- Automatic cleanup of old checkpoints
- Retention policy configuration (time-based, count-based)
- Archive old checkpoints to cold storage
- Size-based cleanup (keep total storage under threshold)

#### Batch Operations
- `save-all` command to checkpoint all campaigns at once
- `restore-batch` to restore multiple checkpoints sequentially
- Progress reporting for batch operations
- Rollback on batch operation failure

#### Hooks and Scripts
- Pre/post-save hooks (e.g., stop DCS server before backup)
- Pre/post-restore hooks (e.g., restart server after restore)
- Custom validation scripts
- Integration with external monitoring tools

---

### 💡 Future Considerations (No Timeline)

**DCS Server Bot plugin enhancements**
- automatic scheduled backups

**Cloud Storage Integration**
- Upload checkpoints to S3, Azure Blob, Google Cloud Storage
- Automatic cloud backup on checkpoint creation
- Restore checkpoints from cloud storage
- Cost optimization (lifecycle policies, compression)

**Checkpoint Verification and Repair**
- `verify` command to check checkpoint integrity
- Detect corrupted files via checksums
- Repair corrupted checkpoints from redundant data
- Health check reports for checkpoint repository

**Documentation and Tooling**
- Interactive configuration wizard
- Video tutorials and documentation site
- Checkpoint migration tools (from other formats)
- Performance profiling and benchmarking tools

---

## Community Feedback

We welcome community input on our roadmap! Please open an issue on GitHub to:

- 👍 Vote on planned features
- 💬 Suggest new features or improvements
- 🐛 Report bugs or issues
- 📖 Request documentation improvements

**GitHub Issues:** https://github.com/VEAF/VEAF-foothold-checkpoint-tool/issues

---

## Release Cadence

- **Patch releases (v1.x.y)**: As needed for bug fixes
- **Minor releases (v1.x.0)**: Quarterly (approximately every 3 months)
- **Major releases (v2.0.0)**: Annually or when breaking changes are necessary

---

## Version History

| Version | Release Date | Type | Description |
|---------|--------------|------|-------------|
| v1.1.0  | 2026-02-15   | Minor | Explicit file configuration, auto-backup |
| v1.0.1  | 2026-02-14   | Patch | Cross-platform compatibility fixes |
| v1.0.0  | 2026-02-14   | Major | Initial release |

---

*Last Updated: February 15, 2026*

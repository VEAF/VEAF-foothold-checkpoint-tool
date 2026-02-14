## 1. Project Setup

- [x] 1.1 Create `pyproject.toml` with project metadata and dependencies
- [x] 1.2 Add runtime dependencies (typer, rich, pyyaml, pydantic)
- [x] 1.3 Add dev dependencies (pytest, ruff, black, mypy)
- [x] 1.4 Create `foothold_checkpoint/` package structure with `__init__.py`
- [x] 1.5 Create `foothold_checkpoint/core/` subpackage with `__init__.py`
- [x] 1.6 Create `tests/` directory structure matching package layout
- [x] 1.7 Create `CHANGELOG.md` following Keep a Changelog format
- [x] 1.8 Create `README.md` with project description and basic usage
- [x] 1.9 Create `config.yaml.example` with sample configuration

## 2. Configuration Management (core/config.py)

- [x] 2.1 Define Pydantic models for configuration (ServerConfig, Config)
- [x] 2.2 Write tests for Pydantic model validation
- [x] 2.3 Implement configuration loading from YAML file
- [x] 2.4 Write tests for config loading (valid, invalid YAML, invalid schema)
- [x] 2.5 Implement auto-creation of default config file
- [x] 2.6 Write tests for auto-creation (directory creation, default values)
- [x] 2.7 Implement config path expansion (tilde, environment variables)
- [x] 2.8 Write tests for path expansion
- [x] 2.9 Add config validation error messages with helpful context
- [x] 2.10 Write tests for error message clarity

## 3. Campaign Detection (core/campaign.py)

- [x] 3.1 Implement file pattern matching for campaign files
- [x] 3.2 Write tests for pattern matching (various prefixes, extensions)
- [x] 3.3 Implement version suffix normalization (regex patterns)
- [x] 3.4 Write tests for version normalization (_v0.2, _V0.1, _0.1, none)
- [x] 3.5 Implement campaign file grouping by normalized prefix
- [x] 3.6 Write tests for file grouping (complete, incomplete, mixed case)
- [x] 3.7 Implement Foothold_Ranks.lua recognition as shared file
- [x] 3.8 Write tests for shared file identification
- [x] 3.9 Implement campaign name mapping using config
- [x] 3.10 Write tests for name mapping (historical names, current names, unknown)
- [x] 3.11 Implement campaign detection report (name, file count)
- [x] 3.12 Write tests for detection reporting

## 4. Checkpoint Storage (core/checkpoint.py)

- [x] 4.1 Define checkpoint metadata structure (dataclass or Pydantic model)
- [x] 4.2 Write tests for metadata structure validation
- [x] 4.3 Implement SHA-256 checksum computation for files
- [x] 4.4 Write tests for checksum computation (small, large files)
- [x] 4.5 Implement metadata.json serialization
- [x] 4.6 Write tests for metadata serialization (all fields, optional fields)
- [x] 4.7 Implement checkpoint filename generation (campaign_YYYY-MM-DD_HH-MM-SS.zip)
- [x] 4.8 Write tests for filename generation (uniqueness, format)
- [x] 4.9 Implement ZIP archive creation with files and metadata
- [x] 4.10 Write tests for ZIP creation (single campaign, with/without ranks)
- [x] 4.11 Implement progress tracking for checkpoint creation
- [x] 4.12 Write tests for progress tracking callbacks

## 5. Checkpoint Storage Operations (core/storage.py)

- [x] 5.1 Implement save_checkpoint function (single campaign)
- [x] 5.2 Write tests for save_checkpoint (various scenarios)
- [x] 5.3 Implement save_all_campaigns function
- [x] 5.4 Write tests for save_all_campaigns (multiple campaigns, partial failures)
- [x] 5.5 Implement source directory validation
- [x] 5.6 Write tests for directory validation (exists, readable, permissions)
- [x] 5.7 Implement ZIP creation error handling (disk full, permissions)
- [x] 5.8 Write tests for error handling and cleanup
- [x] 5.9 Implement checkpoint storage directory creation
- [x] 5.10 Write tests for storage directory creation

## 6. Checkpoint Restoration (core/storage.py)

- [ ] 6.1 Implement restore_checkpoint function
- [ ] 6.2 Write tests for restore_checkpoint (basic restoration)
- [ ] 6.3 Implement ZIP validation (exists, readable, valid format)
- [ ] 6.4 Write tests for ZIP validation (missing, corrupted, invalid)
- [ ] 6.5 Implement metadata.json reading and parsing
- [ ] 6.6 Write tests for metadata parsing (valid, invalid JSON, missing)
- [ ] 6.7 Implement checksum verification before extraction
- [ ] 6.8 Write tests for checksum verification (match, mismatch, missing)
- [ ] 6.9 Implement Foothold_Ranks.lua exclusion by default
- [ ] 6.10 Write tests for ranks exclusion (default, with --restore-ranks)
- [ ] 6.11 Implement file renaming using latest campaign name
- [ ] 6.12 Write tests for file renaming (evolved names, unchanged names)
- [ ] 6.13 Implement overwrite confirmation prompt
- [ ] 6.14 Write tests for overwrite confirmation (empty dir, existing files)
- [ ] 6.15 Implement restoration progress tracking
- [ ] 6.16 Write tests for progress tracking
- [ ] 6.17 Implement restoration error handling
- [ ] 6.18 Write tests for error scenarios (disk full, permissions)

## 7. Checkpoint Listing (core/storage.py)

- [ ] 7.1 Implement list_checkpoints function
- [ ] 7.2 Write tests for list_checkpoints (basic listing)
- [ ] 7.3 Implement metadata reading without full extraction
- [ ] 7.4 Write tests for efficient metadata reading
- [ ] 7.5 Implement server filter
- [ ] 7.6 Write tests for server filtering
- [ ] 7.7 Implement campaign filter
- [ ] 7.8 Write tests for campaign filtering (including name mapping)
- [ ] 7.9 Implement combined filters (server + campaign)
- [ ] 7.10 Write tests for combined filtering
- [ ] 7.11 Implement chronological sorting (newest first)
- [ ] 7.12 Write tests for sorting
- [ ] 7.13 Implement file size calculation
- [ ] 7.14 Write tests for file size formatting (KB, MB, GB)
- [ ] 7.15 Implement error handling for corrupted checkpoints
- [ ] 7.16 Write tests for error handling (continue on corrupted)

## 8. Checkpoint Deletion (core/storage.py)

- [ ] 8.1 Implement delete_checkpoint function
- [ ] 8.2 Write tests for delete_checkpoint (basic deletion)
- [ ] 8.3 Implement checkpoint validation before deletion
- [ ] 8.4 Write tests for validation (exists, is ZIP, has metadata)
- [ ] 8.5 Implement metadata display before confirmation
- [ ] 8.6 Write tests for metadata display
- [ ] 8.7 Implement confirmation prompt
- [ ] 8.8 Write tests for confirmation (accept, cancel)
- [ ] 8.9 Implement force deletion (--force flag)
- [ ] 8.10 Write tests for force deletion
- [ ] 8.11 Implement deletion error handling (in use, permissions)
- [ ] 8.12 Write tests for error scenarios

## 9. Checkpoint Import (core/storage.py)

- [ ] 9.1 Implement import_checkpoint function
- [ ] 9.2 Write tests for import_checkpoint (basic import)
- [ ] 9.3 Implement source directory scanning
- [ ] 9.4 Write tests for directory scanning (single, multiple campaigns)
- [ ] 9.5 Implement campaign auto-detection from files
- [ ] 9.6 Write tests for auto-detection
- [ ] 9.7 Implement file validation with warnings
- [ ] 9.8 Write tests for validation warnings (missing files)
- [ ] 9.9 Implement import metadata collection
- [ ] 9.10 Write tests for metadata collection (from user input)
- [ ] 9.11 Implement checkpoint creation with current timestamp
- [ ] 9.12 Write tests for timestamp behavior
- [ ] 9.13 Implement checksum computation for imported files
- [ ] 9.14 Write tests for checksum computation
- [ ] 9.15 Implement original filename preservation
- [ ] 9.16 Write tests for filename preservation
- [ ] 9.17 Implement import error handling
- [ ] 9.18 Write tests for error scenarios (corrupted source, disk full)

## 10. CLI - Base Structure (cli.py)

- [ ] 10.1 Create Typer app instance with metadata
- [ ] 10.2 Write tests for CLI app initialization
- [ ] 10.3 Implement --version flag
- [ ] 10.4 Write tests for version display
- [ ] 10.5 Implement --config flag for custom config path
- [ ] 10.6 Write tests for custom config loading
- [ ] 10.7 Implement --quiet flag for suppressed output
- [ ] 10.8 Write tests for quiet mode
- [ ] 10.9 Implement Ctrl+C signal handler for graceful exit
- [ ] 10.10 Write tests for interrupt handling

## 11. CLI - Save Command (cli.py)

- [ ] 11.1 Implement save command with flags (--server, --campaign, --all, --name, --comment)
- [ ] 11.2 Write tests for save command with all flags
- [ ] 11.3 Implement server prompt when flag missing
- [ ] 11.4 Write tests for server prompt
- [ ] 11.5 Implement campaign prompt when flag missing
- [ ] 11.6 Write tests for campaign prompt (single, multiple, all)
- [ ] 11.7 Implement name/comment prompts
- [ ] 11.8 Write tests for optional metadata prompts
- [ ] 11.9 Implement progress display with Rich
- [ ] 11.10 Write tests for progress display
- [ ] 11.11 Implement success/error messages
- [ ] 11.12 Write tests for message display

## 12. CLI - Restore Command (cli.py)

- [ ] 12.1 Implement restore command with flags (checkpoint file, --server, --restore-ranks)
- [ ] 12.2 Write tests for restore command with all flags
- [ ] 12.3 Implement checkpoint selection prompt when missing
- [ ] 12.4 Write tests for checkpoint selection (list display, numbered selection)
- [ ] 12.5 Implement server prompt when flag missing
- [ ] 12.6 Write tests for server prompt
- [ ] 12.7 Implement confirmation prompt for overwrite
- [ ] 12.8 Write tests for overwrite confirmation
- [ ] 12.9 Implement progress display with Rich
- [ ] 12.10 Write tests for progress display
- [ ] 12.11 Implement success/error messages
- [ ] 12.12 Write tests for message display

## 13. CLI - List Command (cli.py)

- [ ] 13.1 Implement list command with filters (--server, --campaign)
- [ ] 13.2 Write tests for list command with various filters
- [ ] 13.3 Implement Rich table formatting
- [ ] 13.4 Write tests for table formatting
- [ ] 13.5 Implement timestamp formatting (human-readable)
- [ ] 13.6 Write tests for timestamp display
- [ ] 13.7 Implement file size formatting
- [ ] 13.8 Write tests for file size display
- [ ] 13.9 Implement empty results message
- [ ] 13.10 Write tests for empty results

## 14. CLI - Delete Command (cli.py)

- [ ] 14.1 Implement delete command with flags (checkpoint file, --force)
- [ ] 14.2 Write tests for delete command with/without force
- [ ] 14.3 Implement checkpoint selection in interactive mode
- [ ] 14.4 Write tests for interactive selection
- [ ] 14.5 Implement metadata display before confirmation
- [ ] 14.6 Write tests for metadata display
- [ ] 14.7 Implement confirmation prompt
- [ ] 14.8 Write tests for confirmation (accept, cancel)
- [ ] 14.9 Implement success/error messages
- [ ] 14.10 Write tests for message display

## 15. CLI - Import Command (cli.py)

- [ ] 15.1 Implement import command with flags (directory, --server, --campaign, --name, --comment)
- [ ] 15.2 Write tests for import command with all flags
- [ ] 15.3 Implement directory prompt when missing
- [ ] 15.4 Write tests for directory prompt
- [ ] 15.5 Implement campaign detection and selection
- [ ] 15.6 Write tests for campaign selection (auto-detect, multiple, user choice)
- [ ] 15.7 Implement metadata prompts (server, name, comment)
- [ ] 15.8 Write tests for metadata prompts
- [ ] 15.9 Implement import summary display
- [ ] 15.10 Write tests for summary display
- [ ] 15.11 Implement confirmation prompt
- [ ] 15.12 Write tests for confirmation
- [ ] 15.13 Implement progress display
- [ ] 15.14 Write tests for progress display
- [ ] 15.15 Implement success/error messages with warnings
- [ ] 15.16 Write tests for message display

## 16. CLI - Error Handling (cli.py)

- [ ] 16.1 Implement user-friendly error messages for common scenarios
- [ ] 16.2 Write tests for error messages (server not found, campaign not found)
- [ ] 16.3 Implement file not found error handling
- [ ] 16.4 Write tests for file errors
- [ ] 16.5 Implement permission error handling
- [ ] 16.6 Write tests for permission errors
- [ ] 16.7 Implement validation for conflicting flags
- [ ] 16.8 Write tests for flag validation

## 17. Plugin Structure Preparation (plugin/)

- [ ] 17.1 Create `plugin/` directory structure
- [ ] 17.2 Create `plugin/__init__.py`
- [ ] 17.3 Create `plugin/commands.py` with DCSServerBot plugin skeleton
- [ ] 17.4 Document plugin integration points in README
- [ ] 17.5 Add comments in plugin code referencing DCSServerBot architecture

## 18. Documentation

- [ ] 18.1 Write comprehensive README with installation instructions
- [ ] 18.2 Add usage examples for all commands
- [ ] 18.3 Document configuration file format and options
- [ ] 18.4 Add troubleshooting section
- [ ] 18.5 Document development setup (venv, testing)
- [ ] 18.6 Add contributing guidelines
- [ ] 18.7 Update CHANGELOG.md with initial version

## 19. Integration Testing

- [ ] 19.1 Create end-to-end test for save → list → restore workflow
- [ ] 19.2 Create end-to-end test for import workflow
- [ ] 19.3 Create end-to-end test for delete workflow
- [ ] 19.4 Test with real data from `tests/data/foothold/`
- [ ] 19.5 Test cross-server restoration
- [ ] 19.6 Test all campaigns save/restore
- [ ] 19.7 Test error scenarios (disk full, permissions)
- [ ] 19.8 Test Windows-specific paths and behaviors

## 20. Quality Assurance

- [ ] 20.1 Run ruff linter and fix all issues
- [ ] 20.2 Run black formatter on all Python files
- [ ] 20.3 Run mypy type checker and resolve type errors
- [ ] 20.4 Ensure all tests pass
- [ ] 20.5 Achieve 100% test coverage for core modules
- [ ] 20.6 Verify no VS Code errors or warnings
- [ ] 20.7 Review and update CHANGELOG.md
- [ ] 20.8 Perform manual testing of interactive mode
- [ ] 20.9 Test quiet mode for automation
- [ ] 20.10 Validate against development guidelines

## 21. Release Preparation

- [ ] 21.1 Confirm version number follows semantic versioning
- [ ] 21.2 Update version in `pyproject.toml`
- [ ] 21.3 Update version in `__init__.py`
- [ ] 21.4 Finalize CHANGELOG.md for release
- [ ] 21.5 Create release notes
- [ ] 21.6 Tag release in git
- [ ] 21.7 Test installation from package
- [ ] 21.8 Verify all commands work in clean environment

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

- [x] 6.1 Implement restore_checkpoint function
- [x] 6.2 Write tests for restore_checkpoint (basic restoration)
- [x] 6.3 Implement ZIP validation (exists, readable, valid format)
- [x] 6.4 Write tests for ZIP validation (missing, corrupted, invalid)
- [x] 6.5 Implement metadata.json reading and parsing
- [x] 6.6 Write tests for metadata parsing (valid, invalid JSON, missing)
- [x] 6.7 Implement checksum verification before extraction
- [x] 6.8 Write tests for checksum verification (match, mismatch, missing)
- [x] 6.9 Implement Foothold_Ranks.lua exclusion by default
- [x] 6.10 Write tests for ranks exclusion (default, with --restore-ranks)
- [ ] 6.11 Implement file renaming using latest campaign name
- [ ] 6.12 Write tests for file renaming (evolved names, unchanged names)
- [x] 6.13 Implement overwrite confirmation prompt
- [x] 6.14 Write tests for overwrite confirmation (empty dir, existing files)
- [x] 6.15 Implement restoration progress tracking
- [x] 6.16 Write tests for progress tracking
- [x] 6.17 Implement restoration error handling
- [x] 6.18 Write tests for error scenarios (disk full, permissions)

## 7. Checkpoint Listing (core/storage.py)

- [x] 7.1 Implement list_checkpoints function
- [x] 7.2 Write tests for list_checkpoints (basic listing)
- [x] 7.3 Implement metadata reading without full extraction
- [x] 7.4 Write tests for efficient metadata reading
- [x] 7.5 Implement server filter
- [x] 7.6 Write tests for server filtering
- [x] 7.7 Implement campaign filter
- [x] 7.8 Write tests for campaign filtering (including name mapping)
- [x] 7.9 Implement combined filters (server + campaign)
- [x] 7.10 Write tests for combined filtering
- [x] 7.11 Implement chronological sorting (newest first)
- [x] 7.12 Write tests for sorting
- [x] 7.13 Implement file size calculation
- [x] 7.14 Write tests for file size formatting (KB, MB, GB)
- [x] 7.15 Implement error handling for corrupted checkpoints
- [x] 7.16 Write tests for error handling (continue on corrupted)

## 8. Checkpoint Deletion (core/storage.py)

- [x] 8.1 Implement delete_checkpoint function
- [x] 8.2 Write tests for delete_checkpoint (basic deletion)
- [x] 8.3 Implement checkpoint validation before deletion
- [x] 8.4 Write tests for validation (exists, is ZIP, has metadata)
- [x] 8.5 Implement metadata display before confirmation
- [x] 8.6 Write tests for metadata display
- [x] 8.7 Implement confirmation prompt
- [x] 8.8 Write tests for confirmation (accept, cancel)
- [x] 8.9 Implement force deletion (--force flag)
- [x] 8.10 Write tests for force deletion
- [x] 8.11 Implement deletion error handling (in use, permissions)
- [x] 8.12 Write tests for error scenarios

## 9. Checkpoint Import (core/storage.py)

- [x] 9.1 Implement import_checkpoint function
- [x] 9.2 Write tests for import_checkpoint (basic import)
- [x] 9.3 Implement source directory scanning
- [x] 9.4 Write tests for directory scanning (single, multiple campaigns)
- [x] 9.5 Implement campaign auto-detection from files
- [x] 9.6 Write tests for auto-detection
- [x] 9.7 Implement file validation with warnings
- [x] 9.8 Write tests for validation warnings (missing files)
- [x] 9.9 Implement import metadata collection
- [x] 9.10 Write tests for metadata collection (from user input)
- [x] 9.11 Implement checkpoint creation with current timestamp
- [x] 9.12 Write tests for timestamp behavior
- [x] 9.13 Implement checksum computation for imported files
- [x] 9.14 Write tests for checksum computation
- [x] 9.15 Implement original filename preservation
- [x] 9.16 Write tests for filename preservation
- [x] 9.17 Implement import error handling
- [x] 9.18 Write tests for error scenarios (corrupted source, disk full)

## 10. CLI - Base Structure (cli.py)

- [x] 10.1 Create Typer app instance with metadata
- [x] 10.2 Write tests for CLI app initialization
- [x] 10.3 Implement --version flag
- [x] 10.4 Write tests for version display
- [x] 10.5 Implement --config flag for custom config path
- [x] 10.6 Write tests for custom config loading
- [x] 10.7 Implement --quiet flag for suppressed output
- [x] 10.8 Write tests for quiet mode
- [x] 10.9 Implement Ctrl+C signal handler for graceful exit
- [x] 10.10 Write tests for interrupt handling

## 11. CLI - Save Command (cli.py)

- [x] 11.1 Implement save command with flags (--server, --campaign, --all, --name, --comment)
- [x] 11.2 Write tests for save command with all flags
- [x] 11.3 Implement server prompt when flag missing
- [x] 11.4 Write tests for server prompt
- [x] 11.5 Implement campaign prompt when flag missing
- [x] 11.6 Write tests for campaign prompt (single, multiple, all)
- [x] 11.7 Implement name/comment prompts
- [x] 11.8 Write tests for optional metadata prompts
- [x] 11.9 Implement progress display with Rich
- [x] 11.10 Write tests for progress display
- [x] 11.11 Implement success/error messages
- [x] 11.12 Write tests for message display

## 12. CLI - Restore Command (cli.py)

- [x] 12.1 Implement restore command with flags (checkpoint file, --server, --restore-ranks)
- [x] 12.2 Write tests for restore command with all flags
- [x] 12.3 Implement checkpoint selection prompt when missing
- [x] 12.4 Write tests for checkpoint selection (list display, numbered selection)
- [x] 12.5 Implement server prompt when flag missing
- [x] 12.6 Write tests for server prompt
- [x] 12.7 Implement confirmation prompt for overwrite
- [x] 12.8 Write tests for overwrite confirmation
- [x] 12.9 Implement progress display with Rich
- [x] 12.10 Write tests for progress display
- [x] 12.11 Implement success/error messages
- [x] 12.12 Write tests for message display

## 13. CLI - List Command (cli.py)

- [x] 13.1 Implement list command with filters (--server, --campaign)
- [x] 13.2 Write tests for list command with various filters
- [x] 13.3 Implement Rich table formatting
- [x] 13.4 Write tests for table formatting
- [x] 13.5 Implement timestamp formatting (human-readable)
- [x] 13.6 Write tests for timestamp display
- [x] 13.7 Implement file size formatting
- [x] 13.8 Write tests for file size display
- [x] 13.9 Implement empty results message
- [x] 13.10 Write tests for empty results

## 14. CLI - Delete Command (cli.py)

- [x] 14.1 Implement delete command with flags (checkpoint file, --force)
- [x] 14.2 Write tests for delete command with/without force
- [x] 14.3 Implement checkpoint selection in interactive mode
- [x] 14.4 Write tests for interactive selection
- [x] 14.5 Implement metadata display before confirmation
- [x] 14.6 Write tests for metadata display
- [x] 14.7 Implement confirmation prompt
- [x] 14.8 Write tests for confirmation (accept, cancel)
- [x] 14.9 Implement success/error messages
- [x] 14.10 Write tests for message display

## 15. CLI - Import Command (cli.py)

- [x] 15.1 Implement import command with flags (directory, --server, --campaign, --name, --comment)
- [x] 15.2 Write tests for import command with all flags
- [x] 15.3 Implement directory prompt when missing
- [x] 15.4 Write tests for directory prompt
- [x] 15.5 Implement campaign detection and selection
- [x] 15.6 Write tests for campaign selection (auto-detect, multiple, user choice)
- [x] 15.7 Implement metadata prompts (server, name, comment)
- [x] 15.8 Write tests for metadata prompts
- [x] 15.9 Implement import summary display
- [x] 15.10 Write tests for summary display
- [x] 15.11 Implement confirmation prompt
- [x] 15.12 Write tests for confirmation
- [x] 15.13 Implement progress display
- [x] 15.14 Write tests for progress display
- [x] 15.15 Implement success/error messages with warnings
- [x] 15.16 Write tests for message display

## 16. CLI - Error Handling (cli.py)

- [x] 16.1 Implement user-friendly error messages for common scenarios
- [x] 16.2 Write tests for error messages (server not found, campaign not found)
- [x] 16.3 Implement file not found error handling
- [x] 16.4 Write tests for file errors
- [x] 16.5 Implement permission error handling
- [x] 16.6 Write tests for permission errors
- [x] 16.7 Implement validation for conflicting flags
- [x] 16.8 Write tests for flag validation

## 17. Plugin Structure Preparation (plugin/)

- [x] 17.1 Create `plugin/` directory structure
- [x] 17.2 Create `plugin/__init__.py`
- [x] 17.3 Create `plugin/commands.py` with DCSServerBot plugin skeleton
- [x] 17.4 Document plugin integration points in README
- [x] 17.5 Add comments in plugin code referencing DCSServerBot architecture

## 18. Documentation

- [x] 18.1 Write comprehensive README with installation instructions
- [x] 18.2 Add usage examples for all commands
- [x] 18.3 Document configuration file format and options
- [x] 18.4 Add troubleshooting section
- [x] 18.5 Document development setup (venv, testing)
- [x] 18.6 Add contributing guidelines
- [ ] 18.7 Update CHANGELOG.md with initial version

## 19. Integration Testing

- [x] 19.1 Create end-to-end test for save → list → restore workflow
- [x] 19.2 Create end-to-end test for import workflow
- [x] 19.3 Create end-to-end test for delete workflow
- [ ] 19.4 Test with real data from `tests/data/foothold/`
- [x] 19.5 Test cross-server restoration
- [x] 19.6 Test all campaigns save/restore
- [x] 19.7 Test error scenarios (disk full, permissions)
- [x] 19.8 Test Windows-specific paths and behaviors

## 20. Quality Assurance

- [x] 20.1 Run ruff linter and fix all issues
- [ ] 20.2 Run black formatter on all Python files
- [ ] 20.3 Run mypy type checker and resolve type errors
- [x] 20.4 Ensure all tests pass
- [x] 20.5 Achieve 100% test coverage for core modules
- [ ] 20.6 Verify no VS Code errors or warnings
- [ ] 20.7 Review and update CHANGELOG.md
- [ ] 20.8 Perform manual testing of interactive mode
- [ ] 20.9 Test quiet mode for automation
- [x] 20.10 Validate against development guidelines

## 21. Release Preparation

- [ ] 21.1 Confirm version number follows semantic versioning
- [ ] 21.2 Update version in `pyproject.toml`
- [ ] 21.3 Update version in `__init__.py`
- [ ] 21.4 Finalize CHANGELOG.md for release
- [ ] 21.5 Create release notes
- [ ] 21.6 Tag release in git
- [ ] 21.7 Test installation from package
- [ ] 21.8 Verify all commands work in clean environment

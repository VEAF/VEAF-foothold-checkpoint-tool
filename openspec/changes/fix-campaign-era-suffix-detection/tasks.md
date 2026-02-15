## 1. Update Configuration Schema

- [x] 1.1 Add CampaignFileList Pydantic model with file type categories (persistence, ctld_save, ctld_farps, storage)
- [x] 1.2 Add optional flag support for file types in CampaignFileList model
- [x] 1.3 Update CampaignConfig model to use new file list structure instead of name list
- [x] 1.4 Add display_name field to CampaignConfig for user-friendly campaign names
- [x] 1.5 Update Config model validation to ensure at least one file per required type
- [x] 1.6 Update config.yaml.example with new structure and comprehensive examples
- [x] 1.7 Add validation tests for new config schema structure

## 2. Update Campaign Detection Logic

- [x] 2.1 Create build_file_to_campaign_map() function to create reverse lookup from all configured files
- [x] 2.2 Rewrite detect_campaigns() to use file-to-campaign lookup instead of regex matching
- [x] 2.3 Add detect_unknown_files() function to identify unconfigured foothold-like files
- [x] 2.4 Update group_campaign_files() to use configuration-based matching
- [x] 2.5 Remove normalize_campaign_name() function (no longer needed)
- [x] 2.6 Remove CAMPAIGN_FILE_PATTERN regex constant
- [x] 2.7 Keep is_shared_file() for Foothold_Ranks.lua detection (unchanged)
- [x] 2.8 Update create_campaign_report() to use new detection logic

## 3. Add Unknown File Detection

- [ ] 3.1 Create generate_config_suggestion() function to create example YAML snippet for unknown files
- [ ] 3.2 Add format_unknown_files_error() to create helpful error messages
- [ ] 3.3 Update import_command() to call detect_unknown_files() and fail with guidance
- [ ] 3.4 Add tests for unknown file detection with various patterns
- [ ] 3.5 Add tests verifying error messages include config suggestions

## 4. Add Auto-Backup Before Restore

- [ ] 4.1 Create create_auto_backup() helper function in storage.py
- [ ] 4.2 Generate auto-backup checkpoint name with UTC timestamp format
- [ ] 4.3 Add auto-backup metadata with descriptive comment
- [ ] 4.4 Integrate create_auto_backup() into restore_checkpoint() before file operations
- [ ] 4.5 Handle auto-backup failure cases (disk space, permissions) with clear errors
- [ ] 4.6 Add tests for auto-backup creation during restore
- [ ] 4.7 Add tests for auto-backup failure scenarios
- [ ] 4.8 Verify auto-backup checkpoint is valid and can be restored

## 5. Update CLI Error Messages

- [ ] 5.1 Update import command campaign selection error messages to use display names
- [ ] 5.2 Add helpful suggestions when campaign not found in CLI
- [ ] 5.3 Update campaign detection messages to reference config file structure
- [ ] 5.4 Add progress indicators for auto-backup creation during restore
- [ ] 5.5 Update --help text for import and restore commands with new behavior notes

## 6. Update Tests

- [ ] 6.1 Update test_campaign.py with new config structure fixtures
- [ ] 6.2 Rewrite campaign detection tests to use explicit file lists
- [ ] 6.3 Add tests for files with era suffixes grouping correctly
- [ ] 6.4 Update test_cli_import.py for new detection behavior
- [ ] 6.5 Add tests for missing optional vs required files
- [ ] 6.6 Update test_config.py with new validation rules
- [ ] 6.7 Add integration tests for auto-backup before restore
- [ ] 6.8 Update all test data config files to new format
- [ ] 6.9 Verify all existing tests still pass with new logic

## 7. Documentation and Examples

- [ ] 7.1 Create MIGRATION.md guide for updating config.yaml from old to new format
- [ ] 7.2 Add example config snippets showing multiple file names per type
- [ ] 7.3 Document optional flag usage in README or config example
- [ ] 7.4 Add auto-backup behavior documentation to README
- [ ] 7.5 Update CHANGELOG.md with breaking changes notice
- [ ] 7.6 Document unknown file error messages and resolution steps
- [ ] 7.7 Add examples for common campaign configurations (Afghanistan, Caucasus, etc.)

## 8. Validation and Cleanup

- [ ] 8.1 Run full test suite and verify all tests pass
- [ ] 8.2 Test import command with real backup directories
- [ ] 8.3 Test restore command and verify auto-backup creation
- [ ] 8.4 Verify error messages are clear and helpful
- [ ] 8.5 Remove dead code from old regex-based detection
- [ ] 8.6 Update type hints and docstrings for modified functions
- [ ] 8.7 Run linting and formatting checks (ruff, black, mypy)
- [ ] 8.8 Verify no VS Code errors or warnings

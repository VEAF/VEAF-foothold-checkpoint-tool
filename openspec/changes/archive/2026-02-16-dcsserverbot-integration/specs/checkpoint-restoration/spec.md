## MODIFIED Requirements

### Requirement: System SHALL restore checkpoint files to target server directory

The system SHALL extract checkpoint files from the ZIP archive and copy them to the specified target server's Saves directory. The system SHALL support optional event hooks for Discord progress updates.

#### Scenario: Restore to specified server
- **WHEN** user restores a checkpoint to server "test-server"
- **THEN** files are extracted to the path configured for "test-server" in config.yaml

#### Scenario: Target directory does not exist
- **WHEN** user attempts to restore to a non-existent target directory
- **THEN** the system displays an error and aborts restoration

#### Scenario: Target directory not writable
- **WHEN** user attempts to restore to a directory without write permissions
- **THEN** the system displays a permissions error and aborts restoration

#### Scenario: Event hooks trigger on restore start
- **WHEN** checkpoint restore operation starts and hooks.on_restore_start is provided
- **THEN** system calls await hooks.on_restore_start(checkpoint_name, campaign) before file operations

#### Scenario: Event hooks trigger on restore progress
- **WHEN** checkpoint restoration is in progress and hooks.on_restore_progress is provided
- **THEN** system calls await hooks.on_restore_progress(current_file, total_files) during extraction

#### Scenario: Event hooks trigger on restore complete
- **WHEN** checkpoint restore completes successfully and hooks.on_restore_complete is provided
- **THEN** system calls await hooks.on_restore_complete(restored_files) with list of restored files

#### Scenario: Event hooks trigger on error
- **WHEN** checkpoint restore fails with exception and hooks.on_error is provided
- **THEN** system calls await hooks.on_error(exception) before re-raising

#### Scenario: Restore without event hooks
- **WHEN** checkpoint is restored with hooks=None (CLI mode)
- **THEN** system restores checkpoint normally without calling any callbacks

## ADDED Requirements

### Requirement: System SHALL create automatic backup before restore

The system SHALL create a backup checkpoint of the current campaign state before restoring a different checkpoint, unless explicitly disabled.

#### Scenario: Auto-backup enabled by default
- **WHEN** user restores a checkpoint without --no-auto-backup flag
- **THEN** system creates backup of current state before restoration

#### Scenario: Auto-backup naming convention
- **WHEN** auto-backup is created before restore
- **THEN** backup filename is {campaign}_backup_{YYYY-MM-DD_HH-MM-SS}.zip

#### Scenario: Auto-backup includes metadata reference
- **WHEN** auto-backup is created
- **THEN** metadata.json includes comment field: "Auto-backup before restore of {checkpoint_name}"

#### Scenario: Auto-backup failure aborts restore
- **WHEN** auto-backup creation fails
- **THEN** system displays error and aborts restore without modifying target

#### Scenario: Auto-backup disabled flag
- **WHEN** user restores checkpoint with --no-auto-backup flag
- **THEN** system skips auto-backup and proceeds directly to restore

#### Scenario: Auto-backup success notification
- **WHEN** auto-backup completes successfully and hooks.on_backup_complete is provided
- **THEN** system calls await hooks.on_backup_complete(backup_path)

### Requirement: System SHALL support async restore operation

The system SHALL implement restore operation as async function supporting concurrent operations and non-blocking execution.

#### Scenario: Restore function is async
- **WHEN** restore_checkpoint is defined
- **THEN** function signature is async def restore_checkpoint(...) -> RestoreResult

#### Scenario: Async file operations
- **WHEN** restoring checkpoint files
- **THEN** system uses async file I/O operations (aiofiles) when available

#### Scenario: Concurrent verification and extraction
- **WHEN** files are being verified and extracted
- **THEN** system can perform verification and extraction concurrently for performance

#### Scenario: Non-blocking progress updates
- **WHEN** restore is in progress with event hooks
- **THEN** progress callbacks do not block restore operation

#### Scenario: CLI wraps async with asyncio.run
- **WHEN** CLI calls restore operation
- **THEN** CLI uses asyncio.run(restore_checkpoint(...)) to execute async function

## ADDED Requirements

### Requirement: System SHALL create automatic backup before restoration

The system SHALL automatically create a checkpoint backup of existing campaign files before restoring a checkpoint.

#### Scenario: Automatic backup before restore
- **WHEN** user restores a checkpoint to a server with existing campaign files
- **THEN** the system creates an auto-backup checkpoint with timestamp before proceeding with restoration

#### Scenario: Auto-backup naming convention
- **WHEN** system creates automatic backup
- **THEN** checkpoint is named `auto-backup-YYYYMMDD-HHMMSS` with timestamp in UTC

#### Scenario: Auto-backup metadata
- **WHEN** system creates automatic backup
- **THEN** metadata includes comment: "Automatic backup before restoring {checkpoint_name}"

#### Scenario: Auto-backup uses checkpoint format
- **WHEN** system creates automatic backup
- **THEN** backup uses the same ZIP checkpoint format as manual saves

#### Scenario: Auto-backup failure aborts restore
- **WHEN** automatic backup creation fails (e.g., insufficient disk space, permissions)
- **THEN** system displays error and aborts restoration without modifying target files

#### Scenario: No existing campaign files
- **WHEN** user restores to a server with no existing campaign files
- **THEN** system still creates an empty auto-backup checkpoint for consistency

### Requirement: System SHALL verify file integrity before restoration

The system SHALL verify SHA-256 checksums of all files in the checkpoint against metadata before extracting any files.

#### Scenario: All checksums match
- **WHEN** all files in the checkpoint have matching checksums in metadata
- **THEN** the system proceeds with restoration

#### Scenario: Checksum mismatch detected
- **WHEN** one or more files have checksums that do not match metadata
- **THEN** the system displays an error listing corrupted files and aborts restoration

#### Scenario: Missing checksum in metadata
- **WHEN** metadata.json is missing checksum for a file in the ZIP
- **THEN** the system displays a warning and asks user to confirm restoration

#### Scenario: Progress during verification
- **WHEN** verifying checksums for multiple files
- **THEN** the system displays progress (e.g., "Verifying: 3/5 files")

### Requirement: System SHALL restore checkpoint files to target server directory

The system SHALL extract checkpoint files from the ZIP archive and copy them to the specified target server's Saves directory.

#### Scenario: Restore to specified server
- **WHEN** user restores a checkpoint to server "test-server"
- **THEN** files are extracted to the path configured for "test-server" in config.yaml

#### Scenario: Target directory does not exist
- **WHEN** user attempts to restore to a non-existent target directory
- **THEN** the system displays an error and aborts restoration

#### Scenario: Target directory not writable
- **WHEN** user attempts to restore to a directory without write permissions
- **THEN** the system displays a permissions error and aborts restoration

### Requirement: System SHALL NOT restore Foothold_Ranks.lua by default

The system SHALL exclude `Foothold_Ranks.lua` from restoration unless the user explicitly requests it via the `--restore-ranks` flag.

#### Scenario: Default restoration excludes ranks file
- **WHEN** user restores a checkpoint without the `--restore-ranks` flag
- **THEN** all campaign files are restored but Foothold_Ranks.lua is skipped

#### Scenario: Explicit ranks restoration
- **WHEN** user restores a checkpoint with the `--restore-ranks` flag
- **THEN** Foothold_Ranks.lua is restored along with campaign files

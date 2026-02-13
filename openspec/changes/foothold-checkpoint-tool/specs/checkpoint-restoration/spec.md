## ADDED Requirements

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

### Requirement: System SHALL NOT restore Foothold_Ranks.lua by default

The system SHALL exclude `Foothold_Ranks.lua` from restoration unless the user explicitly requests it via the `--restore-ranks` flag.

#### Scenario: Default restoration excludes ranks file
- **WHEN** user restores a checkpoint without the `--restore-ranks` flag
- **THEN** all campaign files are restored but Foothold_Ranks.lua is skipped

#### Scenario: Explicit ranks restoration
- **WHEN** user restores a checkpoint with the `--restore-ranks` flag
- **THEN** Foothold_Ranks.lua is restored along with campaign files

#### Scenario: Ranks file not in checkpoint
- **WHEN** user restores a checkpoint with `--restore-ranks` but the ZIP lacks Foothold_Ranks.lua
- **THEN** the system displays a warning that ranks file is not available

### Requirement: System SHALL support cross-server restoration

The system SHALL allow restoring a checkpoint created from one server to a different server's directory.

#### Scenario: Restore from prod to test server
- **WHEN** user restores a checkpoint with metadata server="prod-1" to target server="test-server"
- **THEN** files are extracted to test-server's path successfully

#### Scenario: Metadata displays source server
- **WHEN** restoring a checkpoint from a different server
- **THEN** the system displays the source server name from metadata before restoration

### Requirement: System SHALL rename files using latest campaign name

The system SHALL use the latest (current) campaign name from configuration when restoring files, renaming if necessary.

#### Scenario: Campaign name evolved
- **WHEN** restoring a checkpoint with files named `GCW_Modern_V0.1.lua` and config maps `Germany_Modern: [GCW_Modern, Germany_Modern]`
- **THEN** files are restored with the latest name prefix `Germany_Modern`

#### Scenario: Campaign name unchanged
- **WHEN** restoring a checkpoint where campaign name has not evolved
- **THEN** files are restored with their original names

#### Scenario: Version suffix added to latest name
- **WHEN** restoring files and the latest campaign name has a version (e.g., `Germany_Modern_V0.2`)
- **THEN** files are restored with the current version suffix

### Requirement: System SHALL prompt for confirmation before overwriting files

The system SHALL warn the user if restoration will overwrite existing files in the target directory and require confirmation.

#### Scenario: Target directory is empty
- **WHEN** restoring to an empty target directory
- **THEN** the system proceeds without confirmation prompt

#### Scenario: Target directory has existing campaign files
- **WHEN** restoring to a directory that already contains files for the same campaign
- **THEN** the system prompts "Files will be overwritten. Continue? (y/n)" and waits for user input

#### Scenario: User confirms overwrite
- **WHEN** user confirms the overwrite prompt with "y"
- **THEN** the system proceeds with restoration, overwriting existing files

#### Scenario: User cancels overwrite
- **WHEN** user cancels the overwrite prompt with "n"
- **THEN** the system aborts restoration and displays "Restoration cancelled"

### Requirement: System SHALL display restoration progress

The system SHALL show progress feedback during restoration using Rich progress bars.

#### Scenario: Progress for file extraction
- **WHEN** extracting files from a checkpoint
- **THEN** the system displays a progress bar showing extraction progress (e.g., "Extracting: 3/5 files")

#### Scenario: Completion message
- **WHEN** restoration completes successfully
- **THEN** the system displays "Checkpoint restored successfully to {server}"

### Requirement: System SHALL validate checkpoint file before restoration

The system SHALL verify that the checkpoint ZIP file exists, is readable, and contains valid metadata.json before attempting restoration.

#### Scenario: Checkpoint file does not exist
- **WHEN** user attempts to restore a non-existent checkpoint file
- **THEN** the system displays "Checkpoint file not found" and aborts

#### Scenario: Checkpoint file is not a valid ZIP
- **WHEN** user attempts to restore a file that is not a valid ZIP archive
- **THEN** the system displays "Invalid checkpoint file (not a ZIP archive)" and aborts

#### Scenario: Checkpoint missing metadata.json
- **WHEN** a checkpoint ZIP does not contain metadata.json
- **THEN** the system displays "Invalid checkpoint (missing metadata)" and aborts

#### Scenario: Metadata.json has invalid JSON syntax
- **WHEN** metadata.json in the checkpoint has invalid JSON syntax
- **THEN** the system displays a JSON parse error and aborts

### Requirement: System SHALL handle restoration failures gracefully

The system SHALL detect restoration failures (disk full, permissions, corruption) and avoid leaving the target directory in an inconsistent state.

#### Scenario: Disk full during restoration
- **WHEN** disk space runs out during file extraction
- **THEN** the system displays an error and halts restoration (partial files may exist)

#### Scenario: Permission error during extraction
- **WHEN** a file cannot be written due to permissions
- **THEN** the system displays which file failed and aborts restoration

#### Scenario: Restoration interrupted
- **WHEN** restoration is interrupted (e.g., Ctrl+C)
- **THEN** the system displays "Restoration interrupted" and warns about potential incomplete state

## ADDED Requirements

### Requirement: System SHALL delete checkpoint files by filename

The system SHALL delete checkpoint ZIP files from the storage directory when requested by the user.

#### Scenario: Delete existing checkpoint
- **WHEN** user deletes a checkpoint file "afghanistan_2024-02-13_14-30-00.zip" that exists
- **THEN** the system removes the file from the checkpoint storage directory

#### Scenario: Delete non-existent checkpoint
- **WHEN** user attempts to delete a checkpoint file that does not exist
- **THEN** the system displays "Checkpoint file not found: {filename}" and aborts

#### Scenario: Checkpoint file is read-only
- **WHEN** user attempts to delete a read-only checkpoint file
- **THEN** the system displays a permissions error

### Requirement: System SHALL require confirmation before deleting

The system SHALL prompt the user for confirmation before permanently deleting a checkpoint file.

#### Scenario: Confirmation prompt displayed
- **WHEN** user requests to delete a checkpoint
- **THEN** the system displays metadata (server, campaign, date, name) and asks "Delete this checkpoint? (y/n)"

#### Scenario: User confirms deletion
- **WHEN** user confirms deletion with "y"
- **THEN** the system deletes the checkpoint and displays "Checkpoint deleted successfully"

#### Scenario: User cancels deletion
- **WHEN** user cancels deletion with "n"
- **THEN** the system aborts and displays "Deletion cancelled"

#### Scenario: Interactive mode shows checkpoint details
- **WHEN** deleting in interactive mode
- **THEN** the system displays full checkpoint metadata before prompting for confirmation

### Requirement: System SHALL support force deletion without confirmation

The system SHALL allow bypassing the confirmation prompt via a `--force` flag for automated workflows.

#### Scenario: Force delete without prompt
- **WHEN** user runs `foothold-checkpoint delete {filename} --force`
- **THEN** the checkpoint is deleted immediately without prompting

#### Scenario: Force delete non-existent file
- **WHEN** user force-deletes a non-existent checkpoint
- **THEN** the system displays an error (no silent failures)

### Requirement: System SHALL display checkpoint metadata before deletion

The system SHALL read and display checkpoint metadata (server, campaign, timestamp, name/comment) before prompting for confirmation.

#### Scenario: Display metadata from checkpoint
- **WHEN** user requests to delete a checkpoint
- **THEN** the system displays: server name, campaign, timestamp, optional name/comment from metadata.json

#### Scenario: Corrupted metadata
- **WHEN** checkpoint metadata.json is corrupted or missing
- **THEN** the system displays "Warning: Cannot read checkpoint metadata" but still allows deletion

### Requirement: System SHALL handle deletion failures gracefully

The system SHALL detect and report deletion failures (permissions, file in use, etc.) without crashing.

#### Scenario: File in use by another process
- **WHEN** checkpoint file is locked by another process during deletion
- **THEN** the system displays "Cannot delete: file is in use" and aborts

#### Scenario: Deletion permission denied
- **WHEN** user lacks permission to delete the checkpoint file
- **THEN** the system displays a clear permission error

#### Scenario: Disk error during deletion
- **WHEN** a disk error occurs during deletion (e.g., I/O error)
- **THEN** the system displays the error and indicates the file may still exist

### Requirement: System SHALL support interactive deletion with selection

The system SHALL allow users in interactive mode to select checkpoints from a list for deletion.

#### Scenario: Interactive mode displays checkpoint list
- **WHEN** user enters delete mode in interactive CLI
- **THEN** the system displays a numbered list of all checkpoints with metadata

#### Scenario: User selects checkpoint by number
- **WHEN** user selects a checkpoint by entering its number
- **THEN** the system displays that checkpoint's details and prompts for confirmation

#### Scenario: User cancels selection
- **WHEN** user cancels during checkpoint selection
- **THEN** the system returns to main menu without deleting anything

### Requirement: System SHALL verify file is a valid checkpoint before deleting

The system SHALL check that the file to be deleted is a valid checkpoint ZIP file.

#### Scenario: File is a valid checkpoint
- **WHEN** user deletes a file that is a valid checkpoint ZIP
- **THEN** the system proceeds with deletion (after confirmation)

#### Scenario: File is not a ZIP file
- **WHEN** user attempts to delete a file that is not a ZIP archive
- **THEN** the system displays "Not a valid checkpoint file" and aborts

#### Scenario: File is a ZIP but not a checkpoint
- **WHEN** user attempts to delete a ZIP file without checkpoint metadata
- **THEN** the system displays "Not a valid checkpoint (missing metadata)" but allows force deletion

### Requirement: System SHALL not allow undoing deletions

The system SHALL clearly indicate that deletion is permanent and cannot be undone.

#### Scenario: Deletion warning message
- **WHEN** prompting for deletion confirmation
- **THEN** the message includes "This action cannot be undone"

#### Scenario: No recycle bin usage
- **WHEN** a checkpoint is deleted
- **THEN** it is permanently removed (not moved to recycle bin/trash)

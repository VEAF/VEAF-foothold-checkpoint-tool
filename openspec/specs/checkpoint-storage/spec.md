## Purpose

This capability provides creation of checkpoint ZIP archives with metadata, checksums, and timestamp-based naming. It includes support for saving single or multiple campaigns with progress feedback.

## ADDED Requirements

### Requirement: System SHALL create checkpoint as timestamped ZIP archive

The system SHALL create checkpoints as ZIP files named `{campaign}_{YYYY-MM-DD_HH-MM-SS}.zip` containing all campaign files, Foothold_Ranks.lua, and metadata.json.

#### Scenario: Save single campaign checkpoint
- **WHEN** user saves a checkpoint for the "afghanistan" campaign
- **THEN** the system creates a ZIP file named like `afghanistan_2024-02-13_14-30-00.zip`

#### Scenario: Timestamp uniqueness
- **WHEN** multiple checkpoints are created for the same campaign
- **THEN** each checkpoint has a unique timestamp in the filename

#### Scenario: Checkpoint storage location
- **WHEN** a checkpoint is created
- **THEN** the ZIP file is saved in the directory specified by `checkpoints_dir` in configuration

### Requirement: System SHALL include metadata.json in checkpoint

The system SHALL create a `metadata.json` file inside each checkpoint ZIP containing server, campaign, timestamp, custom fields, and file checksums.

#### Scenario: Metadata includes all required fields
- **WHEN** a checkpoint is created
- **THEN** metadata.json contains fields: server, campaign, timestamp, name (optional), comment (optional), files (with original_name and checksum)

#### Scenario: Metadata timestamp is ISO 8601 format
- **WHEN** a checkpoint is created
- **THEN** the metadata timestamp field is in ISO 8601 format (e.g., "2024-02-13T14:30:00Z")

#### Scenario: Metadata includes original filenames
- **WHEN** a checkpoint is created from files like `FootHold_CA_v0.2.lua`
- **THEN** metadata.json preserves the original filename `FootHold_CA_v0.2.lua` for each file

### Requirement: System SHALL compute SHA-256 checksums for all files

The system SHALL compute SHA-256 checksums for all files included in the checkpoint and store them in metadata.json.

#### Scenario: Checksum computed for each file
- **WHEN** a checkpoint is created with 4 campaign files plus Foothold_Ranks.lua
- **THEN** metadata.json contains 5 checksums (one per file)

#### Scenario: Checksum format
- **WHEN** checksums are stored in metadata
- **THEN** they are in hex format (e.g., "sha256:abc123def456...")

#### Scenario: Large file checksum
- **WHEN** a checkpoint includes a large file (>100MB storage.csv)
- **THEN** the system computes the checksum successfully without memory issues (streaming)

### Requirement: System SHALL include Foothold_Ranks.lua in every checkpoint

The system SHALL always include `Foothold_Ranks.lua` in checkpoints when present in the source directory.

#### Scenario: Foothold_Ranks.lua present
- **WHEN** saving a checkpoint and Foothold_Ranks.lua exists in the source directory
- **THEN** the file is included in the ZIP archive

#### Scenario: Foothold_Ranks.lua absent
- **WHEN** saving a checkpoint and Foothold_Ranks.lua does not exist in the source directory
- **THEN** the system issues a warning but continues creating the checkpoint without it

### Requirement: System SHALL support saving all campaigns at once

The system SHALL allow saving checkpoints for all detected campaigns in a single operation, creating one ZIP file per campaign.

#### Scenario: Save all campaigns
- **WHEN** user selects "save all campaigns" and 3 campaigns are detected
- **THEN** the system creates 3 separate checkpoint ZIP files (one per campaign)

#### Scenario: All campaigns with shared metadata
- **WHEN** user saves all campaigns with a common name/comment
- **THEN** each checkpoint includes the same name/comment in metadata but different campaign fields

#### Scenario: Failure on one campaign does not stop others
- **WHEN** saving all campaigns and one fails (e.g., missing permissions)
- **THEN** the system reports the failure and continues saving remaining campaigns

### Requirement: System SHALL accept optional name and comment for checkpoints

The system SHALL allow users to specify an optional name and comment when creating checkpoints, stored in metadata.json.

#### Scenario: Checkpoint with name only
- **WHEN** user creates a checkpoint with name "Before Mission 5"
- **THEN** metadata.json includes `"name": "Before Mission 5"` and no comment field

#### Scenario: Checkpoint with name and comment
- **WHEN** user creates a checkpoint with name "Major Update" and comment "Backup before Kabul attack"
- **THEN** metadata.json includes both name and comment fields

#### Scenario: Checkpoint without name or comment
- **WHEN** user creates a checkpoint without specifying name or comment
- **THEN** metadata.json omits these optional fields

### Requirement: System SHALL validate source directory exists before saving

The system SHALL check that the source directory (server Saves path) exists and is readable before attempting to create a checkpoint.

#### Scenario: Source directory exists and readable
- **WHEN** user saves a checkpoint and the source directory is accessible
- **THEN** the system proceeds with checkpoint creation

#### Scenario: Source directory does not exist
- **WHEN** user attempts to save a checkpoint from a non-existent directory
- **THEN** the system displays an error and aborts the operation

#### Scenario: Source directory not readable
- **WHEN** user attempts to save a checkpoint from a directory without read permissions
- **THEN** the system displays a permissions error and aborts the operation

### Requirement: System SHALL display progress during checkpoint creation

The system SHALL show progress feedback (using Rich) during checkpoint creation, especially for large files.

#### Scenario: Progress bar for large files
- **WHEN** creating a checkpoint with large files (>10MB)
- **THEN** the system displays a progress bar showing compression progress

#### Scenario: Checksum progress indication
- **WHEN** computing checksums for multiple files
- **THEN** the system displays progress (e.g., "Computing checksums: 3/5 files")

#### Scenario: Completion message
- **WHEN** a checkpoint is successfully created
- **THEN** the system displays a success message with the checkpoint filename

### Requirement: System SHALL handle ZIP creation failures gracefully

The system SHALL detect and report ZIP creation failures (disk full, permissions, etc.) without leaving corrupt checkpoint files.

#### Scenario: Disk full during ZIP creation
- **WHEN** disk space runs out during checkpoint creation
- **THEN** the system displays an error and removes the incomplete ZIP file

#### Scenario: Write permission denied
- **WHEN** the checkpoint directory is not writable
- **THEN** the system displays a clear permission error before attempting to create the ZIP

#### Scenario: Partial ZIP cleanup
- **WHEN** ZIP creation fails mid-process
- **THEN** the system cleans up the partially created ZIP file and does not leave corrupted artifacts

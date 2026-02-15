## Purpose

This capability provides importing of campaign files from external directories into checkpoint format. It includes campaign auto-detection, file validation, metadata collection, and checksum computation for imported files.

## ADDED Requirements

### Requirement: System SHALL import campaign files from manual backup directory

The system SHALL scan a user-specified directory for Foothold campaign files and create a checkpoint from them.

#### Scenario: Import from directory with complete campaign
- **WHEN** user imports from a directory containing all expected files for a campaign (*.lua, *_CTLD_*.csv, *_storage.csv)
- **THEN** the system creates a checkpoint with all files

#### Scenario: Import directory does not exist
- **WHEN** user specifies a non-existent import directory
- **THEN** the system displays "Import directory not found: {path}" and aborts

#### Scenario: Import directory is empty
- **WHEN** user imports from an empty directory
- **THEN** the system displays "No campaign files detected in directory" and aborts

### Requirement: System SHALL auto-detect campaigns in import directory

The system SHALL scan the import directory and detect which campaigns are present based on file naming patterns.

#### Scenario: Single campaign detected
- **WHEN** import directory contains files for one campaign (e.g., all `foothold_afghanistan*` files)
- **THEN** the system detects and reports "Campaign detected: afghanistan"

#### Scenario: Multiple campaigns detected
- **WHEN** import directory contains files for multiple campaigns
- **THEN** the system lists all detected campaigns and prompts user to select one

#### Scenario: No recognizable campaigns
- **WHEN** import directory contains no Foothold campaign files
- **THEN** the system displays "No campaigns detected" and aborts

#### Scenario: Partial campaign files
- **WHEN** import directory contains some but not all expected files for a campaign
- **THEN** the system still detects the campaign and issues warnings for missing files

### Requirement: System SHALL validate expected files and issue warnings

The system SHALL check for expected campaign files (*.lua, *_CTLD_FARPS.csv, *_CTLD_Save.csv, *_storage.csv) and warn if any are missing.

#### Scenario: All expected files present
- **WHEN** importing a campaign with all expected files
- **THEN** the system proceeds without warnings

#### Scenario: Missing storage file
- **WHEN** importing a campaign without *_storage.csv
- **THEN** the system displays "Warning: {prefix}_storage.csv not found" and continues

#### Scenario: Missing CTLD files
- **WHEN** importing a campaign without CTLD CSV files
- **THEN** the system displays warnings for each missing file and continues

#### Scenario: Only .lua file present
- **WHEN** importing a campaign with only the .lua file
- **THEN** the system displays multiple warnings but allows import to proceed

### Requirement: System SHALL prompt for checkpoint metadata during import

The system SHALL request server name, optional name, and optional comment from the user when importing.

#### Scenario: CLI mode with metadata flags
- **WHEN** user runs `foothold-checkpoint import /path --server prod-1 --campaign afghanistan --name "Old backup"`
- **THEN** the system uses provided metadata without prompting

#### Scenario: Interactive mode prompts for metadata
- **WHEN** user imports in interactive mode without specifying metadata
- **THEN** the system prompts for server, campaign selection, name, and comment

#### Scenario: Missing required metadata in CLI mode
- **WHEN** user runs import command without --server or --campaign flags
- **THEN** the system prompts for the missing required fields

### Requirement: System SHALL create checkpoint with current timestamp

The system SHALL create the imported checkpoint with the current timestamp (not the file modification dates).

#### Scenario: Imported checkpoint timestamp
- **WHEN** importing old backup files with modification dates from 2023
- **THEN** the checkpoint filename and metadata timestamp reflect the current date/time (2024)

#### Scenario: Timestamp uniqueness
- **WHEN** importing multiple times from the same source
- **THEN** each import creates a checkpoint with a unique timestamp

### Requirement: System SHALL compute checksums for imported files

The system SHALL compute SHA-256 checksums for all files during import and store them in metadata.json.

#### Scenario: Checksums for all imported files
- **WHEN** importing campaign files
- **THEN** metadata.json includes checksums for every file in the checkpoint

#### Scenario: Large file checksum computation
- **WHEN** importing a campaign with large storage.csv (>100MB)
- **THEN** the system computes checksum successfully with progress indication

### Requirement: System SHALL preserve original filenames in metadata

The system SHALL record the original filename of each imported file in metadata.json.

#### Scenario: Original filenames recorded
- **WHEN** importing files like `FootHold_CA_v0.2.lua`
- **THEN** metadata.json includes `"original_name": "FootHold_CA_v0.2.lua"`

#### Scenario: Filenames with version suffixes
- **WHEN** importing files with version suffixes (_v0.2, _V0.1)
- **THEN** original names with suffixes are preserved in metadata

### Requirement: System SHALL include Foothold_Ranks.lua if present

The system SHALL include `Foothold_Ranks.lua` in the imported checkpoint if it exists in the source directory.

#### Scenario: Ranks file present in import directory
- **WHEN** importing and Foothold_Ranks.lua exists
- **THEN** the file is included in the checkpoint

#### Scenario: Ranks file absent from import directory
- **WHEN** importing and Foothold_Ranks.lua does not exist
- **THEN** the system displays "Warning: Foothold_Ranks.lua not found" and continues without it

### Requirement: System SHALL support campaign selection in interactive mode

The system SHALL display detected campaigns and allow the user to select which one to import in interactive mode.

#### Scenario: Multiple campaigns available
- **WHEN** import directory contains 3 campaigns
- **THEN** the system displays a numbered list of campaigns and prompts "Select campaign to import: [1-3]"

#### Scenario: User selects campaign by number
- **WHEN** user enters a valid campaign number
- **THEN** the system imports that campaign

#### Scenario: User enters invalid selection
- **WHEN** user enters an invalid number or text
- **THEN** the system displays "Invalid selection" and prompts again

### Requirement: System SHALL validate import directory is readable

The system SHALL verify the import directory exists and is readable before attempting to scan for campaigns.

#### Scenario: Import directory not readable
- **WHEN** user specifies a directory without read permissions
- **THEN** the system displays a permissions error and aborts

#### Scenario: Import directory is actually a file
- **WHEN** user specifies a file path instead of a directory
- **THEN** the system displays "Not a directory: {path}" and aborts

### Requirement: System SHALL display import summary

The system SHALL show a summary of what will be imported before creating the checkpoint.

#### Scenario: Import summary includes file list
- **WHEN** user is about to import a campaign
- **THEN** the system displays: campaign name, server, number of files, file names, any warnings

#### Scenario: User confirms import
- **WHEN** user confirms the import summary
- **THEN** the system creates the checkpoint

#### Scenario: User cancels import
- **WHEN** user cancels at the import summary
- **THEN** the system aborts and displays "Import cancelled"

### Requirement: System SHALL handle import failures gracefully

The system SHALL detect and report import failures without leaving corrupt checkpoints.

#### Scenario: Disk full during import
- **WHEN** disk space runs out while creating the checkpoint
- **THEN** the system displays an error and cleans up the partial checkpoint file

#### Scenario: Corrupted source file
- **WHEN** a source file is corrupted and cannot be read
- **THEN** the system displays which file failed and aborts the import

#### Scenario: Checkpoint already exists with same name
- **WHEN** importing would create a checkpoint with a filename that already exists
- **THEN** the system appends a unique suffix or prompts for resolution

## MODIFIED Requirements

### Requirement: System SHALL auto-detect campaigns using explicit configuration

The system SHALL scan the import directory and detect which campaigns are present based on configured file lists rather than pattern matching.

#### Scenario: Single campaign detected by file match
- **WHEN** import directory contains files that match one campaign's configured file list (e.g., `FootHold_CA_v0.2.lua` matches caucasus campaign)
- **THEN** the system detects and reports "Campaign detected: caucasus"

#### Scenario: Multiple campaigns detected
- **WHEN** import directory contains files matching multiple configured campaigns
- **THEN** the system lists all detected campaigns and prompts user to select one

#### Scenario: No configured campaigns match
- **WHEN** import directory contains Foothold-like files that don't match any configured campaign
- **THEN** the system displays error listing unknown files and instructions to update config.yaml

#### Scenario: Partial campaign files from configuration
- **WHEN** import directory contains some but not all configured files for a campaign
- **THEN** the system detects the campaign and issues warnings for missing non-optional files

#### Scenario: Mixed era suffix files detected as one campaign
- **WHEN** import directory contains `FootHold_CA_v0.2.lua` and `Foothold_CA_CTLD_FARPS_Modern.csv` both configured for caucasus campaign
- **THEN** the system detects as single "caucasus" campaign, not separate campaigns

### Requirement: System SHALL validate expected files using configuration

The system SHALL check for configured campaign files and warn if any non-optional files are missing.

#### Scenario: All configured files present
- **WHEN** importing a directory with all files configured for the campaign
- **THEN** the system proceeds without warnings

#### Scenario: Optional file missing
- **WHEN** importing a campaign missing a file marked `optional: true` in config
- **THEN** the system proceeds without warning about that file

#### Scenario: Required file missing
- **WHEN** importing a campaign missing a file not marked optional
- **THEN** the system displays "Warning: Expected file '{filename}' not found for campaign '{name}'" and continues

#### Scenario: Multiple required files missing
- **WHEN** importing a campaign missing multiple non-optional files
- **THEN** the system displays separate warnings for each missing file

#### Scenario: Only one file type present
- **WHEN** importing a campaign with only persistence files present (e.g., only .lua)
- **THEN** the system displays warnings for missing file types but allows import to proceed

### Requirement: System SHALL fail on unknown campaign files

The system SHALL abort import when encountering files that appear to be Foothold campaign files but are not in configuration.

#### Scenario: Unknown file detected
- **WHEN** import directory contains `foothold_newmap.lua` which is not in any campaign configuration
- **THEN** the system displays error: "Unknown campaign files detected" with list of unrecognized files and aborts import

#### Scenario: Unknown file error includes guidance
- **WHEN** unknown files are detected
- **THEN** error message includes example config.yaml snippet showing how to add the campaign

#### Scenario: Mix of known and unknown files
- **WHEN** import directory contains both configured files and unknown foothold files
- **THEN** the system lists only the unknown files in the error and aborts

### Requirement: System SHALL import campaign files from manual backup directory

The system SHALL scan a user-specified directory for Foothold campaign files and create a checkpoint from them.

#### Scenario: Import from directory with complete campaign
- **WHEN** user imports from a directory containing all expected files for a campaign
- **THEN** the system creates a checkpoint with all files

#### Scenario: Import directory does not exist
- **WHEN** user specifies a non-existent import directory
- **THEN** the system displays "Import directory not found: {path}" and aborts

#### Scenario: Import directory is empty
- **WHEN** user imports from an empty directory
- **THEN** the system displays "No campaign files detected in directory" and aborts

### Requirement: System SHALL prompt for checkpoint metadata during import

The system SHALL request server name, optional name, and optional comment from the user when importing.

#### Scenario: CLI mode with metadata flags
- **WHEN** user runs `foothold-checkpoint import /path --server prod-1 --campaign caucasus --name "Old backup"`
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
- **THEN** the checkpoint filename and metadata timestamp reflect the current date/time

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

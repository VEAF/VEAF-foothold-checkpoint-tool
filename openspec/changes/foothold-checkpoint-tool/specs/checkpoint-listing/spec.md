## ADDED Requirements

### Requirement: System SHALL list all checkpoints in storage directory

The system SHALL scan the checkpoint storage directory and display all available checkpoint files with their metadata.

#### Scenario: Checkpoints exist in storage
- **WHEN** the checkpoint storage directory contains 5 checkpoint ZIP files
- **THEN** the system displays all 5 checkpoints with their metadata

#### Scenario: No checkpoints exist
- **WHEN** the checkpoint storage directory is empty or contains no ZIP files
- **THEN** the system displays "No checkpoints found"

#### Scenario: Invalid checkpoint files present
- **WHEN** the storage directory contains non-checkpoint ZIP files or corrupted files
- **THEN** the system skips invalid files and displays only valid checkpoints

### Requirement: System SHALL display checkpoints in a formatted table

The system SHALL use Rich to display checkpoints in a table with columns: Filename, Server, Campaign, Date, Name/Comment.

#### Scenario: Table header is displayed
- **WHEN** listing checkpoints
- **THEN** the output includes a table header with column names

#### Scenario: Table rows show checkpoint info
- **WHEN** displaying each checkpoint
- **THEN** the row includes: checkpoint filename, source server, campaign name, timestamp, optional name/comment

#### Scenario: Empty name/comment fields
- **WHEN** a checkpoint has no name or comment in metadata
- **THEN** the table displays "-" or empty string in those columns

#### Scenario: Timestamps are human-readable
- **WHEN** displaying checkpoint timestamps
- **THEN** dates are formatted as readable strings (e.g., "2024-02-13 14:30:00")

### Requirement: System SHALL support filtering by server

The system SHALL allow filtering the checkpoint list to show only checkpoints from a specific server via the `--server` flag.

#### Scenario: Filter by server name
- **WHEN** user runs `foothold-checkpoint list --server prod-1`
- **THEN** only checkpoints with metadata server="prod-1" are displayed

#### Scenario: No checkpoints match server filter
- **WHEN** user filters by a server with no checkpoints
- **THEN** the system displays "No checkpoints found for server {server}"

#### Scenario: Invalid server name in filter
- **WHEN** user filters by a server not defined in config
- **THEN** the system displays a warning but still performs the filter

### Requirement: System SHALL support filtering by campaign

The system SHALL allow filtering the checkpoint list to show only checkpoints for a specific campaign via the `--campaign` flag.

#### Scenario: Filter by campaign name
- **WHEN** user runs `foothold-checkpoint list --campaign afghanistan`
- **THEN** only checkpoints with metadata campaign="afghanistan" are displayed

#### Scenario: No checkpoints match campaign filter
- **WHEN** user filters by a campaign with no checkpoints
- **THEN** the system displays "No checkpoints found for campaign {campaign}"

#### Scenario: Campaign name normalization in filter
- **WHEN** user filters by a historical campaign name (e.g., "GCW_Modern")
- **THEN** the system recognizes it as "Germany_Modern" and displays matching checkpoints

### Requirement: System SHALL support combined server and campaign filters

The system SHALL allow filtering by both server and campaign simultaneously.

#### Scenario: Filter by both server and campaign
- **WHEN** user runs `foothold-checkpoint list --server prod-1 --campaign afghanistan`
- **THEN** only checkpoints matching both server="prod-1" AND campaign="afghanistan" are displayed

#### Scenario: No checkpoints match combined filters
- **WHEN** no checkpoints match both filters
- **THEN** the system displays "No checkpoints found matching criteria"

### Requirement: System SHALL sort checkpoints chronologically

The system SHALL display checkpoints sorted by timestamp (newest first) by default.

#### Scenario: Multiple checkpoints for same campaign
- **WHEN** listing checkpoints where multiple exist for the same campaign
- **THEN** they are sorted with newest checkpoint first

#### Scenario: Checkpoints from different dates
- **WHEN** listing checkpoints created on different dates
- **THEN** they are sorted chronologically (most recent first)

### Requirement: System SHALL read metadata without extracting entire ZIP

The system SHALL read metadata.json from checkpoint ZIPs without extracting all files to disk.

#### Scenario: Large checkpoint file
- **WHEN** listing a checkpoint with large storage.csv (>500MB)
- **THEN** the system reads metadata quickly without extracting the full ZIP

#### Scenario: Corrupted ZIP metadata
- **WHEN** a checkpoint ZIP has corrupted metadata.json
- **THEN** the system displays a warning for that checkpoint and continues listing others

### Requirement: System SHALL show checkpoint file sizes

The system SHALL display the file size of each checkpoint in the list.

#### Scenario: Display file size in human-readable format
- **WHEN** listing checkpoints
- **THEN** file sizes are shown in human-readable format (e.g., "12.5 MB", "450 KB")

#### Scenario: Large checkpoint size
- **WHEN** a checkpoint is larger than 1 GB
- **THEN** the size is displayed as "1.2 GB"

### Requirement: System SHALL handle listing errors gracefully

The system SHALL detect and report errors when listing checkpoints without crashing.

#### Scenario: Checkpoint directory does not exist
- **WHEN** the configured checkpoint directory does not exist
- **THEN** the system displays "Checkpoint directory not found: {path}" and suggests creating it

#### Scenario: Checkpoint directory not readable
- **WHEN** the checkpoint directory lacks read permissions
- **THEN** the system displays a permissions error

#### Scenario: Corrupted checkpoint file
- **WHEN** a checkpoint ZIP file is corrupted and cannot be read
- **THEN** the system displays a warning for that file and continues listing valid checkpoints

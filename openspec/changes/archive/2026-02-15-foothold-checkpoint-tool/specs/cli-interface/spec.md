## ADDED Requirements

### Requirement: System SHALL provide command-line interface with Typer

The system SHALL implement a CLI using Typer with commands: save, restore, list, delete, import.

#### Scenario: Show help text
- **WHEN** user runs `foothold-checkpoint --help`
- **THEN** the system displays usage information for all available commands

#### Scenario: Show command-specific help
- **WHEN** user runs `foothold-checkpoint save --help`
- **THEN** the system displays help text for the save command with all options

#### Scenario: Invalid command
- **WHEN** user runs `foothold-checkpoint invalid-command`
- **THEN** the system displays "Error: No such command 'invalid-command'" and suggests `--help`

### Requirement: System SHALL support save command with options

The system SHALL implement a `save` command that accepts --server, --campaign, --all, --name, --comment flags.

#### Scenario: Save with all required flags
- **WHEN** user runs `foothold-checkpoint save --server prod-1 --campaign afghanistan --name "Mission 5"`
- **THEN** the system saves a checkpoint for the specified campaign

#### Scenario: Save all campaigns
- **WHEN** user runs `foothold-checkpoint save --server prod-1 --all`
- **THEN** the system creates checkpoints for all detected campaigns

#### Scenario: Save with missing required flag
- **WHEN** user runs `foothold-checkpoint save --campaign afghanistan` (missing --server)
- **THEN** the system prompts for server selection

### Requirement: System SHALL support restore command with options

The system SHALL implement a `restore` command that accepts checkpoint file, --server, and --restore-ranks flags.

#### Scenario: Restore with all required flags
- **WHEN** user runs `foothold-checkpoint restore afghanistan_2024-02-13.zip --server test-server`
- **THEN** the system restores the checkpoint to the specified server

#### Scenario: Restore with ranks file
- **WHEN** user runs `foothold-checkpoint restore afghanistan_2024-02-13.zip --server test-server --restore-ranks`
- **THEN** the system restores including Foothold_Ranks.lua

#### Scenario: Restore without server flag
- **WHEN** user runs `foothold-checkpoint restore afghanistan_2024-02-13.zip` (missing --server)
- **THEN** the system prompts for server selection

### Requirement: System SHALL support list command with filters

The system SHALL implement a `list` command that accepts optional --server and --campaign filters.

#### Scenario: List all checkpoints
- **WHEN** user runs `foothold-checkpoint list`
- **THEN** the system displays all checkpoints in a table

#### Scenario: List with server filter
- **WHEN** user runs `foothold-checkpoint list --server prod-1`
- **THEN** only checkpoints from prod-1 are displayed

#### Scenario: List with campaign filter
- **WHEN** user runs `foothold-checkpoint list --campaign afghanistan`
- **THEN** only afghanistan checkpoints are displayed

#### Scenario: List with both filters
- **WHEN** user runs `foothold-checkpoint list --server prod-1 --campaign afghanistan`
- **THEN** only checkpoints matching both criteria are displayed

### Requirement: System SHALL support delete command with confirmation

The system SHALL implement a `delete` command that accepts a checkpoint filename and optional --force flag.

#### Scenario: Delete with confirmation
- **WHEN** user runs `foothold-checkpoint delete afghanistan_2024-02-13.zip`
- **THEN** the system displays checkpoint info and prompts "Delete? (y/n)"

#### Scenario: Force delete without confirmation
- **WHEN** user runs `foothold-checkpoint delete afghanistan_2024-02-13.zip --force`
- **THEN** the system deletes immediately without prompting

### Requirement: System SHALL support import command with options

The system SHALL implement an `import` command that accepts source directory path, --server, --campaign, --name, --comment flags.

#### Scenario: Import with all flags
- **WHEN** user runs `foothold-checkpoint import /path/to/backup --server prod-1 --campaign afghanistan --name "Old backup"`
- **THEN** the system imports the specified campaign

#### Scenario: Import with missing flags
- **WHEN** user runs `foothold-checkpoint import /path/to/backup` (missing metadata)
- **THEN** the system prompts for server, campaign selection, and optional name/comment

### Requirement: System SHALL support interactive mode with simple prompts

The system SHALL allow running commands without required flags and prompt for missing parameters.

#### Scenario: Save without flags prompts for inputs
- **WHEN** user runs `foothold-checkpoint save` with no flags
- **THEN** the system prompts sequentially for: server, campaign (or all), optional name, optional comment

#### Scenario: Restore without flags prompts for inputs
- **WHEN** user runs `foothold-checkpoint restore` with no checkpoint file
- **THEN** the system lists available checkpoints and prompts for selection, then server

#### Scenario: Import without flags prompts for inputs
- **WHEN** user runs `foothold-checkpoint import` with no directory
- **THEN** the system prompts for directory path, then detects campaigns and prompts for selection

### Requirement: System SHALL use Rich for enhanced terminal output

The system SHALL use Rich to display formatted tables, progress bars, and colored output.

#### Scenario: List displays Rich table
- **WHEN** listing checkpoints
- **THEN** output is a formatted table with borders and column alignment

#### Scenario: Progress bars for long operations
- **WHEN** saving or restoring large checkpoints
- **THEN** the system displays Rich progress bars showing operation status

#### Scenario: Colored output for success/error
- **WHEN** operations succeed
- **THEN** success messages are displayed in green
- **WHEN** operations fail
- **THEN** error messages are displayed in red

#### Scenario: Warnings in yellow
- **WHEN** the system issues warnings (e.g., missing files during import)
- **THEN** warnings are displayed in yellow

### Requirement: System SHALL support --version flag

The system SHALL display version information when invoked with --version.

#### Scenario: Display version
- **WHEN** user runs `foothold-checkpoint --version`
- **THEN** the system displays "foothold-checkpoint version X.Y.Z"

### Requirement: System SHALL support --config flag to specify custom config path

The system SHALL allow specifying a custom configuration file path via --config flag.

#### Scenario: Use custom config file
- **WHEN** user runs `foothold-checkpoint --config /path/to/custom.yaml list`
- **THEN** the system loads configuration from the specified path instead of default

#### Scenario: Custom config does not exist
- **WHEN** user specifies a non-existent config file
- **THEN** the system displays "Config file not found: {path}" and exits

### Requirement: System SHALL provide clear error messages

The system SHALL display user-friendly error messages for common failure scenarios.

#### Scenario: Server not found in config
- **WHEN** user specifies a server not defined in config
- **THEN** the system displays "Server '{name}' not found in configuration. Available servers: {list}"

#### Scenario: Campaign not detected
- **WHEN** user specifies a campaign not detected in server directory
- **THEN** the system displays "Campaign '{name}' not found. Detected campaigns: {list}"

#### Scenario: File not found error
- **WHEN** a required file is not found
- **THEN** the system displays "File not found: {path}" (not a stack trace)

#### Scenario: Permission error
- **WHEN** a permission error occurs
- **THEN** the system displays "Permission denied: {path}" with suggestion to check permissions

### Requirement: System SHALL support Ctrl+C graceful exit

The system SHALL handle interrupt signals (Ctrl+C) gracefully without displaying stack traces.

#### Scenario: User interrupts operation
- **WHEN** user presses Ctrl+C during an operation
- **THEN** the system displays "Operation cancelled by user" and exits cleanly

#### Scenario: Interrupt during checkpoint creation
- **WHEN** user interrupts during save operation
- **THEN** the system cleans up partial checkpoint file and exits

### Requirement: System SHALL validate flag combinations

The system SHALL detect invalid flag combinations and display helpful error messages.

#### Scenario: Conflicting flags
- **WHEN** user runs `foothold-checkpoint save --campaign afghanistan --all`
- **THEN** the system displays "Error: Cannot use --campaign and --all together"

#### Scenario: Restore-ranks without restore command
- **WHEN** user runs `foothold-checkpoint list --restore-ranks`
- **THEN** the system displays "Error: --restore-ranks is only valid with restore command"

### Requirement: System SHALL support quiet mode for automation

The system SHALL support a --quiet flag that suppresses non-essential output for use in scripts.

#### Scenario: Quiet save operation
- **WHEN** user runs `foothold-checkpoint save --server prod-1 --campaign afghanistan --quiet`
- **THEN** the system suppresses progress bars and only outputs the checkpoint filename on success

#### Scenario: Quiet list operation
- **WHEN** user runs `foothold-checkpoint list --quiet`
- **THEN** the system outputs checkpoint filenames only (no table formatting)

#### Scenario: Quiet mode still shows errors
- **WHEN** an error occurs in quiet mode
- **THEN** the error message is still displayed (errors are never suppressed)

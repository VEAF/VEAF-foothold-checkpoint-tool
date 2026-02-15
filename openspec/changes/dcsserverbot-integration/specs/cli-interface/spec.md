## MODIFIED Requirements

### Requirement: System SHALL support save command with options

The system SHALL implement a `save` command that accepts --server, --campaign, --all, --name, --comment flags. The CLI SHALL call core library functions via asyncio.run() wrapper.

#### Scenario: Save with all required flags
- **WHEN** user runs `foothold-checkpoint save --server prod-1 --campaign afghanistan --name "Mission 5"`
- **THEN** CLI parses flags and calls asyncio.run(save_checkpoint(...)) from core library

#### Scenario: Save all campaigns
- **WHEN** user runs `foothold-checkpoint save --server prod-1 --all`
- **THEN** CLI iterates campaigns and calls asyncio.run(save_checkpoint(...)) for each

#### Scenario: Save with missing required flag
- **WHEN** user runs `foothold-checkpoint save --campaign afghanistan` (missing --server)
- **THEN** CLI prompts for server selection, then calls core library function

#### Scenario: Save without event hooks
- **WHEN** CLI executes save operation
- **THEN** CLI calls core library with hooks=None (no Discord notifications)

### Requirement: System SHALL support restore command with options

The system SHALL implement a `restore` command that accepts checkpoint file, --server, --auto-backup/--no-auto-backup flags. The CLI SHALL call core library functions via asyncio.run() wrapper.

#### Scenario: Restore with all required flags
- **WHEN** user runs `foothold-checkpoint restore afghanistan_2024-02-13.zip --server test-server`
- **THEN** CLI parses flags and calls asyncio.run(restore_checkpoint(...)) from core library

#### Scenario: Restore with auto-backup flag
- **WHEN** user runs `foothold-checkpoint restore checkpoint.zip --server test --auto-backup`
- **THEN** CLI passes auto_backup=True to core library restore function

#### Scenario: Restore without auto-backup flag
- **WHEN** user runs `foothold-checkpoint restore checkpoint.zip --server test --no-auto-backup`
- **THEN** CLI passes auto_backup=False to core library restore function

#### Scenario: Restore without event hooks
- **WHEN** CLI executes restore operation
- **THEN** CLI calls core library with hooks=None (no Discord notifications)

### Requirement: System SHALL support list command with filters

The system SHALL implement a `list` command that accepts optional --server, --campaign, --details filters. The CLI SHALL call core library functions via asyncio.run() wrapper.

#### Scenario: List all checkpoints
- **WHEN** user runs `foothold-checkpoint list`
- **THEN** CLI calls asyncio.run(list_checkpoints(...)) and formats results as Rich table

#### Scenario: List with server filter
- **WHEN** user runs `foothold-checkpoint list --server prod-1`
- **THEN** CLI passes server filter to core library and displays filtered results

#### Scenario: List with campaign filter
- **WHEN** user runs `foothold-checkpoint list --campaign afghanistan`
- **THEN** CLI passes campaign filter to core library and displays filtered results

#### Scenario: List with details flag
- **WHEN** user runs `foothold-checkpoint list --details`
- **THEN** CLI calls core library with details=True and displays expanded checkpoint information

### Requirement: System SHALL support delete command with confirmation

The system SHALL implement a `delete` command that accepts a checkpoint filename and optional --force flag. The CLI SHALL call core library functions via asyncio.run() wrapper.

#### Scenario: Delete with confirmation
- **WHEN** user runs `foothold-checkpoint delete afghanistan_2024-02-13.zip`
- **THEN** CLI displays checkpoint info, prompts for confirmation, then calls asyncio.run(delete_checkpoint(...))

#### Scenario: Force delete without confirmation
- **WHEN** user runs `foothold-checkpoint delete afghanistan_2024-02-13.zip --force`
- **THEN** CLI skips prompt and immediately calls asyncio.run(delete_checkpoint(...))

#### Scenario: Delete without event hooks
- **WHEN** CLI executes delete operation
- **THEN** CLI calls core library with hooks=None (no Discord notifications)

## ADDED Requirements

### Requirement: System SHALL refactor CLI to use shared core library

The system SHALL refactor CLI commands to orchestrate calls to core library functions without implementing business logic.

#### Scenario: CLI contains no checkpoint business logic
- **WHEN** CLI command is executed
- **THEN** all checkpoint creation, validation, restoration logic is in core library, CLI only handles argument parsing and display

#### Scenario: CLI imports from core library
- **WHEN** CLI module is loaded
- **THEN** imports save_checkpoint, restore_checkpoint, list_checkpoints, delete_checkpoint from foothold_checkpoint.core

#### Scenario: CLI wraps async functions with asyncio.run
- **WHEN** CLI calls core library async function
- **THEN** uses result = asyncio.run(core_function(...)) pattern

#### Scenario: CLI does not implement EventHooks
- **WHEN** CLI calls core library functions
- **THEN** always passes hooks=None (Discord hooks only used by plugin)

### Requirement: System SHALL load configuration for CLI-only mode

The system SHALL load configuration from config.yaml without requiring plugin-specific settings.

#### Scenario: CLI loads config.yaml and campaigns.yaml
- **WHEN** CLI initializes
- **THEN** loads config from ~/.foothold-checkpoint/config.yaml and campaigns from referenced campaigns_file

#### Scenario: CLI validates campaigns_file exists
- **WHEN** CLI loads configuration
- **THEN** validates campaigns_file path exists and is readable

#### Scenario: CLI supports --config flag for custom location
- **WHEN** user specifies --config flag
- **THEN** CLI loads configuration from specified path instead of default

#### Scenario: CLI does not require plugin-specific config
- **WHEN** CLI loads configuration
- **THEN** permissions and notifications sections are ignored (plugin-only)

### Requirement: System SHALL maintain backward compatibility for CLI users

The system SHALL ensure existing CLI workflows continue to work without modification.

#### Scenario: Existing config.yaml upgraded to campaigns_file
- **WHEN** CLI detects old config format with inline campaigns
- **THEN** CLI displays helpful error explaining migration to campaigns.yaml

#### Scenario: All existing CLI commands work
- **WHEN** user runs any v1.1.0 CLI command
- **THEN** command executes successfully with same behavior (after config migration)

#### Scenario: CLI does not introduce Discord dependencies
- **WHEN** CLI is installed without plugin optional dependencies
- **THEN** CLI works fully without discord.py installed

#### Scenario: CLI exit codes unchanged
- **WHEN** CLI completes operations
- **THEN** exit codes match v1.1.0 behavior (0 success, 1 error)

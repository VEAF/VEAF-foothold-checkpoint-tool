## ADDED Requirements

### Requirement: System SHALL load configuration from YAML file

The system SHALL load configuration from `~/.foothold-checkpoint/config.yaml` containing server paths, campaign mappings, and checkpoint storage location.

#### Scenario: Configuration file exists and is valid
- **WHEN** the system starts and config file exists at `~/.foothold-checkpoint/config.yaml`
- **THEN** the system loads the configuration without errors

#### Scenario: Configuration file has invalid YAML syntax
- **WHEN** the system attempts to load a config file with invalid YAML syntax
- **THEN** the system displays a clear error message indicating the syntax error location and exits

#### Scenario: Configuration file has invalid schema
- **WHEN** the system attempts to load a config file that is valid YAML but fails Pydantic validation
- **THEN** the system displays a clear error message indicating which fields are invalid and exits

### Requirement: System SHALL auto-create default configuration if missing

The system SHALL automatically create a default configuration file at `~/.foothold-checkpoint/config.yaml` if it does not exist on first run.

#### Scenario: Configuration file does not exist
- **WHEN** the system starts and no config file exists at `~/.foothold-checkpoint/config.yaml`
- **THEN** the system creates the directory `~/.foothold-checkpoint/` and a default config file with example servers and campaigns

#### Scenario: Configuration directory does not exist
- **WHEN** the system starts and the directory `~/.foothold-checkpoint/` does not exist
- **THEN** the system creates the directory and the default config file

#### Scenario: Default config file is created
- **WHEN** the system creates a default config file
- **THEN** the file contains example server configurations, campaign mappings, and default checkpoint storage location

### Requirement: Configuration SHALL use Pydantic models for validation

The system SHALL use Pydantic models to validate configuration structure and types at runtime.

#### Scenario: Server path is not a valid path
- **WHEN** a server configuration contains a path field that is not a valid filesystem path
- **THEN** Pydantic validation fails with a clear error message

#### Scenario: Campaign mapping is not a list
- **WHEN** a campaign mapping value is not a list of strings
- **THEN** Pydantic validation fails with a clear error message

#### Scenario: Checkpoints directory is missing
- **WHEN** the config file does not specify a checkpoints_dir field
- **THEN** Pydantic validation fails with a clear error message

### Requirement: Configuration SHALL support server definitions

The system SHALL support defining multiple DCS servers with paths and descriptions in the configuration.

#### Scenario: Multiple servers are defined
- **WHEN** the config file defines multiple servers with unique names
- **THEN** the system loads all server configurations and makes them available for checkpoint operations

#### Scenario: Server path does not exist
- **WHEN** a server configuration points to a non-existent path
- **THEN** the system issues a warning but does not fail to load the config

#### Scenario: Duplicate server names
- **WHEN** the config file defines two servers with the same name
- **THEN** Pydantic validation fails with an error indicating duplicate server names

### Requirement: Configuration SHALL support campaign name mappings

The system SHALL support defining campaign name evolution history (from oldest to newest) for handling renamed campaigns.

#### Scenario: Campaign with multiple historical names
- **WHEN** a campaign mapping defines multiple names in chronological order
- **THEN** the system recognizes all names as referring to the same campaign

#### Scenario: Campaign with single name
- **WHEN** a campaign mapping defines only one name
- **THEN** the system treats that name as both historical and current

#### Scenario: Empty campaign name list
- **WHEN** a campaign mapping has an empty list of names
- **THEN** Pydantic validation fails with an error

### Requirement: Configuration SHALL specify checkpoint storage location

The system SHALL allow specifying a custom directory for checkpoint storage via the `checkpoints_dir` configuration field.

#### Scenario: Custom checkpoint directory is specified
- **WHEN** the config file specifies a custom `checkpoints_dir` path
- **THEN** the system uses that path for all checkpoint save/restore/list operations

#### Scenario: Checkpoint directory uses tilde expansion
- **WHEN** the config file specifies a path like `~/my-checkpoints`
- **THEN** the system expands the tilde to the user's home directory

#### Scenario: Checkpoint directory does not exist
- **WHEN** the specified checkpoint directory does not exist
- **THEN** the system creates it automatically when saving the first checkpoint

### Requirement: Configuration SHALL be reloadable without restart

The system SHALL detect and reload configuration changes without requiring a restart (for interactive mode).

#### Scenario: Config file is modified during interactive session
- **WHEN** the user modifies the config file while the interactive CLI is running
- **THEN** the next operation uses the updated configuration

#### Scenario: Config file becomes invalid during session
- **WHEN** the user modifies the config file with invalid syntax during an interactive session
- **THEN** the system displays an error and continues using the last valid configuration

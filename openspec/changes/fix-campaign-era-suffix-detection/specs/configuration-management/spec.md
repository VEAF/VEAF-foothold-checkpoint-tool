## MODIFIED Requirements

### Requirement: System SHALL load configuration from YAML file with campaign file lists

The system SHALL load configuration from `~/.foothold-checkpoint/config.yaml` containing server paths, campaign file lists, and checkpoint storage location.

#### Scenario: Configuration file exists and is valid
- **WHEN** the system starts and config file exists at `~/.foothold-checkpoint/config.yaml`
- **THEN** the system loads the configuration without errors

#### Scenario: Configuration includes campaign file lists
- **WHEN** config.yaml includes campaign definitions with explicit file lists for each file type
- **THEN** the system successfully parses file type categories (persistence, ctld_save, ctld_farps, storage) and optional flags

#### Scenario: Configuration file has invalid YAML syntax
- **WHEN** the system attempts to load a config file with invalid YAML syntax
- **THEN** the system displays a clear error message indicating the syntax error location and exits

#### Scenario: Configuration file has invalid schema
- **WHEN** the system attempts to load a config file that is valid YAML but fails Pydantic validation
- **THEN** the system displays a clear error message indicating which fields are invalid and exits

#### Scenario: Campaign missing required file lists
- **WHEN** config.yaml defines a campaign without required file type categories
- **THEN** Pydantic validation fails with error: "Campaign '{name}' must define file lists"

#### Scenario: Campaign file list is empty
- **WHEN** a campaign's file type list is empty (e.g., `persistence: []`)
- **THEN** Pydantic validation fails with error indicating at least one file required per type

#### Scenario: Server path is not a valid path
- **WHEN** a server configuration contains a path field that is not a valid filesystem path
- **THEN** Pydantic validation fails with a clear error message

#### Scenario: Checkpoints directory is missing
- **WHEN** the config file does not specify a checkpoints_dir field
- **THEN** Pydantic validation fails with a clear error message

### Requirement: Configuration SHALL use Pydantic models for validation

The system SHALL use Pydantic models to validate configuration structure and types at runtime.

#### Scenario: Campaign file list structure validation
- **WHEN** a campaign's files section has invalid structure (e.g., missing file type categories)
- **THEN** Pydantic validation fails with a clear error message

#### Scenario: Optional flag validation
- **WHEN** a file type includes `optional: true` flag
- **THEN** the system parses the optional flag correctly as a boolean

#### Scenario: Invalid optional flag value
- **WHEN** a file type includes `optional: "maybe"` (non-boolean value)
- **THEN** Pydantic validation fails with error: "optional must be a boolean"

### Requirement: System SHALL auto-create default configuration if missing

The system SHALL automatically create a default configuration file at `~/.foothold-checkpoint/config.yaml` if it does not exist on first run.

#### Scenario: Configuration file does not exist
- **WHEN** the system starts and no config file exists at `~/.foothold-checkpoint/config.yaml`
- **THEN** the system creates the directory `~/.foothold-checkpoint/` and a default config file with example servers and campaigns

#### Scenario: Configuration directory does not exist
- **WHEN** the system starts and the directory `~/.foothold-checkpoint/` does not exist
- **THEN** the system creates the directory and the default config file

#### Scenario: Default config includes file lists
- **WHEN** the system creates a default config file
- **THEN** the file contains example campaign configurations with explicit file lists using the new structure

#### Scenario: Default config is valid
- **WHEN** the system creates a default config file
- **THEN** the generated config passes Pydantic validation without errors

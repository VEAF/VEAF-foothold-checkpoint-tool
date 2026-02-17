## Purpose

This capability provides role-based access control for checkpoint operations using Discord roles, allowing administrators to configure which roles can perform save, restore, list, and delete operations. Integrates with DCSServerBot's permission system.

## ADDED Requirements

### Requirement: System SHALL enforce role-based permissions for checkpoint operations

The system SHALL verify user has required Discord role before executing checkpoint operations.

#### Scenario: User with required role can execute operation
- **WHEN** user with permitted role executes checkpoint command
- **THEN** system allows operation to proceed

#### Scenario: User without required role is denied
- **WHEN** user without permitted role executes checkpoint command
- **THEN** system denies operation and sends ephemeral error message

#### Scenario: Permission check before operation execution
- **WHEN** checkpoint command is invoked
- **THEN** system checks permissions before defer() is called

#### Scenario: Multiple roles allowed per operation
- **WHEN** configuration lists multiple roles for operation
- **THEN** system allows execution if user has any of the permitted roles

#### Scenario: Case-insensitive role matching
- **WHEN** system checks user roles against configuration
- **THEN** role names are compared case-insensitively

### Requirement: System SHALL configure permissions per operation type

The system SHALL allow different role requirements for save, restore, list, and delete operations.

#### Scenario: Save operation permissions
- **WHEN** user executes save command
- **THEN** system checks user roles against config['permissions']['save'] list

#### Scenario: Restore operation permissions
- **WHEN** user executes restore command
- **THEN** system checks user roles against config['permissions']['restore'] list

#### Scenario: List operation permissions
- **WHEN** user executes list command
- **THEN** system checks user roles against config['permissions']['list'] list

#### Scenario: Delete operation permissions
- **WHEN** user executes delete command
- **THEN** system checks user roles against config['permissions']['delete'] list

#### Scenario: Different permission levels per operation
- **WHEN** configuration specifies different roles per operation
- **THEN** more restricted operations (restore, delete) can require higher privilege roles than less restricted (save, list)

### Requirement: System SHALL integrate with DCSServerBot permission decorators

The system SHALL use DCSServerBot's @utils.app_has_role() decorator for base permission enforcement.

#### Scenario: Commands use base role requirement
- **WHEN** command is defined
- **THEN** command uses @utils.app_has_role('DCS') as minimum requirement

#### Scenario: Additional permission check in command body
- **WHEN** command requires operation-specific permissions
- **THEN** command calls check_permission() method after base role check

#### Scenario: Base role check applies to all commands
- **WHEN** any foothold command is invoked
- **THEN** user must have at least 'DCS' role as enforced by decorator

### Requirement: System SHALL provide clear permission denied messages

The system SHALL inform users when they lack required permissions with actionable feedback.

#### Scenario: Permission denied shows required roles
- **WHEN** user is denied due to insufficient permissions
- **THEN** error message lists roles that are permitted for operation

#### Scenario: Permission denied message is ephemeral
- **WHEN** permission denied error is sent
- **THEN** message is ephemeral (visible only to user who invoked command)

#### Scenario: Permission denied includes emoji indicator
- **WHEN** permission denied error is displayed
- **THEN** message includes ❌ emoji for clear visual indication

#### Scenario: Permission denied message format
- **WHEN** permission denied error is sent
- **THEN** message format is "❌ You don't have permission to [operation]. Required roles: [role1, role2]"

### Requirement: System SHALL load permissions from plugin configuration

The system SHALL read role permissions from foothold.yaml configuration file.

#### Scenario: Default permissions loaded
- **WHEN** plugin initializes with DEFAULT config section
- **THEN** system loads permissions from config['DEFAULT']['permissions']

#### Scenario: Server-specific permission overrides
- **WHEN** plugin configuration includes server-specific section
- **THEN** server-specific permissions override DEFAULT permissions for that server

#### Scenario: Missing permissions key uses safe defaults
- **WHEN** configuration lacks permissions section
- **THEN** system defaults to requiring 'DCS Admin' role for all operations

#### Scenario: Empty role list denies all
- **WHEN** configuration specifies empty list for operation permission
- **THEN** no users can perform that operation (effectively disabled)

#### Scenario: Invalid configuration logs warning
- **WHEN** permissions configuration is invalid or malformed
- **THEN** system logs warning and falls back to safe defaults

### Requirement: System SHALL support administrator override

The system SHALL allow server administrators to bypass role restrictions for emergency operations.

#### Scenario: Administrator role bypasses all restrictions
- **WHEN** user has 'Administrator' Discord permission
- **THEN** system allows all checkpoint operations regardless of configured roles

#### Scenario: Bot owner bypasses all restrictions
- **WHEN** user is bot owner (from bot configuration)
- **THEN** system allows all checkpoint operations regardless of configured roles

#### Scenario: Override logged for audit
- **WHEN** administrator or bot owner bypasses role restriction
- **THEN** system logs override event with user information

### Requirement: System SHALL validate role configuration on startup

The system SHALL check permission configuration validity when plugin loads.

#### Scenario: Valid configuration passes validation
- **WHEN** plugin loads with valid permissions configuration
- **THEN** system completes initialization without errors

#### Scenario: Invalid role name format detected
- **WHEN** configuration contains invalid role name format
- **THEN** system logs warning identifying problematic role name

#### Scenario: Missing required permission keys detected
- **WHEN** configuration lacks required permission operation keys
- **THEN** system logs warning and uses defaults for missing keys

#### Scenario: Configuration schema validation
- **WHEN** foothold.yaml is loaded
- **THEN** system validates permissions section against foothold_schema.yaml

#### Scenario: Validation errors prevent plugin load
- **WHEN** permission configuration has critical validation errors
- **THEN** system prevents plugin from loading and logs detailed error message

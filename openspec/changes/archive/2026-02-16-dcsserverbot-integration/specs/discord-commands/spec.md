## Purpose

This capability provides Discord slash commands for checkpoint management operations, enabling users to save, restore, list, and delete checkpoints directly from Discord. Commands use interactive Discord UI elements (autocomplete, select menus, buttons) for an intuitive user experience.

## ADDED Requirements

### Requirement: System SHALL provide /foothold save command

The system SHALL provide a `/foothold save` Discord slash command to create a checkpoint from a campaign's current state.

#### Scenario: Save checkpoint with default name
- **WHEN** user executes `/foothold save` with server and campaign parameters
- **THEN** system creates a timestamped checkpoint with default naming

#### Scenario: Save checkpoint with custom name
- **WHEN** user executes `/foothold save` with server, campaign, and name parameters
- **THEN** system creates a checkpoint using the provided custom name

#### Scenario: Save checkpoint with comment
- **WHEN** user executes `/foothold save` with server, campaign, and comment parameters
- **THEN** system creates a checkpoint and stores the comment in metadata

#### Scenario: Campaign autocomplete suggestions
- **WHEN** user types in the campaign parameter field
- **THEN** system displays autocomplete suggestions from campaigns.yaml filtered by current input

#### Scenario: Save in progress feedback
- **WHEN** checkpoint save operation starts
- **THEN** system displays "thinking" indicator followed by progress updates

#### Scenario: Save success response
- **WHEN** checkpoint save completes successfully
- **THEN** system displays rich Discord embed with checkpoint name, size, campaign, and server details

#### Scenario: Save failure response  
- **WHEN** checkpoint save fails due to error
- **THEN** system displays error embed with failure reason and suggestions for resolution

#### Scenario: Permission denied for save
- **WHEN** user without save permissions attempts `/foothold save`
- **THEN** system displays ephemeral error message indicating insufficient permissions

### Requirement: System SHALL provide /foothold restore command

The system SHALL provide a `/foothold restore` Discord slash command to restore a campaign from a checkpoint.

#### Scenario: Restore with checkpoint selection
- **WHEN** user executes `/foothold restore` with server and checkpoint parameters
- **THEN** system restores the specified checkpoint to the server's mission directory

#### Scenario: Checkpoint autocomplete suggestions
- **WHEN** user types in the checkpoint parameter field
- **THEN** system displays autocomplete suggestions of available checkpoints filtered by current input and server

#### Scenario: Restore with auto-backup enabled
- **WHEN** user executes `/foothold restore` without --no-auto-backup flag
- **THEN** system creates automatic backup before restoring checkpoint

#### Scenario: Restore with auto-backup disabled
- **WHEN** user executes `/foothold restore` with --no-auto-backup flag
- **THEN** system restores checkpoint without creating automatic backup

#### Scenario: Restore confirmation prompt
- **WHEN** user executes `/foothold restore` command
- **THEN** system displays Discord modal or buttons requiring explicit confirmation before proceeding

#### Scenario: Restore in progress feedback
- **WHEN** checkpoint restore operation starts
- **THEN** system displays progress updates including auto-backup creation and file restoration status

#### Scenario: Restore success response
- **WHEN** checkpoint restore completes successfully
- **THEN** system displays rich Discord embed with restored checkpoint details, campaign, and auto-backup path if created

#### Scenario: Restore failure response
- **WHEN** checkpoint restore fails due to error
- **THEN** system displays error embed with failure reason and indicates auto-backup location if created

#### Scenario: Permission denied for restore
- **WHEN** user without restore permissions attempts `/foothold restore`
- **THEN** system displays ephemeral error message indicating insufficient permissions

### Requirement: System SHALL provide /foothold list command

The system SHALL provide a `/foothold list` Discord slash command to display available checkpoints.

#### Scenario: List all checkpoints for server
- **WHEN** user executes `/foothold list` with server parameter only
- **THEN** system displays paginated list of all checkpoints for that server

#### Scenario: List checkpoints filtered by campaign
- **WHEN** user executes `/foothold list` with server and campaign parameters
- **THEN** system displays checkpoints filtered to specified campaign

#### Scenario: List with details flag
- **WHEN** user executes `/foothold list` with --details flag
- **THEN** system displays checkpoint list including file contents and sizes

#### Scenario: Empty checkpoint list
- **WHEN** user executes `/foothold list` and no checkpoints exist
- **THEN** system displays message indicating no checkpoints found with suggestion to create one

#### Scenario: Paginated checkpoint list
- **WHEN** checkpoint count exceeds page limit
- **THEN** system displays Discord embed with navigation buttons for next/previous pages

#### Scenario: Checkpoint list formatting
- **WHEN** system displays checkpoint list
- **THEN** each entry shows checkpoint name, campaign, timestamp, size, and comment if present

#### Scenario: Permission denied for list
- **WHEN** user without list permissions attempts `/foothold list`
- **THEN** system displays ephemeral error message indicating insufficient permissions

### Requirement: System SHALL provide /foothold delete command

The system SHALL provide a `/foothold delete` Discord slash command to remove a checkpoint.

#### Scenario: Delete with checkpoint selection
- **WHEN** user executes `/foothold delete` with server and checkpoint parameters
- **THEN** system prompts for confirmation before deletion

#### Scenario: Delete confirmation required
- **WHEN** user confirms deletion via Discord button or modal
- **THEN** system deletes the checkpoint file and displays success message

#### Scenario: Delete cancellation
- **WHEN** user cancels deletion confirmation
- **THEN** system aborts deletion and displays cancellation message

#### Scenario: Delete success response
- **WHEN** checkpoint deletion completes successfully
- **THEN** system displays confirmation embed with deleted checkpoint name

#### Scenario: Delete failure response
- **WHEN** checkpoint deletion fails due to error
- **THEN** system displays error embed with failure reason

#### Scenario: Permission denied for delete
- **WHEN** user without delete permissions attempts `/foothold delete`
- **THEN** system displays ephemeral error message indicating insufficient permissions

### Requirement: Commands SHALL use interactive Discord UI elements

The system SHALL leverage Discord's interactive UI capabilities for enhanced user experience.

#### Scenario: Autocomplete provides real-time filtering
- **WHEN** user types in any autocomplete field
- **THEN** system filters and updates suggestions in real-time based on input

#### Scenario: Server selection uses transformer
- **WHEN** server parameter is required
- **THEN** system uses DCSServerBot ServerTransformer for server selection with autocomplete

#### Scenario: Select menus for multi-option choices
- **WHEN** user needs to select from limited options
- **THEN** system displays Discord select menu component

#### Scenario: Buttons for confirmation actions
- **WHEN** user action requires confirmation (restore, delete)
- **THEN** system displays Discord buttons for confirm/cancel

#### Scenario: Modals for text input
- **WHEN** user needs to provide multi-line input or complex data
- **THEN** system displays Discord modal with appropriate input fields

#### Scenario: Ephemeral error messages
- **WHEN** user encounters permission denied or validation error
- **THEN** system displays ephemeral message visible only to user

#### Scenario: Rich embeds for responses
- **WHEN** command completes successfully or fails
- **THEN** system displays formatted Discord embed with appropriate colors, icons, and fields

### Requirement: Commands SHALL integrate with DCSServerBot framework

The system SHALL follow DCSServerBot plugin conventions for command implementation.

#### Scenario: Commands use @command decorator
- **WHEN** Discord command is defined
- **THEN** system uses DCSServerBot @command decorator for registration

#### Scenario: Commands require guild context
- **WHEN** command is invoked
- **THEN** system enforces @app_commands.guild_only() to prevent DM usage

#### Scenario: Commands use ServerTransformer
- **WHEN** server parameter is needed
- **THEN** system uses app_commands.Transform with utils.ServerTransformer

#### Scenario: Commands defer responses for long operations
- **WHEN** command operation takes more than 3 seconds
- **THEN** system calls interaction.response.defer(thinking=True) before processing

#### Scenario: Commands follow DCSServerBot naming convention
- **WHEN** commands are registered with Discord
- **THEN** commands appear under `/foothold` command group

#### Scenario: Commands handle interaction lifecycle
- **WHEN** command is invoked
- **THEN** system properly manages interaction response, followup, and error handling

#### Scenario: Commands log operations
- **WHEN** command executes
- **THEN** system logs command invocation, user, parameters, and result to plugin logger

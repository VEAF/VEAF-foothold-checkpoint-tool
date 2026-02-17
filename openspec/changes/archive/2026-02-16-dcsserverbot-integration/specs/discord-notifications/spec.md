## Purpose

This capability provides Discord notifications for checkpoint operations, sending rich embeds to configured channels on save, restore, delete events, and failures. Notifications keep team members informed of checkpoint activities and provide audit trail.

## ADDED Requirements

### Requirement: System SHALL send notifications to configured Discord channel

The system SHALL send notification messages to the Discord channel specified in plugin configuration for checkpoint events.

#### Scenario: Notification sent to correct channel
- **WHEN** a checkpoint event occurs
- **THEN** system sends notification to channel specified in config['notifications']['channel']

#### Scenario: Channel lookup by name
- **WHEN** configuration specifies channel by name
- **THEN** system resolves channel by searching guild channels for matching name

#### Scenario: Channel lookup by ID
- **WHEN** configuration specifies channel by numeric ID
- **THEN** system resolves channel directly using Discord channel ID

#### Scenario: Channel not found error
- **WHEN** configured notification channel does not exist in guild
- **THEN** system logs error and skips notification without failing operation

#### Scenario: Multiple guild support
- **WHEN** bot operates in multiple guilds
- **THEN** system sends notifications to channel in guild where command was invoked

### Requirement: System SHALL send notifications for save events

The system SHALL send notification embeds when checkpoint save operations complete successfully.

#### Scenario: Save success notification
- **WHEN** checkpoint save completes successfully
- **THEN** system sends green embed with title "📦 Checkpoint Saved", campaign name, checkpoint name, and file size

#### Scenario: Save notification includes operation metadata
- **WHEN** save notification is sent
- **THEN** embed includes fields for checkpoint name, campaign, server, size, and comment if provided

#### Scenario: Save notification shows user attribution
- **WHEN** save notification is sent
- **THEN** embed footer shows username and avatar of user who initiated save

#### Scenario: Save notification disabled in config
- **WHEN** config['notifications']['on_save'] is false
- **THEN** system skips save notification

### Requirement: System SHALL send notifications for restore events  

The system SHALL send notification embeds when checkpoint restore operations complete successfully.

#### Scenario: Restore success notification
- **WHEN** checkpoint restore completes successfully
- **THEN** system sends blue embed with title "♻️ Checkpoint Restored", campaign name, and checkpoint name

#### Scenario: Restore notification includes auto-backup info
- **WHEN** restore was preceded by auto-backup
- **THEN** embed includes field showing auto-backup checkpoint name and location

#### Scenario: Restore notification shows file changes
- **WHEN** restore notification is sent
- **THEN** embed includes count of files restored and renamed files if any

#### Scenario: Restore notification shows user attribution
- **WHEN** restore notification is sent
- **THEN** embed footer shows username and avatar of user who initiated restore

#### Scenario: Restore notification disabled in config
- **WHEN** config['notifications']['on_restore'] is false
- **THEN** system skips restore notification

### Requirement: System SHALL send notifications for delete events

The system SHALL send notification embeds when checkpoint delete operations complete successfully.

#### Scenario: Delete success notification
- **WHEN** checkpoint delete completes successfully
- **THEN** system sends orange embed with title "🗑️ Checkpoint Deleted", checkpoint name, and campaign

#### Scenario: Delete notification shows user attribution
- **WHEN** delete notification is sent
- **THEN** embed footer shows username and avatar of user who initiated delete

#### Scenario: Delete notification includes warning
- **WHEN** delete notification is sent
- **THEN** embed includes warning field indicating deletion is permanent

#### Scenario: Delete notification disabled in config
- **WHEN** config['notifications']['on_delete'] is false
- **THEN** system skips delete notification

### Requirement: System SHALL send notifications for operation failures

The system SHALL send notification embeds when checkpoint operations fail with errors.

#### Scenario: Failure notification for any operation
- **WHEN** checkpoint operation (save/restore/delete) fails with exception
- **THEN** system sends red embed with title "❌ Operation Failed", operation type, and error message

#### Scenario: Failure notification includes error details
- **WHEN** failure notification is sent
- **THEN** embed includes fields for operation, campaign, server, and formatted error traceback

#### Scenario: Failure notification shows user attribution
- **WHEN** failure notification is sent
- **THEN** embed footer shows username and avatar of user who initiated failed operation

#### Scenario: Failure notification includes suggested actions
- **WHEN** failure is due to known error type
- **THEN** embed includes field with troubleshooting suggestions

#### Scenario: Failure notification disabled in config
- **WHEN** config['notifications']['on_failure'] is false
- **THEN** system skips failure notification

### Requirement: System SHALL format notifications as rich Discord embeds

The system SHALL use Discord's embed format with appropriate styling for all notifications.

#### Scenario: Embed uses appropriate color
- **WHEN** notification embed is created
- **THEN** embed uses green for success, blue for restore, orange for delete, red for error

#### Scenario: Embed includes timestamp
- **WHEN** notification embed is sent
- **THEN** embed timestamp field shows current UTC time

#### Scenario: Embed includes operation icon
- **WHEN** notification embed is created
- **THEN** embed title includes appropriate emoji (📦 save, ♻️ restore, 🗑️ delete, ❌ error)

#### Scenario: Embed fields use consistent formatting
- **WHEN** notification includes multiple data fields
- **THEN** fields use consistent naming and value formatting

#### Scenario: Embed includes server name
- **WHEN** notification is for server-specific operation
- **THEN** embed includes field or footer showing DCS server name

#### Scenario: Embed footer shows user with avatar
- **WHEN** notification includes user attribution
- **THEN** embed footer text shows username and icon_url shows user avatar

### Requirement: System SHALL handle notification errors gracefully

The system SHALL continue checkpoint operations even if notification delivery fails.

#### Scenario: Notification failure does not block operation
- **WHEN** notification send fails with exception
- **THEN** system logs error and continues without failing checkpoint operation

#### Scenario: Missing permissions logged
- **WHEN** bot lacks permissions to send to notification channel
- **THEN** system logs warning about missing send message permissions

#### Scenario: Invalid channel configuration logged
- **WHEN** notification channel configuration is invalid or missing
- **THEN** system logs error with helpful message about correct configuration format

#### Scenario: Rate limit handling
- **WHEN** Discord rate limits notification sends
- **THEN** system respects rate limits and queues notification for retry

#### Scenario: Network error handling
- **WHEN** notification fails due to network connectivity
- **THEN** system logs error and continues without retrying

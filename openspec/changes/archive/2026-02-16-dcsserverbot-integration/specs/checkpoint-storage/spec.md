## MODIFIED Requirements

### Requirement: System SHALL create checkpoint as timestamped ZIP archive

The system SHALL create checkpoints as ZIP files named `{campaign}_{YYYY-MM-DD_HH-MM-SS}.zip` containing all campaign files, Foothold_Ranks.lua, and metadata.json. The system SHALL support optional event hooks for Discord notifications.

#### Scenario: Save single campaign checkpoint
- **WHEN** user saves a checkpoint for the "afghanistan" campaign
- **THEN** the system creates a ZIP file named like `afghanistan_2024-02-13_14-30-00.zip`

#### Scenario: Timestamp uniqueness
- **WHEN** multiple checkpoints are created for the same campaign
- **THEN** each checkpoint has a unique timestamp in the filename

#### Scenario: Checkpoint storage location
- **WHEN** a checkpoint is created
- **THEN** the ZIP file is saved in the directory specified by `checkpoints_dir` in configuration

#### Scenario: Event hooks trigger on save start
- **WHEN** checkpoint save operation starts and hooks.on_save_start is provided
- **THEN** system calls await hooks.on_save_start(campaign) before file operations

#### Scenario: Event hooks trigger on save progress
- **WHEN** checkpoint is being created and hooks.on_save_progress is provided
- **THEN** system calls await hooks.on_save_progress(current, total) for progress updates

#### Scenario: Event hooks trigger on save complete
- **WHEN** checkpoint save completes successfully and hooks.on_save_complete is provided
- **THEN** system calls await hooks.on_save_complete(checkpoint_path) with result

#### Scenario: Event hooks trigger on error
- **WHEN** checkpoint save fails with exception and hooks.on_error is provided
- **THEN** system calls await hooks.on_error(exception) before re-raising

#### Scenario: Save without event hooks
- **WHEN** checkpoint is created with hooks=None (CLI mode)
- **THEN** system creates checkpoint normally without calling any callbacks

## ADDED Requirements

### Requirement: System SHALL accept optional EventHooks for operation callbacks

The system SHALL accept optional EventHooks parameter containing async callbacks for notifying external systems (Discord) of checkpoint operation events.

#### Scenario: EventHooks dataclass structure
- **WHEN** EventHooks is defined
- **THEN** it contains optional callable fields: on_save_start, on_save_progress, on_save_complete, on_error

#### Scenario: All hooks are optional
- **WHEN** EventHooks is instantiated
- **THEN** all callback fields default to None and are individually optional

#### Scenario: Hooks are async callables
- **WHEN** hook callback is provided
- **THEN** it is an async function returning Awaitable[None]

#### Scenario: Hook errors do not fail operation
- **WHEN** event hook callback raises exception
- **THEN** system logs hook error and continues checkpoint operation

#### Scenario: Hooks parameter defaults to None
- **WHEN** checkpoint operation is called without hooks parameter
- **THEN** system treats it as hooks=None and skips all callbacks

### Requirement: System SHALL invoke delete event hooks

The system SHALL trigger event hooks when checkpoint delete operations occur.

#### Scenario: Event hooks trigger on delete start
- **WHEN** checkpoint delete operation starts and hooks.on_delete_start is provided
- **THEN** system calls await hooks.on_delete_start(checkpoint_name) before deletion

#### Scenario: Event hooks trigger on delete complete
- **WHEN** checkpoint delete completes successfully and hooks.on_delete_complete is provided
- **THEN** system calls await hooks.on_delete_complete(checkpoint_name)

#### Scenario: Event hooks trigger on delete error
- **WHEN** checkpoint delete fails with exception and hooks.on_error is provided
- **THEN** system calls await hooks.on_error(exception) before re-raising

#### Scenario: Delete without event hooks
- **WHEN** checkpoint is deleted with hooks=None (CLI mode)
- **THEN** system deletes checkpoint normally without calling any callbacks

## 1. Configuration Migration

- [x] 1.1 Create campaigns.yaml schema file
- [x] 1.2 Extract campaigns section from existing config.yaml to campaigns.yaml
- [x] 1.3 Update config.yaml to add campaigns_file reference
- [x] 1.4 Update Config model to support campaigns_file field
- [x] 1.5 Implement load_campaigns() function in core/config.py
- [x] 1.6 Update CLI config loading to read campaigns from separate file
- [x] 1.7 Add validation for campaigns_file existence and readability
- [x] 1.8 Create example campaigns.yaml in project root
- [x] 1.9 Update config.yaml.example with campaigns_file reference

## 2. Core Library Event Hooks System

- [x] 2.1 Create EventHooks dataclass in core/events.py
- [x] 2.2 Add on_save_start, on_save_progress, on_save_complete callbacks to EventHooks
- [x] 2.3 Add on_restore_start, on_restore_progress, on_restore_complete callbacks to EventHooks
- [x] 2.4 Add on_delete_start, on_delete_complete callbacks to EventHooks
- [x] 2.5 Add on_backup_complete callback to EventHooks
- [x] 2.6 Add on_error callback to EventHooks
- [x] 2.7 Implement safe hook invocation wrapper (async, catches exceptions, logs errors)
- [x] 2.8 Add type hints for all hook callbacks (Callable[[...], Awaitable[None]])

## 3. Core Library Async Refactoring

- [x] 3.1 Convert save_checkpoint() to async def
- [x] 3.2 Add optional hooks parameter to save_checkpoint()
- [x] 3.3 Integrate EventHooks calls in save_checkpoint() at appropriate points
- [x] 3.4 Convert restore_checkpoint() to async def
- [x] 3.5 Add optional hooks parameter to restore_checkpoint()
- [x] 3.6 Integrate EventHooks calls in restore_checkpoint() at appropriate points
- [x] 3.7 Convert delete_checkpoint() to async def
- [x] 3.8 Add optional hooks parameter to delete_checkpoint()
- [x] 3.9 Integrate EventHooks calls in delete_checkpoint() at appropriate points
- [x] 3.10 Convert list_checkpoints() to async def
- [x] 3.11 Convert import_checkpoint() to async def
- [ ] 3.12 Add aiofiles dependency for async file operations (optional optimization)
- [ ] 3.13 Update all core tests to use asyncio.run() or @pytest.mark.asyncio

## 4. Auto-Backup Feature

- [x] 4.1 Implement create_auto_backup() function in core/storage.py
- [x] 4.2 Add auto_backup parameter to restore_checkpoint() (default True)
- [x] 4.3 Integrate auto-backup creation before restore operations
- [x] 4.4 Add auto-backup naming convention: {campaign}_backup_{timestamp}.zip
- [x] 4.5 Include auto-backup reference in restore metadata/comment
- [x] 4.6 Handle auto-backup failures (abort restore on backup failure)
- [x] 4.7 Trigger on_backup_complete hook when auto-backup succeeds
- [ ] 4.8 Add tests for auto-backup creation and failure scenarios

## 5. CLI Async Wrapper Updates

- [x] 5.1 Add asyncio import to cli.py
- [x] 5.2 Wrap save command with asyncio.run(save_checkpoint(...))
- [x] 5.3 Wrap restore command with asyncio.run(restore_checkpoint(...))
- [x] 5.4 Wrap list command with asyncio.run(list_checkpoints(...))
- [x] 5.5 Wrap delete command with asyncio.run(delete_checkpoint(...))
- [x] 5.6 Wrap import command with asyncio.run(import_checkpoint(...))
- [x] 5.7 Ensure all CLI calls pass hooks=None
- [x] 5.8 Add --auto-backup / --no-auto-backup flags to restore command
- [x] 5.9 Add --details flag to list command
- [x] 5.10 Update CLI tests to verify async wrapping works correctly

## 6. Plugin Directory Structure

- [x] 6.1 Create src/foothold_checkpoint/plugin/ directory
- [x] 6.2 Create plugin/__init__.py with package metadata
- [x] 6.3 Create plugin/version.py with __version__ = "2.0.0"
- [x] 6.4 Create plugin/commands.py skeleton
- [x] 6.5 Create plugin/listener.py skeleton
- [x] 6.6 Create plugin/permissions.py skeleton
- [x] 6.7 Create plugin/notifications.py skeleton
- [x] 6.8 Create plugin/schemas/ directory
- [x] 6.9 Create plugin/schemas/foothold_schema.yaml

## 7. Plugin Configuration Schema

- [x] 7.1 Define campaigns_file field in foothold_schema.yaml
- [x] 7.2 Define checkpoints_dir field in foothold_schema.yaml
- [x] 7.3 Define permissions section schema (save, restore, list, delete as string arrays)
- [x] 7.4 Define notifications section schema (channel, on_save, on_restore, on_delete, on_failure)
- [x] 7.5 Mark campaigns_file and checkpoints_dir as required fields
- [x] 7.6 Add type validations for all fields
- [x] 7.7 Create example config/plugins/foothold.yaml for documentation

## 8. Plugin Base Class Implementation

- [x] 8.1 Implement Foothold(Plugin[FootholdEventListener]) class in commands.py
- [x] 8.2 Implement __init__ method with super().__init__(bot, listener) call
- [x] 8.3 Implement cog_load() lifecycle hook
- [x] 8.4 Implement cog_unload() lifecycle hook
- [x] 8.5 Implement install() lifecycle hook (if needed)
- [x] 8.6 Add setup() function for bot registration
- [x] 8.7 Initialize plugin logger via self.log
- [x] 8.8 Load config via self.get_config() in cog_load()

## 9. Plugin Permissions System

- [x] 9.1 Implement check_permission() method in commands.py
- [x] 9.2 Load permissions from config['permissions'] section
- [x] 9.3 Check user roles against permitted roles for operation
- [ ] 9.4 Implement case-insensitive role name matching
- [x] 9.5 Support multiple permitted roles per operation (OR logic)
- [x] 9.6 Implement administrator override (Discord Administrator permission)
- [ ] 9.7 Implement bot owner override
- [ ] 9.8 Log permission checks and overrides
- [x] 9.9 Create format_permission_denied() helper for error messages
- [ ] 9.10 Add unit tests for permission checking logic

## 10. Discord Notifications System

- [x] 10.1 Implement NotificationManager class in notifications.py
- [x] 10.2 Implement get_notification_channel() method (lookup by name or ID)
- [x] 10.3 Implement create_save_embed() for save notifications
- [x] 10.4 Implement create_restore_embed() for restore notifications
- [x] 10.5 Implement create_delete_embed() for delete notifications
- [x] 10.6 Implement create_error_embed() for failure notifications
- [x] 10.7 Add timestamp and user attribution to all embeds
- [x] 10.8 Implement send_notification() method with error handling
- [x] 10.9 Check notification config flags (on_save, on_restore, etc.) before sending
- [x] 10.10 Handle missing channel gracefully (log warning, don't fail operation)
- [x] 10.11 Handle missing permissions gracefully (log warning, don't fail operation)
- [ ] 10.12 Add Discord rate limit handling
- [ ] 10.13 Add unit tests for embed creation and sending

## 11. Discord Commands - Base Infrastructure

- [x] 11.1 Add @command decorator to Foothold class commands
- [x] 11.2 Add @app_commands.guild_only() to all commands
- [ ] 11.3 Add @utils.app_has_role('DCS') base permission to all commands
- [ ] 11.4 Implement ServerTransformer parameter for all commands
- [ ] 11.5 Create campaign_autocomplete() function for campaign parameter
- [ ] 11.6 Create checkpoint_autocomplete() function for checkpoint parameter
- [x] 11.7 Implement interaction.response.defer(thinking=True) for long operations
- [x] 11.8 Implement error handling wrapper for all commands
- [x] 11.9 Add command execution logging (user, server, params, result)

## 12. Discord Commands - /foothold save Implementation

- [x] 12.1 Define save command with description
- [x] 12.2 Add server parameter with ServerTransformer
- [x] 12.3 Add campaign parameter with autocomplete
- [x] 12.4 Add optional name parameter
- [x] 12.5 Add optional comment parameter
- [x] 12.6 Implement permission check for 'save' operation
- [x] 12.7 Create EventHooks for Discord progress updates
- [x] 12.8 Call save_checkpoint() from core library with hooks
- [x] 12.9 Create success embed response
- [x] 12.10 Create failure embed response
- [x] 12.11 Trigger notification on save complete
- [x] 12.12 Handle exceptions and send error notifications

## 13. Discord Commands - /foothold restore Implementation

- [x] 13.1 Define restore command with description
- [x] 13.2 Add server parameter with ServerTransformer
- [x] 13.3 Add checkpoint parameter with autocomplete
- [x] 13.4 Add optional auto_backup flag (default True)
- [x] 13.5 Implement permission check for 'restore' operation
- [ ] 13.6 Implement Discord confirmation modal or buttons
- [x] 13.7 Create EventHooks for Discord progress updates
- [x] 13.8 Call restore_checkpoint() from core library with hooks and auto_backup flag
- [x] 13.9 Create success embed response including auto-backup info
- [x] 13.10 Create failure embed response
- [x] 13.11 Trigger notification on restore complete
- [x] 13.12 Handle exceptions and send error notifications

## 14. Discord Commands - /foothold list Implementation

- [x] 14.1 Define list command with description
- [x] 14.2 Add server parameter with ServerTransformer
- [x] 14.3 Add optional campaign filter parameter with autocomplete
- [x] 14.4 Add optional details flag
- [x] 14.5 Implement permission check for 'list' operation
- [x] 14.6 Call list_checkpoints() from core library with filters
- [x] 14.7 Format checkpoint list as Discord embed with fields
- [ ] 14.8 Implement pagination if checkpoint count exceeds limit
- [ ] 14.9 Add navigation buttons for paginated results
- [x] 14.10 Handle empty checkpoint list with helpful message
- [x] 14.11 Display checkpoint details when --details flag is used

## 15. Discord Commands - /foothold delete Implementation

- [x] 15.1 Define delete command with description
- [x] 15.2 Add server parameter with ServerTransformer
- [x] 15.3 Add checkpoint parameter with autocomplete
- [x] 15.4 Implement permission check for 'delete' operation\n- [ ] 15.5 Implement Discord confirmation buttons
- [ ] 15.6 Create EventHooks for notifications
- [x] 15.7 Call delete_checkpoint() from core library on confirmation
- [x] 15.8 Create success embed response
- [ ] 15.9 Create cancellation message for aborted deletes
- [x] 15.10 Create failure embed response
- [x] 15.11 Trigger notification on delete complete
- [x] 15.12 Handle exceptions and send error notifications

## 16. EventListener Implementation

- [ ] 16.1 Implement FootholdEventListener class in listener.py
- [ ] 16.2 Extend EventListener base class
- [ ] 16.3 Add stub methods for future DCS event integration (optional for v2.0.0)
- [ ] 16.4 Add docstrings explaining EventListener purpose
- [ ] 16.5 Keep implementation minimal since no DCS events needed for v2.0.0

## 17. Poetry Dependency Management

- [ ] 17.1 Add discord-py to pyproject.toml
- [ ] 17.2 Create [tool.poetry.group.plugin] optional group
- [ ] 17.3 Move discord-py to plugin dependency group
- [ ] 17.4 Add aiofiles to dependencies (if using async file I/O)
- [ ] 17.5 Update poetry.lock with new dependencies
- [ ] 17.6 Test CLI-only install (poetry install without --with plugin)
- [ ] 17.7 Test full install (poetry install --with plugin)
- [ ] 17.8 Verify discord.py not required for CLI-only usage

## 18. Plugin Packaging Script

- [ ] 18.1 Create scripts/build_plugin.py
- [ ] 18.2 Implement ZIP creation for plugin/ directory
- [ ] 18.3 Include commands.py, listener.py, version.py, __init__.py in ZIP
- [ ] 18.4 Include schemas/ directory in ZIP
- [ ] 18.5 Generate requirements.txt with plugin dependencies only
- [ ] 18.6 Include README_PLUGIN.md with installation instructions
- [ ] 18.7 Output ZIP to dist/foothold-plugin-v2.0.0.zip
- [ ] 18.8 Test ZIP extraction and structure
- [ ] 18.9 Update CI/CD to run build_plugin.py on release

## 19. Testing - Core Library Tests

- [ ] 19.1 Update test_storage.py tests to use asyncio
- [ ] 19.2 Add tests for save_checkpoint() with EventHooks
- [ ] 19.3 Add tests for save_checkpoint() without EventHooks (CLI mode)
- [ ] 19.4 Add tests for restore_checkpoint() with EventHooks
- [ ] 19.5 Add tests for restore_checkpoint() auto-backup enabled
- [ ] 19.6 Add tests for restore_checkpoint() auto-backup disabled
- [ ] 19.7 Add tests for delete_checkpoint() with EventHooks
- [ ] 19.8 Add tests for hook error handling (hook raises exception)
- [ ] 19.9 Add tests for campaigns.yaml loading
- [ ] 19.10 Add tests for Config with campaigns_file reference
- [ ] 19.11 Verify all existing 304 tests still pass

## 20. Testing - Plugin Tests

- [ ] 20.1 Create tests/plugin/ directory
- [ ] 20.2 Create test_commands.py for command tests
- [ ] 20.3 Create test_permissions.py for permission tests
- [ ] 20.4 Create test_notifications.py for notification tests
- [ ] 20.5 Mock discord.py components (Interaction, Guild, User, Channel)
- [ ] 20.6 Test check_permission() with various role configurations
- [ ] 20.7 Test command permission checks (allowed and denied)
- [ ] 20.8 Test embed creation for all notification types
- [ ] 20.9 Test notification channel lookup (by name and ID)
- [ ] 20.10 Test notification error handling (missing channel, permissions)
- [ ] 20.11 Test autocomplete functions (campaigns, checkpoints)
- [ ] 20.12 Test command error handling and graceful failures
- [ ] 20.13 Achieve >90% coverage on plugin code

## 21. Testing - Integration Tests

- [ ] 21.1 Create test_plugin_integration.py
- [ ] 21.2 Test Plugin class initialization
- [ ] 21.3 Test cog_load() and cog_unload() lifecycle
- [ ] 21.4 Test config loading from foothold.yaml
- [ ] 21.5 Test campaigns.yaml loading via config reference
- [ ] 21.6 Test ServerTransformer integration
- [ ] 21.7 Test end-to-end save command flow (mocked Discord)
- [ ] 21.8 Test end-to-end restore command flow with auto-backup
- [ ] 21.9 Test end-to-end list command flow with pagination
- [ ] 21.10 Test end-to-end delete command flow with confirmation

## 22. Documentation - Migration Guide

- [ ] 22.1 Create MIGRATION_v2.0.0.md
- [ ] 22.2 Document config.yaml → campaigns.yaml migration steps
- [ ] 22.3 Provide before/after config examples
- [ ] 22.4 Document CLI backward compatibility notes
- [ ] 22.5 Document breaking changes (async functions, EventHooks parameter)
- [ ] 22.6 Document plugin installation steps
- [ ] 22.7 Document foothold.yaml configuration
- [ ] 22.8 Document permissions configuration
- [ ] 22.9 Document notifications configuration
- [ ] 22.10 Add troubleshooting section

## 23. Documentation - User Guide Updates

- [ ] 23.1 Update USERS.md with Discord commands section
- [ ] 23.2 Document /foothold save command with examples
- [ ] 23.3 Document /foothold restore command with examples
- [ ] 23.4 Document /foothold list command with examples
- [ ] 23.5 Document /foothold delete command with examples
- [ ] 23.6 Add screenshots of Discord command usage
- [ ] 23.7 Document autocomplete features
- [ ] 23.8 Document permission requirements per command
- [ ] 23.9 Document notification behavior
- [ ] 23.10 Add FAQ section for common Discord plugin questions

## 24. Documentation - Plugin README

- [ ] 24.1 Create README_PLUGIN.md
- [ ] 24.2 Document plugin installation from ZIP
- [ ] 24.3 Document plugin installation via Poetry
- [ ] 24.4 Document required configuration files
- [ ] 24.5 Document foothold.yaml configuration options
- [ ] 24.6 Document campaigns.yaml setup
- [ ] 24.7 Document permissions and role setup
- [ ] 24.8 Document notification channel setup
- [ ] 24.9 Add troubleshooting common plugin issues
- [ ] 24.10 Add example configurations

## 25. Documentation - Developer Guide

- [ ] 25.1 Update CONTRIBUTING.md with plugin development section
- [ ] 25.2 Document how to test plugin locally with DCSServerBot
- [ ] 25.3 Document EventHooks system for future developers
- [ ] 25.4 Document async/await patterns in codebase
- [ ] 25.5 Document plugin architecture and components
- [ ] 25.6 Document how to add new Discord commands
- [ ] 25.7 Document how to extend notification types

## 26. Documentation - Release Notes

- [ ] 26.1 Update CHANGELOG.md with v2.0.0 entry
- [ ] 26.2 Document all added features (Discord integration)
- [ ] 26.3 Document all changed features (async core, campaigns.yaml)
- [ ] 26.4 Document breaking changes prominently
- [ ] 26.5 Add migration guide reference
- [ ] 26.6 Update RELEASE_NOTES.md with v2.0.0 section
- [ ] 26.7 Include Discord command examples in release notes
- [ ] 26.8 Document quality metrics (test count, coverage)
- [ ] 26.9 Add upgrade instructions

## 27. Configuration Examples

- [ ] 27.1 Update config.yaml.example with campaigns_file reference
- [ ] 27.2 Create campaigns.yaml.example with all VEAF campaigns
- [ ] 27.3 Create config/plugins/foothold.yaml.example
- [ ] 27.4 Document all configuration options with inline comments
- [ ] 27.5 Provide minimal and full configuration examples
- [ ] 27.6 Add configuration validation examples

## 28. CI/CD Updates

- [ ] 28.1 Update GitHub Actions workflow for v2.0.0
- [ ] 28.2 Add plugin build step to CI pipeline
- [ ] 28.3 Test both CLI-only and full install in CI
- [ ] 28.4 Run tests with and without plugin dependencies
- [ ] 28.5 Build plugin ZIP on release
- [ ] 28.6 Upload plugin ZIP as release asset
- [ ] 28.7 Verify Discord dependency is optional

## 29. Manual Testing

- [ ] 29.1 Test CLI with migrated configuration
- [ ] 29.2 Test all CLI commands (save, restore, list, delete, import)
- [ ] 29.3 Test CLI with --auto-backup and --no-auto-backup flags
- [ ] 29.4 Install plugin in local DCSServerBot instance
- [ ] 29.5 Test plugin loads successfully
- [ ] 29.6 Test /foothold save command in Discord
- [ ] 29.7 Test /foothold restore command with confirmation
- [ ] 29.8 Test /foothold list command with filters
- [ ] 29.9 Test /foothold delete command with confirmation
- [ ] 29.10 Test autocomplete for campaigns and checkpoints
- [ ] 29.11 Test permissions with different Discord roles
- [ ] 29.12 Test notifications appear in configured channel
- [ ] 29.13 Test error notifications for failures
- [ ] 29.14 Test plugin reload without bot restart
- [ ] 29.15 Verify auto-backup creation before restore

## 30. Release Preparation

- [ ] 30.1 Update version to 2.0.0 in pyproject.toml
- [ ] 30.2 Update version to 2.0.0 in src/foothold_checkpoint/__init__.py
- [ ] 30.3 Update version to 2.0.0 in plugin/version.py
- [ ] 30.4 Verify all tests pass (aim for 350+ tests)
- [ ] 30.5 Verify code coverage >90%
- [ ] 30.6 Run mypy type checking (no errors)
- [ ] 30.7 Run black formatting
- [ ] 30.8 Run ruff linting
- [ ] 30.9 Build package with poetry build
- [ ] 30.10 Build plugin ZIP with build_plugin.py
- [ ] 30.11 Create git tag v2.0.0
- [ ] 30.12 Push tag to GitHub
- [ ] 30.13 Create GitHub Release with plugin ZIP asset
- [ ] 30.14 Update ROADMAP.md to mark v2.0.0 as completed

## Why

VEAF uses Discord as the primary communication platform for DCS operations. Currently, users must SSH into servers or use the CLI directly to manage checkpoints, which is cumbersome and limits accessibility. Integrating checkpoint management into DCSServerBot enables Discord-based checkpoint operations, making saves and restores accessible to authorized users without server access, improving operational efficiency and collaboration.

## What Changes

- **New DCSServerBot Plugin**: Create native plugin for [DCSServerBot](https://github.com/Special-K-s-Flightsim-Bots/DCSServerBot) framework
- **Discord Commands**: Implement slash commands for checkpoint operations (`/checkpoint save`, `/checkpoint restore`, `/checkpoint list`, `/checkpoint delete`)
- **Discord Notifications**: Send Discord embeds for checkpoint events (save success/failure, restore completion, integrity warnings)
- **Role-Based Access Control**: Integrate with Discord roles to control who can save/restore/delete checkpoints
- **Plugin Lifecycle Management**: Handle plugin initialization, configuration, bot integration, and graceful shutdown
- **Event-Driven Architecture**: Use async event handlers for checkpoint operations triggered from Discord
- **Refactor CLI Core**: Extract core checkpoint logic into reusable library functions callable from both CLI and plugin
- **Configuration Extension**: Add plugin-specific configuration (Discord webhook URLs, role permissions, notification preferences)

## Capabilities

### New Capabilities

- `discord-commands`: Discord slash commands for checkpoint management operations with interactive embeds and parameter validation
- `discord-notifications`: Discord event notifications for checkpoint operations with rich embeds, status updates, and error reports
- `role-based-access`: Permission system using Discord roles to control checkpoint operation access (separate permissions for save, restore, delete)
- `plugin-integration`: DCSServerBot plugin architecture, lifecycle management, configuration, and event integration

### Modified Capabilities

- `checkpoint-storage`: Add event hooks for Discord notifications on save/restore/delete operations
- `checkpoint-restoration`: Support async operation with progress callbacks for Discord updates
- `cli-interface`: Refactor to use shared core library (no CLI-specific business logic, pure orchestration)

## Impact

**New Components:**
- `src/foothold_checkpoint/plugin/` - DCSServerBot plugin implementation
- `src/foothold_checkpoint/plugin/commands.py` - Discord command handlers
- `src/foothold_checkpoint/plugin/notifications.py` - Discord notification system
- `src/foothold_checkpoint/plugin/permissions.py` - Role-based access control
- `src/foothold_checkpoint/core/events.py` - Event system for checkpoint operations
- `plugins.yaml` - DCSServerBot plugin manifest

**Modified Components:**
- `src/foothold_checkpoint/cli.py` - Refactor to use core library functions
- `src/foothold_checkpoint/core/storage.py` - Add event hooks and async support
- `src/foothold_checkpoint/core/config.py` - Extend with plugin configuration

**Dependencies:**
- `discord.py` - Discord API interactions
- `DCSServerBot` framework - Plugin integration
- Async support throughout core modules

**Breaking Changes:**
- **BREAKING**: Core checkpoint functions now require event handler callbacks (optional but changes function signatures)
- **BREAKING**: Configuration format extended with plugin section (old configs still work but no plugin features)

**Testing:**
- Discord command integration tests with mock bot
- Permission system unit tests
- Event notification tests
- End-to-end plugin lifecycle tests
- Backward compatibility tests for CLI-only usage

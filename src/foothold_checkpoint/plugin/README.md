# DCSServerBot Plugin for Foothold Checkpoint Tool

This document provides installation and configuration instructions for using the Foothold Checkpoint Tool as a DCSServerBot plugin.

## Overview

The Foothold plugin integrates the Foothold Checkpoint Tool with DCSServerBot, providing Discord slash commands for managing campaign checkpoints directly from Discord.

### Features

- **Discord Commands**: `/foothold-checkpoint save`, `/restore`, `/list`, `/delete`
- **Role-Based Permissions**: Configure which Discord roles can execute each command
- **Rich Embeds**: Beautiful Discord embeds for command responses and notifications
- **Auto-Backup**: Automatic backup creation before restoring checkpoints
- **Notifications**: Configurable Discord notifications for checkpoint events
- **Server Integration**: Automatically detects Missions/Saves directory per DCS server
- **Interactive UI**: Discord buttons and dropdowns for better UX

## Documentation

This package includes comprehensive user documentation:

- **[PLUGIN_USER_MANUAL_EN.md](PLUGIN_USER_MANUAL_EN.md)** - Complete user guide in English for Discord bot users
- **[PLUGIN_USER_MANUAL_FR.md](PLUGIN_USER_MANUAL_FR.md)** - Guide utilisateur complet en français pour les utilisateurs du bot Discord
- **This README** - Technical documentation for server administrators

**For end users**: Share the user manual files with your Discord community to help them learn how to use the checkpoint commands.

## Installation

### Prerequisites

- DCSServerBot already installed
- Python 3.10+ (should already be configured with DCSSB)
- All required dependencies are already in DCSSB's `requirements.txt`:
  - `discord.py >= 2.6.4`
  - `pydantic >= 2.12.5`
  - `pyyaml` (via ruamel-yaml)

### Option 1: From Pre-built ZIP (Recommended)

**Step 1: Download or Build the Plugin ZIP**

**Option A: Download pre-built ZIP** (if available from releases)
- Download `foothold-checkpoint-plugin-vX.X.X.zip` from GitHub releases

**Option B: Build from source**
```powershell
cd D:\dev\_VEAF\VEAF-foothold-checkpoint-tool
python scripts\build_plugin.py
```

This creates `dist\foothold-checkpoint-plugin-vX.X.X.zip` containing:
- `foothold-checkpoint/` directory with all plugin code
- `foothold-checkpoint.yaml.example`
- `campaigns.yaml.example`
- `README.md` (technical documentation for admins)
- `PLUGIN_USER_MANUAL_EN.md` (user guide in English)
- `PLUGIN_USER_MANUAL_FR.md` (user guide in French)

**Step 2: Extract Plugin to DCSSB**

Extract the ZIP file to your DCSSB plugins directory:

```powershell
# Using PowerShell built-in extraction
cd D:\dev\_VEAF\VEAF-DCSServerBot\plugins
Expand-Archive -Path "path\to\foothold-checkpoint-plugin-vX.X.X.zip" -DestinationPath . -Force
```

Or manually extract the ZIP so that the `foothold-checkpoint/` directory ends up in `plugins/`.

This creates the following structure:
```
DCSServerBot/plugins/foothold-checkpoint/
├── __init__.py               # Plugin entry point (auto-generated)
├── py.typed                  # Type checking marker
├── commands.py               # Discord slash commands
├── formatters.py             # Discord embed formatting
├── listener.py               # Event listeners
├── notifications.py          # Discord notifications
├── permissions.py            # Permission checks
├── ui.py                     # Interactive UI components
├── version.py
├── schemas/                  # Pydantic config models
│   ├── __init__.py
│   └── plugin_config.py
└── core/                     # Core checkpoint functionality
    ├── __init__.py
    ├── campaign.py
    ├── checkpoint.py
    ├── config.py
    ├── events.py
    └── storage.py
```

> **Next**: After installation, proceed to the **Configuration** section below to enable and configure the plugin.

### Option 2: From Source (Development)

**Step 1: Clone Repository**

```powershell
cd D:\dev\_VEAF
git clone https://github.com/VEAF/VEAF-foothold-checkpoint-tool.git
```

**Step 2: Copy Plugin Files**

```powershell
# Create plugin directory
cd D:\dev\_VEAF\VEAF-DCSServerBot\plugins
mkdir foothold-checkpoint

# Copy core module
xcopy /E /I D:\dev\_VEAF\VEAF-foothold-checkpoint-tool\src\foothold_checkpoint\core D:\dev\_VEAF\VEAF-DCSServerBot\plugins\foothold-checkpoint\core

# Copy plugin module files
xcopy /E /I D:\dev\_VEAF\VEAF-foothold-checkpoint-tool\src\foothold_checkpoint\plugin\*.py D:\dev\_VEAF\VEAF-DCSServerBot\plugins\foothold-checkpoint\

# Copy schemas
xcopy /E /I D:\dev\_VEAF\VEAF-foothold-checkpoint-tool\src\foothold_checkpoint\plugin\schemas D:\dev\_VEAF\VEAF-DCSServerBot\plugins\foothold-checkpoint\schemas

# Copy py.typed marker
copy D:\dev\_VEAF\VEAF-foothold-checkpoint-tool\src\foothold_checkpoint\py.typed D:\dev\_VEAF\VEAF-DCSServerBot\plugins\foothold-checkpoint\
```

> **Next**: After installation, proceed to the **Configuration** section below to enable and configure the plugin.

## Configuration

### Overview

The Foothold Checkpoint plugin follows DCSServerBot's standard configuration pattern:

1. **Enable in main.yaml**: Add plugin to `opt_plugins` list (required for loading)
2. **Plugin Configuration**: `config/plugins/foothold-checkpoint.yaml` (configures the plugin behavior)
3. **Campaigns Definition**: `config/campaigns.yaml` (defines all campaign file structures)
4. **Bot Restart**: Required after adding/modifying configuration

### DCSServerBot Configuration Structure

DCSServerBot uses a hierarchical configuration system:

- **DEFAULT section**: Base configuration applied to all servers
- **Server-specific sections**: Override DEFAULT settings for specific servers (server names must match `servers.yaml`)
- **enabled**: Set to `true` to activate the plugin for a server, `false` to disable
- **opt_plugins**: List in `main.yaml` that controls which optional plugins are loaded

### Step 1: Enable the Plugin in main.yaml

**This is the critical first step** - without this, the plugin will not be loaded at all.

Edit `config/main.yaml` and add `foothold-checkpoint` to the `opt_plugins` list:

```yaml
# config/main.yaml
guild_id: YOUR_GUILD_ID
autoupdate: false
# ... other settings ...

opt_plugins:                          # Optional plugins to load
  - tacview
  - discord
  - restapi
  - commands
  - backup
  - foothold-checkpoint               # Add this line
```

> **Important**: The plugin name in `opt_plugins` must be `foothold-checkpoint` (with hyphen), matching the directory name in `plugins/`.

### Step 2: Create Plugin Configuration

Copy the example configuration:

```powershell
cd D:\dev\_VEAF\VEAF-DCSServerBot
cp plugins\foothold-checkpoint\foothold-checkpoint.yaml.example config\plugins\foothold-checkpoint.yaml
```

Edit `config/plugins/foothold-checkpoint.yaml`:

```yaml
##############################################################
# Configuration for the Foothold Checkpoint plugin          #
##############################################################

DEFAULT:
  # Enable or disable the plugin
  enabled: true
  
  # Path to campaigns.yaml file (required)
  campaigns_file: ./campaigns.yaml
  
  # Directory where checkpoints are stored
  checkpoints_dir: ./checkpoints
  
  # Discord role-based permissions
  permissions:
    save:
      - DCS Admin
      - Mission Designer
    restore:
      - DCS Admin
    list:
      - DCS Admin
      - Mission Designer
      - Mission Controller
    delete:
      - DCS Admin
  
  # Discord notifications
  notifications:
    # Use channel ID (recommended) or channel name
    # To get ID: Right-click channel → Copy Channel ID (requires Developer Mode)
    channel: 1234567890123456789  # Replace with your channel ID
    on_save: true
    on_restore: true
    on_delete: true
    on_error: true

# Per-server configuration (optional)
# Server names must match your servers.yaml

# Example: Disable for specific server
# DCS.release_server:
#   enabled: false

# Example: Different permissions per server
# DCS.production_server:
#   permissions:
#     restore:
#       - Admin  # More restrictive
```

**Configuration Notes:**

- **enabled**: Set to `false` to disable the plugin without removing it
- **campaigns_file**: Path to campaigns configuration (see Step 3)
- **checkpoints_dir**: Where checkpoint ZIP files are stored
- **notifications.channel**: Replace `1234567890123456789` with your actual Discord channel ID or use channel name like `"foothold-checkpoints"`
- **Server sections**: Add `DCS.your_server_name:` sections to override defaults per server

### Step 3: Configure Campaigns

Copy the campaigns example:

```powershell
cp plugins\foothold-checkpoint\campaigns.yaml.example campaigns.yaml
```

Edit `campaigns.yaml` to define your campaign file structures. See the included `campaigns.yaml.example` for complete examples with all DCS maps.

**Example minimal configuration:**

```yaml
campaigns:
  afghanistan:
    display_name: "Afghanistan"
    files:
      persistence:
        - "foothold_afghanistan.lua"
      ctld_save:
        files:
          - "foothold_afghanistan_CTLD_Save.csv"
        optional: true
      ctld_farps:
        files:
          - "foothold_afghanistan_CTLD_FARPS.csv"
        optional: true
      storage:
        files:
          - "foothold_afghanistan_storage.csv"
        optional: true
```

> **Note**: The campaigns.yaml file defines **file names and structures**, not server paths. 
> Server paths are configured in DCSServerBot's `servers.yaml` and accessed dynamically via the `server` parameter.

### Step 4: Restart DCSServerBot

After creating the configuration files, restart DCSServerBot to load the plugin:

```powershell
# Stop DCSSB (Ctrl+C if running in terminal, or stop service)
# Then restart
cd D:\dev\_VEAF\VEAF-DCSServerBot
python run.py
```

**Or if running as a service:**

```powershell
Restart-Service DCSServerBot
```

## Verification

### Check Plugin Loaded

**First, verify the plugin was enabled in `main.yaml`:**
- Confirm `foothold-checkpoint` appears in the `opt_plugins` list
- If not present, the plugin will not load at all

**Then check Discord for slash commands:**

The following slash commands should be available:

- `/foothold-checkpoint save` - Save a checkpoint
- `/foothold-checkpoint restore` - Restore a checkpoint
- `/foothold-checkpoint list` - List available checkpoints
- `/foothold-checkpoint delete` - Delete a checkpoint

> **Note**: Slash commands may take 1-2 minutes to sync with Discord after bot restart.

### Check Logs

Check DCSSB logs for plugin loading confirmation:

```powershell
Get-Content DCSServerBot\logs\bot.log -Tail 50
```

Look for lines like:
```
[INFO] Loading extension plugins.foothold-checkpoint
[INFO] Extension plugins.foothold-checkpoint loaded successfully
```

## Discord Commands

All commands are under the `/foothold-checkpoint` group:

### `/foothold-checkpoint save`

Save a checkpoint for campaign files.

**Parameters:**
- `server` (required): DCS server name from DCSSB configuration
  - Determines which `Missions/Saves` folder to read from
  - Must match a server defined in `servers.yaml`
  - **Autocomplete**: Type to filter available servers
- `campaign` (optional): Campaign name, or leave empty for interactive selection
- `name` (optional): Custom checkpoint name (defaults to timestamp)
- `comment` (optional): Descriptive comment for this checkpoint

**Examples:**
```
/foothold-checkpoint save server:Afghanistan campaign:afghanistan
/foothold-checkpoint save server:Caucasus name:pre-deployment comment:Before major update
/foothold-checkpoint save server:Afghanistan    # Interactive campaign selection
```

**How it works:**
1. Plugin accesses the server instance from DCSSB: `self.bot.servers[server_name]`
2. Gets the DCS installation path: `server.instance.home`
3. Constructs Missions/Saves path: `{home}/Missions/Saves/`
4. **Detects campaigns**: Scans files in Missions/Saves and matches them to campaign configurations
5. **Interactive mode**: Shows only detected campaigns in the selection menu
6. **Direct mode**: Validates that the specified campaign exists in the server directory
7. Reads campaign files from that directory based on `campaigns.yaml` definitions
8. Creates versioned ZIP checkpoint in `checkpoints_dir`

**Campaign Detection:**
Like the CLI tool, the plugin only shows campaigns that are actually present in the server's Missions/Saves directory. If a campaign is configured in `campaigns.yaml` but has no files in the server directory, it won't appear in the selection menu. This prevents saving empty checkpoints and provides accurate feedback about which campaigns are available on each server.

**Required Role:** Configured in `permissions.save`

### `/foothold-checkpoint restore`

Restore a checkpoint to a campaign.

**Parameters:**
- `server` (required): DCS server name from DCSSB configuration
  - Determines which `Missions/Saves` folder to restore to
  - Must match a server defined in `servers.yaml`
  - **Autocomplete**: Type to filter available servers
- `checkpoint` (optional): Checkpoint filename to restore
  - Leave empty for **interactive selection** from dropdown menu
- `campaign` (optional): Campaign name to restore to
  - Defaults to checkpoint's original campaign if not specified
- `auto_backup` (optional, default: true): Create automatic backup before restoring

**Examples:**
```
# Interactive mode - select checkpoint from dropdown
/foothold-checkpoint restore server:Afghanistan

# Direct mode - specify checkpoint
/foothold-checkpoint restore server:Afghanistan checkpoint:caucasus_2026-02-15.zip campaign:caucasus

# Disable auto-backup
/foothold-checkpoint restore server:Caucasus checkpoint:afghanistan_backup.zip auto_backup:false
```

**Interactive Selection:**
When no checkpoint is specified, the plugin displays a dropdown menu with all available checkpoints, showing:
- Checkpoint filename
- Campaign name
- Date and time
- File size

**Safety features:**
- Automatic backup created before restore (unless disabled)
- Files renamed to match current campaign file naming conventions
- Validation of checkpoint integrity before restore
- Server-specific restore to correct Missions/Saves directory

**Required Role:** Configured in `permissions.restore`

### `/foothold-checkpoint list`

Display all saved checkpoints in an aligned table.

**Parameters:**
- `campaign` (optional): Filter by campaign name
- `server` (optional): Filter by server name

**Output format:**
```
FILE                          DATE         SIZE
──────────────────────────────────────────────
afghanistan_20240101_120000   2024-01-01   2.5 MB
afghanistan_20240102_150000   2024-01-02   2.6 MB
caucasus_20240101_140000      2024-01-01   3.1 MB
```

**Required Role:** Configured in `permissions.list`

### `/foothold-checkpoint delete`

Delete a checkpoint file.

**Parameters:**
- `checkpoint` (optional): Checkpoint filename to delete
  - Leave empty for **interactive selection** from dropdown menu
- `campaign` (optional): Filter checkpoints by campaign

**Examples:**
```
# Interactive mode - select checkpoint from dropdown
/foothold-checkpoint delete

# Filter by campaign, then select
/foothold-checkpoint delete campaign:caucasus

# Direct mode - specify checkpoint
/foothold-checkpoint delete checkpoint:old_backup_2024.zip campaign:afghanistan
```

**Interactive Selection:**
When no checkpoint is specified, the plugin displays a dropdown menu with all available checkpoints, showing:
- Checkpoint filename
- Campaign name
- Date and time
- File size

**Confirmation:**
- Interactive button confirmation required after selection
- Shows checkpoint name and campaign before deletion
- 60-second timeout for confirmation

**Warning:** Deletion is permanent and cannot be undone!

**Required Role:** Configured in `permissions.delete`

## Server Integration

The plugin integrates directly with DCSServerBot's server management:

### How Server Selection Works

When you run `/foothold-checkpoint save server:Afghanistan`:

1. **Server Validation**: Plugin checks if `Afghanistan` exists in `self.bot.servers`
2. **Path Resolution**: Accesses `self.bot.servers["Afghanistan"].instance.home`
3. **Directory Construction**: Builds path `{home}/Missions/Saves/`
4. **File Collection**: Reads campaign files from that Missions/Saves directory

### Why This Matters

- **Multi-Server Support**: Each DCS server has its own Missions/Saves folder
- **Dynamic Paths**: No hardcoded paths in campaigns.yaml
- **Automatic Detection**: Plugin finds files automatically based on server instance
- **Consistency**: Server name in checkpoint metadata matches actual DCS server

### Example Setup

If you have these DCSSB servers:
```yaml
# servers.yaml
Afghanistan:
  installation: "D:/DCS/Afghanistan"
  
Caucasus:
  installation: "D:/DCS/Caucasus"
```

The plugin automatically uses:
- Afghanistan saves from: `D:/DCS/Afghanistan/Missions/Saves/`
- Caucasus saves from: `D:/DCS/Caucasus/Missions/Saves/`

## Permissions

The plugin uses role-based access control. Users must have one of the configured roles for each operation, or have Discord Administrator permission.

### Permission Structure

Each operation has a list of Discord role names that have permission:

```yaml
permissions:
  save: ["DCS Admin", "Mission Designer"]
  restore: ["Admin"]
  list: ["@everyone"]
  delete: ["Admin"]
```

### Permission Levels

- **save**: Create new checkpoints
- **restore**: Restore checkpoints (most dangerous - can overwrite live data)
- **list**: View available checkpoints (read-only)
- **delete**: Delete checkpoints (permanent action)

### Example Permission Configuration

```yaml
permissions:
  save: ["DCS Admin", "Mission Designer"]
  restore: ["Admin"]  # Most restrictive
  list: []  # Empty = everyone can use
  delete: ["Admin"]
```

Empty array `[]` = everyone can use the command.

## Notifications

The plugin can send Discord notifications for checkpoint events to a configured channel.

### Notification Configuration

Notifications use a simple on/off toggle per event type with a single channel:

```yaml
notifications:
  # Discord channel ID (recommended) or name where all notifications are sent
  # To get channel ID: Right-click channel → Copy Channel ID (Developer Mode required)
  channel: 1234567890123456789  # Or use channel name: "foothold-notifications"
  
  # Enable/disable notifications per event type
  on_save: true      # Notify when checkpoint saved
  on_restore: true   # Notify when checkpoint restored
  on_delete: true    # Notify when checkpoint deleted
  on_error: true     # Notify when operation fails
```

### Notification Types

- **on_save**: Checkpoint saved successfully (green embed with checkpoint details)
- **on_restore**: Checkpoint restored successfully (blue embed with restore details)
- **on_delete**: Checkpoint deleted (orange embed with warning)
- **on_error**: Operation failed (red embed with error message)

### Configure Per Server

Use server-specific sections to override notification channels:

```yaml
DEFAULT:
  notifications:
    channel: 1234567890123456789
    on_save: true
    on_restore: true
    on_delete: true
    on_error: true

# Production server uses different channel
DCS.production_server:
  notifications:
    channel: 9876543210987654321  # Production notifications channel
    on_delete: true
    on_error: true
    on_save: false    # Don't notify on routine saves
    on_restore: false # Don't notify on routine restores
```

### Disable All Notifications

To disable notifications, set all events to `false`:

```yaml
notifications:
  channel: 1234567890123456789
  on_save: false
  on_restore: false
  on_delete: false
  on_error: false  # Still recommended to keep error notifications
```

Events generate rich embeds with checkpoint details, user info, and timestamps.

## File Structure

After installation:
```
DCSServerBot/
├── plugins/
│   └── foothold-checkpoint/
│       ├── __init__.py
│       ├── commands.py         # Slash command handlers
│       ├── formatters.py       # Discord embed formatting
│       ├── listener.py         # Event listeners
│       ├── notifications.py    # Discord notifications
│       ├── permissions.py      # Permission checks
│       ├── ui.py              # Interactive UI components
│       ├── version.py
│       ├── schemas/           # Pydantic config models
│       └── core/              # Core checkpoint logic
├── config/
│   ├── plugins/
│   │   └── foothold-checkpoint.yaml  # Plugin config
│   └── campaigns.yaml                # Campaign definitions
└── checkpoints/                      # Checkpoint storage (created automatically)
```

## Troubleshooting

### "Unknown server" error

**Cause**: Server name doesn't match DCSSB servers.yaml  
**Fix**: Use exact server name from `servers.yaml`, case-sensitive

### "Missions/Saves not found" error

**Cause**: Server installation path incorrect or Missions/Saves doesn't exist  
**Fix**: Verify server installation path in `servers.yaml` and ensure DCS server has created the Missions/Saves folder

### "Cannot access server installation path" error

**Cause**: DCSSB server instance API mismatch  
**Fix**: Check DCSSB version compatibility, ensure `server.instance.home` property exists

### No campaigns in selection menu

**Cause**: `campaigns.yaml` not configured or invalid  
**Fix**: Verify `config/campaigns.yaml` exists and contains valid campaign definitions

## Development

### Development Mode

For active development, you can create a symbolic link instead of copying files:

```powershell
# Remove the copied directory (run PowerShell as Administrator)
cd D:\dev\_VEAF\VEAF-DCSServerBot\plugins
Remove-Item -Recurse foothold-checkpoint

# Create symbolic link to source
New-Item -ItemType SymbolicLink -Path foothold-checkpoint -Target D:\dev\_VEAF\VEAF-foothold-checkpoint-tool\src\foothold_checkpoint\plugin
```

With a symbolic link, changes to the source code take effect immediately after restarting DCSSB, without needing to re-copy files.

This is ideal for:
- Testing changes
- Debugging issues
- Contributing to development

> **Note**: Symbolic links require administrator privileges in PowerShell.

### Running Tests

```bash
# All tests
poetry run pytest

# With coverage
poetry run pytest --cov=foothold_checkpoint

# Specific test file
poetry run pytest tests/test_cli.py
```

### Building Plugin Distribution

```bash
python scripts/build_plugin.py
```

Output: `dist/foothold-checkpoint-plugin-vX.X.X.zip`

### File Structure

After installation:
```
DCSServerBot/
├── plugins/
│   └── foothold-checkpoint/
│       ├── __init__.py
│       ├── commands.py         # Slash command handlers
│       ├── formatters.py       # Discord embed formatting
│       ├── listener.py         # Event listeners
│       ├── notifications.py    # Discord notifications
│       ├── permissions.py      # Permission checks
│       ├── ui.py              # Interactive UI components
│       ├── version.py
│       ├── schemas/           # Pydantic config models
│       └── core/              # Core checkpoint logic
├── config/
│   ├── plugins/
│   │   └── foothold-checkpoint.yaml  # Plugin config
│   └── campaigns.yaml                # Campaign definitions
└── checkpoints/                      # Checkpoint storage (created automatically)
```

## Support

- **User Manuals**: See [PLUGIN_USER_MANUAL_EN.md](PLUGIN_USER_MANUAL_EN.md) or [PLUGIN_USER_MANUAL_FR.md](PLUGIN_USER_MANUAL_FR.md) for end-user documentation
- **GitHub Issues**: https://github.com/VEAF/VEAF-foothold-checkpoint-tool/issues
- **General Usage**: See USERS.md in main repository
- **CLI Tool**: See main README.md for standalone CLI usage

## Version History

### v2.0.0 (Current)
- 🏗️ **ARCHITECTURE**: Plugin now uses DCSServerBot's `Plugin` base class
- 🎮 **EVENT LISTENER**: Integration with DCS events via `EventListener`
- ⚙️ **AUTO-CONFIG**: Configuration via `self.locals` and `self.get_config(server)`
- 📢 **NOTIFICATIONS**: Per-server channels with configurable toggles
- 📚 **DOCUMENTATION**: Comprehensive EN/FR user manuals
- 🗂️ **EXTERNAL CAMPAIGNS**: Support for shared `campaigns.yaml` configuration
- 📋 **GROUPING**: Visual separator between manual checkpoints and auto-backups
- 📅 **SORTING**: Chronological ordering (oldest first, newest last in dropdowns)

### v1.1.0
- ✨ Added server parameter integration with DCSSB
- 🎨 Improved list command with aligned table formatting
- 🔧 Dynamic Missions/Saves path resolution per server
- 📚 Enhanced documentation for server integration

### v1.0.0
- 🎉 Initial plugin release
- 💾 Save, restore, list, delete commands
- 🎯 Interactive UI components
- 🔐 Role-based permissions
- 📢 Discord notifications

## License

Same as the main Foothold Checkpoint Tool project.

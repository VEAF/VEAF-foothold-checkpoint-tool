# DCSServerBot Plugin for Foothold Checkpoint Tool

This document provides installation and configuration instructions for using the Foothold Checkpoint Tool as a DCSServerBot plugin.

## Overview

The Foothold plugin integrates the Foothold Checkpoint Tool with DCSServerBot, providing Discord slash commands for managing campaign checkpoints directly from Discord.

### Features

- **Discord Commands**: `/foothold save`, `/foothold restore`, `/foothold list`, `/foothold delete`
- **Role-Based Permissions**: Configure which Discord roles can execute each command
- **Rich Embeds**: Beautiful Discord embeds for command responses and notifications
- **Auto-Backup**: Automatic backup creation before restoring checkpoints
- **Notifications**: Configurable Discord notifications for checkpoint events

## Installation

### Prerequisites

- DCSServerBot installed and configured
- Python 3.10 or higher
- Foothold Checkpoint Tool v2.0.0+

### Option 1: From Distribution ZIP (Recommended)

1. Download `foothold-plugin-v2.0.0.zip` from the releases page
2. Extract to DCSServerBot plugins directory:
   ```
   DCSServerBot/
   └── plugins/
       └── foothold/
           ├── commands.py
           ├── listener.py
           ├── version.py
           ├── permissions.py
           ├── notifications.py
           └── schemas/
               └── ...
   ```
3. Install dependencies:
   ```bash
   pip install foothold-checkpoint[plugin]
   ```

### Option 2: From Source with Poetry

```bash
# Clone repository
git clone https://github.com/VEAF/VEAF-foothold-checkpoint-tool.git
cd VEAF-foothold-checkpoint-tool

# Install with plugin dependencies
poetry install --with plugin

# Or pip install with plugin extras
pip install -e .[plugin]
```

## Configuration

### 1. Create campaigns.yaml

Create a `campaigns.yaml` file defining all your campaigns:

```yaml
afghanistan:
  path: C:\DCS\Missions\Saves
  file_types:
    persistence: afghan
    ctld_saves: ctld_saves
    storage: storage
    optional: ["optional_file"]

# Add more campaigns as needed
```

### 2. Create Plugin Configuration

Create `DCSServerBot/config/plugins/foothold.yaml`:

```yaml
campaigns_file: ./campaigns.yaml
checkpoints_dir: ./checkpoints

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

notifications:
  channel: mission-logs
  on_save: true
  on_restore: true
  on_delete: true
  on_error: true
```

## Discord Commands

### /foothold save

Save a checkpoint for a campaign.

```
/foothold save campaign:afghanistan name:"Before update" comment:"Pre-patch backup"
```

**Parameters:**
- `campaign` (required): Campaign to save
- `name` (optional): Custom checkpoint name
- `comment` (optional): Checkpoint description

**Required Role:** Configured in `permissions.save`

### /foothold restore

Restore a checkpoint to a campaign.

```
/foothold restore checkpoint:afghanistan_2026-02-16.zip campaign:afghanistan auto_backup:true
```

**Parameters:**
- `checkpoint` (required): Checkpoint filename to restore
- `campaign` (required): Campaign to restore to
- `auto_backup` (optional): Create backup before restore (default: true)

**Required Role:** Configured in `permissions.restore`

### /foothold list

List available checkpoints.

```
/foothold list campaign:afghanistan show_details:true
```

**Parameters:**
- `campaign` (optional): Filter by campaign
- `show_details` (optional): Show file sizes and timestamps

**Required Role:** Configured in `permissions.list`

### /foothold delete

Delete a checkpoint (permanent).

```
/foothold delete checkpoint:afghanistan_old.zip campaign:afghanistan
```

**Parameters:**
- `checkpoint` (required): Checkpoint filename to delete
- `campaign` (required): Campaign name

**Required Role:** Configured in `permissions.delete`

**Warning:** Deletion is permanent and cannot be undone!

## Permissions

The plugin uses role-based access control. Users must have one of the configured roles for each operation, or have Discord Administrator permission.

### Permission Levels

- **save**: Create new checkpoints
- **restore**: Restore checkpoints (most dangerous - can overwrite live data)
- **list**: View available checkpoints (read-only)
- **delete**: Delete checkpoints (permanent action)

### Example Permission Configuration

```yaml
permissions:
  save: [DCS Admin, Mission Designer]
  restore: [DCS Admin]  # Most restrictive
  list: [DCS Admin, Mission Designer, Mission Controller, @everyone]  # Most permissive
  delete: [DCS Admin]
```

## Notifications

The plugin can send notifications to a Discord channel for checkpoint events.

### Notification Types

- **on_save**: Checkpoint saved successfully
- **on_restore**: Checkpoint restored successfully
- **on_delete**: Checkpoint deleted
- **on_error**: Operation failed with error

### Disable Notifications

Set any notification flag to `false` to disable:

```yaml
notifications:
  channel: mission-logs
  on_save: true
  on_restore: false  # Don't notify on restore
  on_delete: true
  on_error: true
```

## Troubleshooting

### Plugin Not Loading

- Check DCSServerBot logs for errors
- Verify `foothold_checkpoint` package is installed
- Ensure `campaigns.yaml` path is correct and accessible

### Permission Errors

- Verify user has one of the configured roles
- Check role names match exactly (case-sensitive)
- Administrators bypass all permission checks

### Checkpoint Not Found

- Use `/foothold list` to see available checkpoints
- Verify `checkpoints_dir` path is correct
- Check file permissions on checkpoints directory

### Notification Channel Not Found

- Verify channel name in config matches Discord channel
- Check bot has permission to view and send messages to channel
- Operations will succeed even if notifications fail (logged as warning)

## Development

### Running Tests

```bash
# All tests
poetry run pytest

# Plugin tests only
poetry run pytest tests/plugin/

# With coverage
poetry run pytest --cov=foothold_checkpoint.plugin
```

### Building Plugin Distribution

```bash
python scripts/build_plugin.py
```

Output: `dist/foothold-plugin-v2.0.0.zip`

## Support

- GitHub Issues: https://github.com/VEAF/VEAF-foothold-checkpoint-tool/issues
- Documentation: See USERS.md for general usage
- Migration Guide: See MIGRATION_v2.0.0.md for upgrading from v1.x

## License

Same as the main Foothold Checkpoint Tool project.

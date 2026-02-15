# User Guide - Foothold Checkpoint Tool

Complete guide for using the Foothold Checkpoint Tool to manage DCS Foothold campaign saves.

## Table of Contents

- [Installation](#installation)
- [Configuration](#configuration)
- [Usage](#usage)
  - [Save Checkpoints](#save-checkpoints)
  - [List Checkpoints](#list-checkpoints)
  - [Restore Checkpoints](#restore-checkpoints)
  - [Delete Checkpoints](#delete-checkpoints)
  - [Import Manual Backups](#import-manual-backups)
- [Examples](#examples)
- [Troubleshooting](#troubleshooting)

## Installation

### Requirements

- Python 3.10 or higher
- Windows (PowerShell)
- DCS servers with Foothold campaigns

### Install from Source

```powershell
git clone https://github.com/VEAF/VEAF-foothold-checkpoint-tool.git
cd VEAF-foothold-checkpoint-tool
poetry install
```

## Running

```powershell
poetry run foothold-checkpoint
```

## Configuration

The tool uses a YAML configuration file located at `~/.foothold-checkpoint/config.yaml`.

### Auto-creation

On first run, the tool automatically creates a default configuration file. You can customize it for your setup.

### Configuration File (v1.1.0)

⚠️ **Breaking Change**: Configuration format changed in v1.1.0. See migration instructions below.

```yaml
# Directory where checkpoints are stored
checkpoints_dir: ~/.foothold-checkpoints

# DCS servers configuration
servers:
  production-1:
    path: D:\Servers\DCS-Production-1\Missions\Saves
    description: "Main production server"

  test-server:
    path: D:\Servers\DCS-Test\Missions\Saves
    description: "Test server"

# Campaign configurations with explicit file lists (NEW in v1.1.0)
campaigns:
  afghanistan:
    display_name: "Afghanistan"
    files:
      persistence:  # Required: at least one file
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

  # Example with campaign name evolution
  germany_modern:
    display_name: "Germany Modern"
    files:
      persistence:
        - "FootHold_Germany_Modern_V0.1.lua"  # Canonical name (first = current)
        - "FootHold_GCW_Modern.lua"           # Accepted (legacy name)
      ctld_save:
        files:
          - "FootHold_Germany_Modern_V0.1_CTLD_Save.csv"
          - "FootHold_GCW_Modern_CTLD_Save.csv"
        optional: true
      ctld_farps:
        files: []
        optional: true
      storage:
        files: []
        optional: true
```

**Key Points:**
- `checkpoints_dir`: Where checkpoint ZIP files are stored
- `servers`: Map server names to their `Missions\Saves` paths
- `campaigns`: Explicit file lists for each campaign
  - `persistence`: Required Lua files (at least one)
  - `ctld_save`, `ctld_farps`, `storage`: Optional file types
  - First filename = canonical name (used when restoring)
  - Multiple names = accepted alternatives (for old checkpoints)

**Migration from v1.0.x:**
```yaml
# OLD format (v1.0.x)
campaigns:
  Afghanistan: ["afghanistan"]

# NEW format (v1.1.0)
campaigns:
  afghanistan:
    display_name: "Afghanistan"
    files:
      persistence:
        - "foothold_afghanistan.lua"
      ctld_save:
        files: []
        optional: true
      ctld_farps:
        files: []
        optional: true
      storage:
        files: []
        optional: true
```

See `config.yaml.example` for complete examples.

## Usage

### Save Checkpoints

Create a checkpoint of a campaign's current state.

#### Save a Single Campaign

```powershell
poetry run foothold-checkpoint save --server production-1 --campaign afghanistan --name "Before Mission 5"
```

#### Save All Campaigns

```powershell
poetry run foothold-checkpoint save --server production-1 --all --name "End of Week Backup"
```

#### Interactive Mode

```powershell
poetry run foothold-checkpoint save
# The tool will prompt for:
# - Server selection
# - Campaign selection
# - Optional name/comment
```

**Options:**
- `--server`: Server name from config
- `--campaign`: Campaign to save
- `--all`: Save all detected campaigns
- `--name`: Optional checkpoint name
- `--comment`: Optional description

### List Checkpoints

Display all available checkpoints.

#### List All Checkpoints

```powershell
poetry run foothold-checkpoint list
```

Output:
```
┌──────────────────────────────────────┬──────────────┬────────────┬─────────────────────┬─────────────────┐
│ Checkpoint                           │ Server       │ Campaign   │ Date                │ Name            │
├──────────────────────────────────────┼──────────────┼────────────┼─────────────────────┼─────────────────┤
│ afghanistan_2024-02-13_14-30-00.zip  │ production-1 │Afghanistan │ 2024-02-13 14:30:00 │ Before Mission 5│
│ CA_2024-02-13_14-31-00.zip           │ production-1 │ Caucasus   │ 2024-02-13 14:31:00 │ Before Mission 5│
└──────────────────────────────────────┴──────────────┴────────────┴─────────────────────┴─────────────────┘
```

#### List with File Details (NEW in v1.1.0)

```powershell
poetry run foothold-checkpoint list --details
```

Shows all files contained in each checkpoint:
```
[Table as above]

Files in afghanistan_2024-02-13_14-30-00.zip:
  - foothold_afghanistan.lua
  - foothold_afghanistan_storage.csv
  - Foothold_Ranks.lua
```

#### Filter by Server

```powershell
poetry run foothold-checkpoint list --server production-1
```

#### Filter by Campaign

```powershell
poetry run foothold-checkpoint list --campaign afghanistan
```

#### Combined Filters

```powershell
poetry run foothold-checkpoint list --server production-1 --campaign afghanistan
```

### Restore Checkpoints

Restore a checkpoint to a server.

#### Basic Restore

```powershell
poetry run foothold-checkpoint restore afghanistan_2024-02-13_14-30-00.zip --server test-server
```

**Behavior:**
- **Auto-backup** (NEW): Creates timestamped backup before overwriting (enabled by default)
- Files are extracted to the target server's `Saves` directory
- **Automatic renaming** (NEW): Files renamed to canonical names from config
  - Example: Old `FootHold_GCW_Modern.lua` → New `FootHold_Germany_Modern_V0.1.lua`
- Integrity is verified using SHA-256 checksums
- `Foothold_Ranks.lua` is **NOT** restored by default

#### Restore Without Auto-Backup

```powershell
poetry run foothold-checkpoint restore afghanistan_2024-02-13_14-30-00.zip --server test-server --no-auto-backup
```

⚠️ **Warning**: Only use `--no-auto-backup` if you're certain you want to overwrite without a safety backup.

#### Restore with Ranks File

```powershell
poetry run foothold-checkpoint restore afghanistan_2024-02-13_14-30-00.zip --server test-server --restore-ranks
```

#### Interactive Mode

```powershell
poetry run foothold-checkpoint restore
# The tool will:
# 1. Display available checkpoints
# 2. Let you select one
# 3. Prompt for target server
# 4. Ask for confirmation before overwriting
```

**Cross-Server Restoration:**
You can restore a checkpoint created on `production-1` to `test-server`. The tool handles this automatically.

### Delete Checkpoints

Remove old or unwanted checkpoints.

#### Delete with Confirmation

```powershell
poetry run foothold-checkpoint delete afghanistan_2024-02-13_14-30-00.zip
```

The tool will:
1. Display checkpoint metadata
2. Ask for confirmation
3. Delete the file

#### Force Delete (No Confirmation)

```powershell
poetry run foothold-checkpoint delete afghanistan_2024-02-13_14-30-00.zip --force
```

⚠️ **Warning**: Deletion is permanent and cannot be undone.

#### Interactive Mode

```powershell
poetry run foothold-checkpoint delete
# Select checkpoint from numbered list
```

### Import Manual Backups

Convert existing manual backups into proper checkpoints.

#### Import from Directory

```powershell
poetry run foothold-checkpoint import D:\Backups\Manual\2024-02-10 --server production-1 --campaign afghanistan --name "Old backup"
```

**Behavior:**
- Scans the directory for Foothold campaign files
- Detects campaign automatically if `--campaign` not specified
- Issues warnings for missing expected files (non-fatal)
- Creates checkpoint with current timestamp
- Computes checksums for all files

#### Interactive Mode

```powershell
poetry run foothold-checkpoint import D:\Backups\Manual\2024-02-10
# The tool will:
# 1. Auto-detect campaigns in directory
# 2. Let you select which campaign to import
# 3. Prompt for server and optional name/comment
```

## Examples

### Weekly Backup Workflow

```powershell
# Friday evening: Save all campaigns
poetry run foothold-checkpoint save --server production-1 --all --name "End of Week - Feb 16"

# List recent backups
poetry run foothold-checkpoint list --server production-1

# Test restore on test server
poetry run foothold-checkpoint restore afghanistan_2024-02-16_18-00-00.zip --server test-server
```

### Testing New Content

```powershell
# Before testing: Create checkpoint
poetry run foothold-checkpoint save --server test-server --campaign afghanistan --name "Before new mission test"

# ... test the new mission ...

# If broken: Restore previous state
poetry run foothold-checkpoint restore afghanistan_2024-02-13_16-00-00.zip --server test-server
```

### Cleanup Old Checkpoints

```powershell
# List all checkpoints
poetry run foothold-checkpoint list

# Delete old ones
poetry run foothold-checkpoint delete afghanistan_2024-01-15_10-00-00.zip
poetry run foothold-checkpoint delete afghanistan_2024-01-18_14-30-00.zip
```

## Troubleshooting

### "Server not found in configuration"

**Problem**: Specified server doesn't exist in `config.yaml`

**Solution**: Add the server to your config file or check for typos.

```yaml
servers:
  your-server-name:
    path: D:\Path\To\Server\Missions\Saves
    description: "Your server description"
```

### "Campaign not detected"

**Problem**: Campaign files don't match expected patterns

**Solution**:
1. Check that files follow Foothold naming conventions (`foothold_name*.lua`, `FootHold_Name*.csv`)
2. Add campaign mapping in config if using custom names

### "Unknown campaign files detected" (NEW in v1.1.0)

**Problem**: Files found that aren't configured in config.yaml

**Solution**: The tool provides a helpful error with YAML snippet to add:

```
Unknown campaign files detected in source directory:
  - foothold_newmap.lua

These files appear to be Foothold campaign files but are not configured.

To import this campaign, add it to your config.yaml under 'campaigns':

  newmap:
    display_name: "New Map"
    files:
      persistence:
        - "foothold_newmap.lua"
      ctld_save:
        files: []
        optional: true
      ctld_farps:
        files: []
        optional: true
      storage:
        files: []
        optional: true
```

**Action**: Copy the suggested YAML to your `config.yaml` and customize as needed.

### "Checksum verification failed"

**Problem**: Checkpoint file is corrupted

**Solution**: The checkpoint file may be corrupted. Try:
1. Re-download if from remote storage
2. Use a different checkpoint
3. Import from original manual backup if available

### Permission Errors

**Problem**: Cannot read/write files

**Solution**:
1. Run PowerShell as Administrator
2. Check file/folder permissions
3. Ensure DCS server is not running (files may be locked)

## Advanced Usage

### Custom Checkpoint Directory

Override default checkpoint location in `config.yaml`:

```yaml
checkpoints_dir: E:\VEAF\Checkpoints
```

### Quiet Mode (for Scripts)

Suppress progress bars for automation:

```powershell
poetry run foothold-checkpoint save --server prod-1 --campaign afghanistan --quiet
```

Output: Just the checkpoint filename on success.

### Help

Get help for any command:

```powershell
poetry run foothold-checkpoint --help
poetry run foothold-checkpoint save --help
poetry run foothold-checkpoint restore --help
```

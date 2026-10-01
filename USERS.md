# User Guide - Foothold Checkpoint Tool

Complete guide for using the Foothold Checkpoint Tool to manage DCS Foothold campaign saves.

## Table of Contents

- [Installation](#installation)
- [Configuration](#configuration)
- [Usage](#usage)
  - [Global Options](#global-options)
  - [The Log File](#the-log-file)
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

## DCSServerBot Integration

This tool can also be used as a plugin for [DCSServerBot](https://github.com/Special-K-s-Flightsim-Bots/DCSServerBot), providing Discord slash commands for checkpoint management directly from Discord:

- Save, restore, list, and delete checkpoints using Discord slash commands
- Role-based permissions for checkpoint operations
- Discord notifications for checkpoint events
- No need to access the server command line

**For plugin installation and usage, see the [Plugin Guide](src/foothold_checkpoint/plugin/README.md).**

The rest of this guide covers the CLI usage. Plugin users should refer to the Plugin Guide instead.

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

### Global Options

These apply to every command and go **before** it:

```powershell
poetry run foothold-checkpoint --debug restore
poetry run foothold-checkpoint --log-file D:\logs\foothold.log save --all --server production-1
```

- `--config PATH`: use a specific configuration file
- `--quiet`: suppress non-essential output
- `--debug`: print the full traceback when something fails, and log at `DEBUG` level
- `--log-file PATH`: where to write the operation log

### The Log File

Every save and restore is recorded: the campaign, the target server, the directory the files came
from or went to, the resulting files, and any failure with its traceback. When a restore does not
do what you expected, this is the file to read.

By default it is written to:

```
~/.foothold-checkpoint/logs/foothold-checkpoint.log
```

It rotates at 5 MB and keeps three older files, so it cannot grow without bound. If the log file
cannot be opened, the command still runs - logging never blocks the work.

When running as a DCSServerBot plugin, there is no separate file: everything goes to the bot's own
log, alongside the rest of its activity.

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

### "N file(s) are not listed in any campaign and will NOT be saved"

**Problem**: the server's `Missions/Saves` directory contains files that look like Foothold campaign
files but are not listed in any campaign in your configuration. The tool names them and carries on
with the campaigns it does recognise.

**Why this matters even though the command succeeded**: a file the configuration does not know is
invisible to the tool. It is never captured by a save, and a restore writes *beside* it rather than
over it. The usual cause is a campaign file being renamed on the server - say from
`FootHold_CA_v0.2.lua` to `FootHold_CA_v0.3.lua` - without `campaigns.yaml` following. Left alone,
this is silent: that campaign's checkpoints contain nothing, and a restore reports success while the
running mission keeps reading the old file and nothing changes in game.

The warning does not block the operation, because an unconfigured campaign sitting on the server is
no reason to stop backing up the others. The case that would actually lose data - a restore whose
safety backup captured nothing - is stopped, and has its own entry below.

**Solution**: add the real names to the campaign, keeping the previous ones so older checkpoints stay
restorable. The **first** name in each list is the one a restore writes to, so it must be the name
the mission currently reads:

```yaml
campaigns:
  caucasus:
    display_name: "Caucasus"
    files:
      persistence:
        - "FootHold_CA_v0.3.lua"   # current name - restores write to this one
        - "FootHold_CA_v0.2.lua"   # kept so older checkpoints still restore
```

To find the real names, list the server's save directory:

```powershell
dir "C:\Users\veaf\Saved Games\<server>\Missions\Saves"
```

### "The campaign running on ... is NOT being backed up"

**Problem**: the mission is writing its save file under a name no campaign in `campaigns.yaml`
lists, so no checkpoint of the campaign being played exists. **Every configured campaign was still
saved** - only this one is missing.

Foothold names its persistence file after the mission version, so each mission update invents a new
name - `FootHold_CA_v0.3.lua` becomes `FootHold_CA_v0.4.lua` - and the old name stops existing. The
tool reads `foothold.status`, which the mission writes beside its saves on every save, to learn
which file is genuinely in use. Expect this at every Foothold mission update.

**Solution**: the message lists the file names found next to it on disk. Add them to the campaign,
putting the new name **first** in each list and keeping the previous ones after it, so older
checkpoints stay restorable:

```yaml
caucasus:
  files:
    persistence:
      - "FootHold_CA_v0.4.lua"   # new: canonical, what a restore writes to
      - "FootHold_CA_v0.3.lua"   # kept: so older checkpoints still restore
```

Then run the save again.

The command reports this as a failure - the Discord bot sends a separate error message, the CLI
exits non-zero - because a campaign with no backup is a failure whatever else succeeded. The
checkpoints that were written are real and are kept.

This only fires on the file the mission is writing **right now**. Other unrecognised files in the
directory produce a warning instead - see below.

### "Restore aborted: the automatic backup captured no files"

**Problem**: before overwriting a campaign, the tool saves its current state. That backup came back
empty *while campaign files it does not recognise are sitting in the target directory*, so the
restore stopped. **Nothing was written.**

**Solution**: this is almost always the same cause as above - fix the file names in `campaigns.yaml`
and run the restore again. If you genuinely want to restore over a state that cannot be backed up,
and you accept that there is no way back, use `--no-auto-backup`.

Note that restoring into a directory with **no** campaign files at all is allowed and does not
trigger this: seeding a fresh server from a checkpoint is a normal operation, and there is nothing
to protect.

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

# Migration Guide: v1.x → v2.0.0

This guide helps you migrate from Foothold Checkpoint Tool v1.x to v2.0.0, which introduces DCSServerBot integration and several architectural improvements.

## What's New in v2.0.0

### Major Changes

1. **Async Architecture**: All storage functions are now `async def`
2. **EventHooks System**: New callback system for plugins and GUIs
3. **External Campaigns Configuration**: Move campaigns to `campaigns.yaml`
4. **DCSServerBot Plugin**: Discord slash commands for checkpoint management
5. **Auto-Backup on Restore**: Automatic backup creation before restoring

### Breaking Changes

⚠️ **Function Signatures Changed**
- `save_checkpoint()` is now `async def` and accepts `hooks` parameter
- `restore_checkpoint()` is now `async def` and accepts `hooks` and `auto_backup` parameters
- `list_checkpoints()` is now `async def`
- `delete_checkpoint()` is now `async def`

⚠️ **Configuration Changes**
- `Config.servers` is now optional (can be `None` for plugin mode)
- `Config.campaigns_file` is a new field for referencing external campaigns
- `Config.campaigns` can be `None` if `campaigns_file` is provided

## Migration Steps

### 1. Update Dependencies

```bash
# Using Poetry
poetry update

# Using pip
pip install --upgrade foothold-checkpoint
```

### 2. Create campaigns.yaml (Optional but Recommended)

Extract campaigns from `config.yaml` into `campaigns.yaml`:

**Before (config.yaml):**
```yaml
servers:
  production-1:
    path: C:\DCS\Server1\Missions\Saves

campaigns:
  afghanistan:
    path: C:\DCS\Server1\Missions\Saves
    file_types:
      persistence: afghan
      ctld_saves: ctld_saves
```

**After (campaigns.yaml):**
```yaml
afghanistan:
  path: C:\DCS\Server1\Missions\Saves
  file_types:
    persistence: afghan
    ctld_saves: ctld_saves
    storage: storage
    optional: []

caucasus:
  path: C:\DCS\Server1\Missions\Saves
  file_types:
    persistence: caucasus
    ctld_saves: ctld_saves
# ... more campaigns
```

**Updated config.yaml:**
```yaml
servers:
  production-1:
    path: C:\DCS\Server1\Missions\Saves

# Reference external campaigns file
campaigns_file: ./campaigns.yaml
```

### 3. Update CLI Usage (No Changes Required!)

The CLI remains backward-compatible. All commands work as before:

```bash
# These still work unchanged
foothold-checkpoint save afghanistan production-1
foothold-checkpoint restore afghanistan_2026-02-16.zip production-1
foothold-checkpoint list
foothold-checkpoint delete afghanistan_2026-02-16.zip
```

### 4. Update Custom Scripts (If Any)

If you have Python scripts calling storage functions, update them:

**Before (v1.x):**
```python
from foothold_checkpoint.core.storage import save_checkpoint

# Synchronous call
checkpoint = save_checkpoint(
    campaign_name="afghanistan",
    server_name="production-1",
    source_dir=source,
    output_dir=output,
    config=config
)
```

**After (v2.0.0):**
```python
import asyncio
from foothold_checkpoint.core.storage import save_checkpoint

# Async call with asyncio.run()
checkpoint = asyncio.run(save_checkpoint(
    campaign_name="afghanistan",
    server_name="production-1",
    source_dir=source,
    output_dir=output,
    config=config,
    hooks=None  # Optional EventHooks for progress tracking
))
```

### 5. Install DCSServerBot Plugin (Optional)

If you want Discord integration:

1. Install plugin dependencies:
   ```bash
   poetry install --with plugin
   ```

2. Copy plugin files to DCSServerBot:
   ```
   DCSServerBot/plugins/foothold/
   ```

3. Create `config/plugins/foothold.yaml`:
   ```yaml
   campaigns_file: ./campaigns.yaml
   checkpoints_dir: ./checkpoints
   permissions:
     save: [DCS Admin]
     restore: [DCS Admin]
     list: [DCS Admin, Mission Designer]
     delete: [DCS Admin]
   notifications:
     channel: mission-logs
     on_save: true
     on_restore: true
     on_delete: true
     on_error: true
   ```

## New Features You Can Use

### Auto-Backup on Restore

Now enabled by default! To disable:

**CLI:**
```bash
foothold-checkpoint restore checkpoint.zip production-1 --no-auto-backup
```

**Python:**
```python
await restore_checkpoint(
    checkpoint_path=path,
    target_dir=target,
    auto_backup=False
)
```

### EventHooks for Progress Tracking

Create custom progress callbacks:

```python
from foothold_checkpoint.core.events import EventHooks
import asyncio

async def on_save_progress(current: int, total: int):
    print(f"Progress: {current}/{total}")

hooks = EventHooks(on_save_progress=on_save_progress)

await save_checkpoint(
    campaign_name="afghanistan",
    server_name="production-1",
    source_dir=source,
    output_dir=output,
    config=config,
    hooks=hooks
)
```

### Discord Commands (with Plugin)

```
/foothold save campaign:afghanistan name:"Pre-update backup"
/foothold restore checkpoint:afghan_2026-02-16.zip campaign:afghanistan
/foothold list campaign:afghanistan show_details:true
/foothold delete checkpoint:old_backup.zip campaign:afghanistan
```

## Backward Compatibility

### What Still Works

✅ All CLI commands work exactly as before  
✅ Existing `config.yaml` files work (campaigns section still supported)  
✅ Existing checkpoint files are fully compatible  
✅ All checkpoint metadata formats unchanged  

### What Changed

❌ Python API is now async (requires `asyncio.run()` or `await`)  
❌ Direct imports of internal CLI functions (use CLI instead)  
❌ Custom implementations relying on sync behavior  

## Testing Your Migration

### 1. Verify CLI Still Works

```bash
# Test all commands
foothold-checkpoint --version
foothold-checkpoint list
foothold-checkpoint save test-campaign production-1 --name "Migration test"
```

### 2. Run Test Suite

```bash
poetry run pytest
# Should show: 303 passed, 3 skipped
```

### 3. Check Existing Checkpoints

```bash
foothold-checkpoint list --details
# Verify all checkpoints are visible and metadata is correct
```

## Troubleshooting

### "coroutine was never awaited" Error

**Problem:** Calling async functions without `await` or `asyncio.run()`

**Solution:**
```python
# Wrong
result = save_checkpoint(...)

# Correct
import asyncio
result = asyncio.run(save_checkpoint(...))

# Or in async context
async def my_function():
    result = await save_checkpoint(...)
```

### Config Validation Errors

**Problem:** `Config` requires either `campaigns` or `campaigns_file`

**Solution:** Add one of:
```yaml
# Option 1: Inline campaigns (old way)
campaigns:
  afghanistan: ...

# Option 2: External file (new way)
campaigns_file: ./campaigns.yaml
```

### Plugin Not Loading

**Problem:** DCSServerBot can't find plugin

**Solution:**
1. Verify plugin files in `DCSServerBot/plugins/foothold/`
2. Check `foothold.yaml` exists in `config/plugins/`
3. Ensure `campaigns_file` path is correct
4. Check DCSServerBot logs for specific errors

## Rollback Instructions

If you need to rollback to v1.x:

```bash
# Using Poetry
poetry add foothold-checkpoint@^1.0.0

# Using pip
pip install foothold-checkpoint==1.0.1
```

Your checkpoints and configurations will continue to work.

## Getting Help

- **Documentation**: See USERS.md and README_PLUGIN.md
- **Issues**: https://github.com/VEAF/VEAF-foothold-checkpoint-tool/issues
- **Changes**: See CHANGELOG.md for detailed change log

## Summary Checklist

- [ ] Updated to foothold-checkpoint v2.0.0
- [ ] Created `campaigns.yaml` (optional)
- [ ] Verified CLI commands still work
- [ ] Updated custom scripts to use `async`/`await`
- [ ] Tested checkpoint save/restore operations
- [ ] Installed DCSServerBot plugin (if using Discord integration)
- [ ] Configured plugin permissions and notifications
- [ ] Ran test suite to verify functionality

Welcome to v2.0.0! 🎉

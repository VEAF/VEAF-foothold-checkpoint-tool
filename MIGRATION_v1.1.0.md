# Migration Guide: v1.0.x → v1.1.0

This guide helps you migrate your configuration from v1.0.x to v1.1.0.

## ⚠️ Breaking Changes

### Configuration Format Changed

The campaign configuration structure has changed from simple name lists to explicit file lists.

**Why?** The new format provides:
- ✅ **Explicit control**: Define exactly which files belong to each campaign
- ✅ **Optional files**: Mark storage/CTLD files as optional (no warnings if missing)
- ✅ **Better errors**: See exactly what's configured vs. what's found
- ✅ **File renaming**: Support campaign name evolution transparently
- ✅ **No false positives**: No more regex guessing

## Step-by-Step Migration

### 1. Backup Your Current Config

```powershell
cp ~/.foothold-checkpoint/config.yaml ~/.foothold-checkpoint/config.yaml.backup
```

### 2. Identify Your Current Configuration

**Old format (v1.0.x)**:
```yaml
campaigns:
  Afghanistan: ["afghanistan"]
  Caucasus: ["CA"]
  Germany_Modern: ["GCW_Modern", "Germany_Modern"]
```

### 3. Convert to New Format

For each campaign, you need to:
1. Use lowercase campaign ID (optional but recommended)
2. Add `display_name` field
3. Create `files` section with four file types:
   - `persistence`: Required Lua files
   - `ctld_save`: Optional CTLD save CSV
   - `ctld_farps`: Optional CTLD FARPs CSV
   - `storage`: Optional storage CSV

**New format (v1.1.0)**:
```yaml
campaigns:
  afghanistan:  # Lowercase ID
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

  caucasus:
    display_name: "Caucasus"
    files:
      persistence:
        - "FootHold_CA_v0.2.lua"
      ctld_save:
        files:
          - "FootHold_CA_v0.2_CTLD_Save.csv"
        optional: true
      ctld_farps:
        files:
          - "FootHold_CA_v0.2_CTLD_FARPS.csv"
        optional: true
      storage:
        files: []
        optional: true

  # Campaign with name evolution (multiple accepted names)
  germany_modern:
    display_name: "Germany Modern"
    files:
      persistence:
        - "FootHold_Germany_Modern_V0.1.lua"  # First = canonical (current)
        - "FootHold_GCW_Modern.lua"           # Also accepted (legacy)
      ctld_save:
        files:
          - "FootHold_Germany_Modern_V0.1_CTLD_Save.csv"
          - "FootHold_GCW_Modern_CTLD_Save.csv"
        optional: true
      ctld_farps:
        files:
          - "FootHold_Germany_Modern_V0.1_CTLD_FARPS.csv"
          - "FootHold_GCW_Modern_CTLD_FARPS.csv"
        optional: true
      storage:
        files: []
        optional: true
```

### 4. Find Your Actual File Names

To find the exact file names used in your campaigns:

```powershell
# List files in your server's Saves directory
ls "D:\Servers\DCS-Production\Missions\Saves" | Where-Object { $_.Name -like "*foothold*" -or $_.Name -like "*FootHold*" }
```

Look for:
- `.lua` files → `persistence`
- `*CTLD_Save*.csv` → `ctld_save`
- `*CTLD_FARPS*.csv` → `ctld_farps`
- `*storage*.csv` → `storage`

### 5. Handle Campaign Name Evolution

If your campaign files have been renamed over time:

**Example**: Germany campaign evolved from `GCW_Modern` to `Germany_Modern`

```yaml
germany_modern:
  display_name: "Germany Modern"
  files:
    persistence:
      # List ALL accepted names, with CURRENT name FIRST
      - "FootHold_Germany_Modern_V0.1.lua"  # ← Current/canonical name
      - "FootHold_GCW_Modern.lua"           # ← Old name (still accepted)
```

**Benefits**:
- Old checkpoints with `FootHold_GCW_Modern.lua` work fine
- On restore, files are automatically renamed to `FootHold_Germany_Modern_V0.1.lua`
- No manual intervention needed

### 6. Mark Optional Files

If your campaign doesn't use CTLD or storage files:

```yaml
campaigns:
  simple_campaign:
    display_name: "Simple Campaign"
    files:
      persistence:
        - "foothold_simple.lua"
      ctld_save:
        files: []           # Empty list
        optional: true      # Marked optional
      ctld_farps:
        files: []
        optional: true
      storage:
        files: []
        optional: true
```

### 7. Test Your Configuration

```powershell
# Test listing checkpoints (should work without errors)
poetry run foothold-checkpoint list

# Test saving (will validate your config)
poetry run foothold-checkpoint save --server test-server --campaign afghanistan
```

If you see errors about unknown files, the tool will provide helpful YAML snippets to add.

## Migration Checklist

- [ ] Backed up old `config.yaml`
- [ ] Listed actual file names in server directories
- [ ] Converted all campaigns to new format
- [ ] Added `display_name` for each campaign
- [ ] Listed all persistence files
- [ ] Marked optional file types
- [ ] Listed all accepted names for evolved campaigns (current name first)
- [ ] Tested `list` command
- [ ] Tested `save` command
- [ ] Tested `restore` command

## Quick Reference

### Minimal Campaign (Lua only)

```yaml
mycampaign:
  display_name: "My Campaign"
  files:
    persistence:
      - "foothold_mycampaign.lua"
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

### Full Campaign (All file types)

```yaml
fullcampaign:
  display_name: "Full Campaign"
  files:
    persistence:
      - "foothold_full.lua"
    ctld_save:
      files:
        - "foothold_full_CTLD_Save.csv"
      optional: true
    ctld_farps:
      files:
        - "foothold_full_CTLD_FARPS.csv"
      optional: true
    storage:
      files:
        - "foothold_full_storage.csv"
      optional: true
```

### Campaign with Multiple Versions

```yaml
evolvingcampaign:
  display_name: "Evolving Campaign"
  files:
    persistence:
      - "foothold_new_v2.lua"     # Current
      - "foothold_new_v1.lua"     # Old but accepted
      - "foothold_old.lua"        # Even older but accepted
    ctld_save:
      files:
        - "foothold_new_v2_CTLD_Save.csv"
        - "foothold_new_v1_CTLD_Save.csv"
      optional: true
    ctld_farps:
      files: []
      optional: true
    storage:
      files: []
      optional: true
```

## Need Help?

- See `config.yaml.example` for complete examples
- Check [USERS.md](USERS.md) for detailed documentation
- Review [CHANGELOG.md](CHANGELOG.md) for all changes in v1.1.0

## Rollback

If you need to rollback to v1.0.x:

```powershell
# Restore old config
cp ~/.foothold-checkpoint/config.yaml.backup ~/.foothold-checkpoint/config.yaml

# Reinstall v1.0.1
poetry install
git checkout v1.0.1
```

**Note**: Checkpoints created with v1.1.0 are compatible with v1.0.x, but v1.0.x won't have the new features (auto-backup, file renaming, etc.).

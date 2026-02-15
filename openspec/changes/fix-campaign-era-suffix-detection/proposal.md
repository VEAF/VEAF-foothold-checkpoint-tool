## Why

Campaign file detection currently fails when era suffixes (`_Modern`, `_Coldwar`) are present in file names. The regex-based normalization treats these as part of the campaign name, causing files from the same campaign to be incorrectly grouped into separate campaigns (e.g., `ca` vs `ca_modern`). This breaks the import command and makes campaign detection unreliable. An explicit configuration-based approach eliminates ambiguity and provides better control over file evolution as Foothold changes file naming conventions.

## What Changes

- Replace regex pattern matching with explicit file lists in configuration
- Campaign configuration now defines all expected file names (historical and current)
- Add automatic backup before checkpoint restoration to prevent data loss
- Fail with clear error when unknown files are detected (no silent assumptions)
- Remove all campaign name normalization code (no longer needed)
- **BREAKING**: Requires config.yaml migration - no backward compatibility with old campaign mapping format

## Capabilities

### New Capabilities

None - all changes modify existing capabilities.

### Modified Capabilities

- `campaign-detection`: Replace regex-based pattern matching with explicit file list configuration
- `checkpoint-restoration`: Add automatic checkpoint backup before restoring files
- `configuration-management`: Add campaign file lists to config.yaml structure
- `checkpoint-import`: Update to use new explicit file list detection

## Impact

**Affected code:**
- `src/foothold_checkpoint/core/campaign.py` - Complete rewrite of detection logic
- `src/foothold_checkpoint/core/config.py` - Add file list structure to campaign config model
- `src/foothold_checkpoint/core/storage.py` - Add auto-backup before restore
- `src/foothold_checkpoint/cli.py` - Update error messages and campaign selection

**Configuration migration required:**
- Users must update `config.yaml` to new format with explicit file lists
- Migration script or documentation needed for upgrading existing configs
- Example config file must be updated

**Test updates:**
- All campaign detection tests need updating
- Add tests for unknown file detection
- Add tests for auto-backup behavior
- Update test data configs to new format

**Breaking changes:**
- Old config.yaml format no longer supported
- Campaign auto-detection behavior changes (more strict)

## Context

The current campaign detection system uses regex patterns to identify and normalize campaign file names. This approach has proven fragile when dealing with era suffixes (`_Modern`, `_Coldwar`) which are sometimes part of the campaign identity and sometimes just decorative metadata. The system incorrectly splits files from the same campaign into separate groups based on these suffixes.

Example failure case:
- `FootHold_CA_v0.2.lua` → detected as campaign `ca`
- `Foothold_CA_CTLD_FARPS_Modern.csv` → detected as campaign `ca_modern`
- Result: Files from the same campaign are split into two groups, breaking import functionality

As Foothold evolves, file naming conventions change unpredictably, making regex-based detection increasingly brittle.

**Current architecture:**
- `campaign.py` uses CAMPAIGN_FILE_PATTERN regex to match files
- `normalize_campaign_name()` strips prefixes, versions, suffixes using regex substitutions
- `group_campaign_files()` groups by normalized names
- Configuration only maps campaign names, not files

**Constraints:**
- Must handle historical file name variations (e.g., `GCW_Modern` → `Germany_Modern`)
- Must not break existing checkpoints (they contain old file names)
- Must be maintainable as Foothold naming evolves

## Goals / Non-Goals

**Goals:**
- Eliminate ambiguity in campaign file detection through explicit configuration
- Support historical file name evolution (multiple names per file type)
- Provide clear errors when unknown files are encountered
- Automatically backup existing campaign files before restoration
- Simplify campaign detection logic (remove complex regex)

**Non-Goals:**
- Automatic migration of old config.yaml files (manual migration only)
- Backward compatibility with old configuration format
- Support for auto-detecting completely unknown file patterns
- GUI for managing campaign file lists

## Decisions

### Decision 1: Explicit file lists in configuration

**Choice:** Campaign configuration lists all known file names explicitly for each file type.

**Structure:**
```yaml
campaigns:
  caucasus:
    display_name: "Caucasus"
    files:
      persistence:
        - "FootHold_CA_v0.2.lua"
        - "FootHold_CA_CTLD_Save_Modern.csv"  # Both with and without era suffix
      ctld_save:
        - "FootHold_CA_v0.2_CTLD_Save.csv"
        - "FootHold_CA_CTLD_Save_Modern.csv"
      ctld_farps:
        - "FootHold_CA_v0.2_CTLD_FARPS.csv"
        - "Foothold_CA_CTLD_FARPS_Modern.csv"
      storage:
        - "FootHold_CA_v0.2_storage.csv"
        optional: true
```

**Rationale:**
- No ambiguity: each file name maps to exactly one campaign
- Easy to maintain: adding new file name = adding one line
- Self-documenting: configuration shows the complete history
- Simple matching: exact string comparison instead of complex regex

**Alternatives considered:**
- Keep regex with more sophisticated patterns: Rejected - would become even more complex and still fragile
- Hybrid approach (regex + whitelist): Rejected - adds complexity without clear benefit
- Pattern templates with wildcards: Rejected - reintroduces ambiguity

### Decision 2: File type categorization

**Choice:** Group files by functional type (persistence, ctld_save, ctld_farps, storage) with optional flag support.

**Rationale:**
- Reflects actual Foothold file structure
- Allows marking optional files (some campaigns lack certain file types)
- Enables validation (e.g., "persistence file missing")
- Future-proof for new file types

**Alternatives considered:**
- Flat list of all files: Rejected - loses semantic information
- Prefix-based categorization: Rejected - brings regex complexity back

### Decision 3: Automatic backup before restore

**Choice:** Create a timestamped checkpoint automatically before any restore operation, using the same checkpoint format.

**Implementation:**
```python
def restore_checkpoint(checkpoint_path, server_name, config, auto_backup=True):
    if auto_backup:
        backup_name = f"auto-backup-{datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S')}"
        backup_comment = f"Automatic backup before restoring {checkpoint_path.stem}"
        save_checkpoint(server_name, campaign_name, config, backup_name, backup_comment)
    # ... proceed with restore
```

**Rationale:**
- Safety first: never lose data during restore
- Uses existing checkpoint infrastructure (no new code paths)
- Timestamped names prevent conflicts
- Can be disabled if needed (future flag)

**Alternatives considered:**
- Simple file copy to .backup directory: Rejected - doesn't leverage existing checkpoint system
- Prompt user for confirmation: Rejected - adds friction, user said Option A (automatic)
- No backup: Rejected - too risky

### Decision 4: Strict unknown file detection

**Choice:** Fail immediately with clear error message when encountering files that match Foothold patterns but aren't in configuration.

**Error format:**
```
Error: Unknown campaign files detected in source directory:
  - foothold_NewMap_v1.0.lua
  - foothold_NewMap_storage.csv

These files appear to be Foothold campaign files but are not configured.

To import this campaign, add it to config.yaml:
  campaigns:
    newmap:
      display_name: "New Map"
      files:
        persistence: ["foothold_NewMap_v1.0.lua"]
        storage: ["foothold_NewMap_storage.csv"]
```

**Rationale:**
- No silent failures or assumptions
- Guides user to fix configuration
- Prevents data corruption from wrong assumptions
- User explicitly requested this behavior (question 3)

**Alternatives considered:**
- Warning but continue: Rejected - could lead to silent data loss
- Auto-add to config: Rejected - too magical, could cause issues
- Prompt user for campaign assignment: Rejected - too complex

### Decision 5: Remove normalization logic

**Choice:** Delete `normalize_campaign_name()`, `CAMPAIGN_FILE_PATTERN` regex, and related functions entirely.

**Rationale:**
- No longer needed with explicit configuration
- Reduces code complexity (~200 lines removed)
- Eliminates source of bugs
- Simplifies testing

**Migration:**
- Detection logic becomes simple dict lookup
- `is_campaign_file()` becomes `any(f in all_known_files for campaign in campaigns)`
- `group_campaign_files()` becomes direct mapping via reverse lookup

## Risks / Trade-offs

**[Risk]** Configuration becomes verbose for servers with many campaigns
→ **Mitigation:** YAML structure is readable; can be generated from existing server directories using a helper script

**[Risk]** Users must manually update config when Foothold changes file names
→ **Mitigation:** This is actually desired behavior - forces explicit acknowledgment of changes; error messages guide users

**[Risk]** Large configuration files become hard to maintain
→ **Mitigation:** Consider moving to separate `campaigns.yaml` if it becomes unwieldy (future enhancement)

**[Risk]** Breaking change forces all users to update configs
→ **Mitigation:** Provide migration guide with examples; error messages clearly explain what's needed

**[Trade-off]** Loses flexibility of auto-detecting unknown patterns
→ **Benefit:** Gains reliability and predictability; this is the right trade-off per user requirements

**[Trade-off]** Automatic backups consume disk space
→ **Benefit:** Safety is worth the cost; old backups can be manually cleaned up

## Migration Plan

### Phase 1: Update configuration schema
1. Add new campaign configuration structure to Pydantic models
2. Update config validation to require file lists
3. Update example config file with new structure

### Phase 2: Update core detection logic
1. Rewrite `campaign.py` to use explicit file lists
2. Update `detect_campaigns()` to use lookup instead of regex
3. Remove normalization functions
4. Add validation for unknown files

### Phase 3: Add auto-backup functionality
1. Add `create_auto_backup()` helper in storage.py
2. Integrate into `restore_checkpoint()` before file operations
3. Add metadata flag to distinguish auto-backups

### Phase 4: Update CLI and error messages
1. Update import command error messages
2. Add helpful configuration hints to errors
3. Update help text and examples

### Phase 5: Testing and documentation
1. Update all campaign detection tests
2. Add tests for unknown file detection
3. Add tests for auto-backup behavior
4. Update README with migration guide
5. Update example config files

### Rollback strategy
If issues arise:
- Old checkpoints remain compatible (they just contain files)
- Can manually edit config.yaml to fix issues
- Worst case: restore from auto-backup checkpoint

## Open Questions

None - all decisions confirmed with user.

## Context

VEAF operates multiple Windows-based DCS servers running Foothold dynamic campaigns. Each server stores campaign persistence files in `SERVER\Missions\Saves` directories. Campaign files follow naming patterns like `foothold_afghanistan*.lua/csv` and `FootHold_CA_v0.2*.lua/csv`, with version suffixes that change over time.

**Current State:**
- No automated checkpoint/restore mechanism
- Manual file copying is error-prone and lacks integrity verification
- No cross-server testing capability
- Campaign name evolution (e.g., `GCW` → `Germany_Modern`) complicates restoration

**Constraints:**
- Windows environment with PowerShell
- Must integrate with existing DCSServerBot architecture (future)
- Test-driven development (TDD) approach required
- All code in English, documentation in English, communication in French

**Stakeholders:**
- VEAF server administrators (primary users)
- Future DCSServerBot Discord users (plugin mode)

## Goals / Non-Goals

**Goals:**
- Reliable checkpoint creation with SHA-256 integrity verification
- Cross-server checkpoint restoration with campaign name evolution support
- Import existing manual backups into checkpoint format
- User-friendly CLI with both command-line and interactive modes
- Structured metadata (server, campaign, timestamp, custom fields)
- Extensible architecture for future DCSServerBot plugin integration
- Comprehensive test coverage from day one (TDD)

**Non-Goals:**
- Real-time synchronization between servers
- Cloud storage or remote backup
- Checkpoint compression optimization (standard ZIP is sufficient)
- Export to external formats (import from manual backups is supported)
- GUI application (CLI only)
- Automatic scheduled backups (manual operation only)

## Decisions

### Architecture: Modular Core + CLI + Plugin Structure

**Decision:** Three-layer architecture:
1. `foothold_checkpoint/core/` - Pure Python business logic (config, campaign, checkpoint, storage)
2. `foothold_checkpoint/cli.py` - Typer-based CLI with Rich UI
3. `plugin/` - DCSServerBot plugin structure (prepared, not fully implemented)

**Rationale:**
- Core modules are reusable across CLI and plugin contexts
- CLI can be tested independently from Discord bot
- Future plugin integration requires minimal changes to core logic
- Clear separation of concerns (business logic vs. presentation)

**Alternatives Considered:**
- Monolithic CLI-only tool: Rejected due to future DCSServerBot integration requirement
- Django/Flask web interface: Rejected as over-engineering for administrative tasks

### Configuration: Pydantic Models with YAML

**Decision:** Use Pydantic models for configuration validation, stored in `~/.foothold-checkpoint/config.yaml`

**Rationale:**
- Pydantic provides runtime validation and type safety
- YAML is human-readable and editable
- Auto-creation on first run eliminates setup friction
- Centralized config (~/.foothold-checkpoint/) survives project moves

**Schema:**
```python
class ServerConfig(BaseModel):
    path: Path
    description: str

class Config(BaseModel):
    checkpoints_dir: Path
    servers: dict[str, ServerConfig]
    campaigns: dict[str, list[str]]  # campaign -> [old_name, ..., current_name]
```

**Alternatives Considered:**
- JSON config: Rejected due to lack of comments and less human-friendly
- TOML: Rejected due to less familiarity in VEAF ecosystem
- Database: Over-engineering for simple key-value storage

### Checkpoint Format: ZIP with JSON Metadata

**Decision:** One checkpoint = one ZIP file containing:
- All campaign files (*.lua, *.csv)
- `Foothold_Ranks.lua` (always saved, not restored by default)
- `metadata.json` with checksums, server, campaign, timestamp, custom fields

**Naming:** `{campaign}_{YYYY-MM-DD_HH-MM-SS}.zip`

**Rationale:**
- ZIP is standard, portable, and inspectable
- JSON metadata is parsable and extensible
- Checksums enable integrity verification before restoration
- Original filenames tracked for audit trail
- Timestamp in filename enables chronological sorting

**Alternatives Considered:**
- Tar.gz: Rejected (less Windows-native, minimal compression benefit)
- SQLite database: Over-engineering, reduces portability
- Git-based versioning: Rejected (binary files, overkill for snapshots)

### Campaign Normalization: Version-Aware Mapping

**Decision:** Maintain campaign evolution history in config:
```yaml
campaigns:
  Germany_Modern:
    - GCW_Modern      # historical name
    - Germany_Modern  # current name (used for restoration)
```

On save: Normalize `FootHold_Germany_Modern_V0.1.lua` → campaign `Germany_Modern`
On restore: Use last name in list (`Germany_Modern`) to create files

**Rationale:**
- Handles campaign name evolution transparently
- Enables restoration of old checkpoints to current server versions
- Config-driven (no code changes when campaigns rename)
- Preserves original filenames in metadata for traceability

**Alternatives Considered:**
- Hardcoded regex patterns: Rejected (inflexible, requires code changes)
- Symlink approach: Rejected (Windows compatibility issues)

### CLI Framework: Typer + Rich

**Decision:** Use Typer for command structure, Rich for enhanced output (tables, progress bars)

**Modes:**
1. **Command-line mode:** `foothold-checkpoint save --server prod-1 --campaign afghanistan`
2. **Simple interactive mode:** `foothold-checkpoint save` → prompts for missing parameters (server, campaign, name)

**Rationale:**
- Typer provides clean command definitions with type hints
- Rich enhances output (tables for listing, progress bars for operations)
- Simple prompts avoid TUI complexity while maintaining usability
- Both modes coexist naturally (missing args trigger prompts)
- Excellent Windows/PowerShell compatibility

**Interactive Behavior:**
- If required parameters missing, prompt user with simple questions
- Use `typer.prompt()` for input (no complex TUI menus)
- Display choices as numbered lists when needed (e.g., select campaign)
- Example: `foothold-checkpoint save` → "Select server: [1] prod-1 [2] test-server"

**Alternatives Considered:**
- Full TUI (Textual): Rejected - poor user experience, unnecessary complexity
- Click: Rejected (Typer is Click-based with better type hints)
- Argparse: Rejected (more verbose, less modern)

### Testing Strategy: Test-Driven Development (TDD)

**Decision:** Write tests first using pytest, with fixtures for test data in `tests/data/foothold/`

**Coverage targets:**
- Core modules: 100% (config, campaign, checkpoint, storage)
- CLI: Integration tests for major workflows
- Edge cases: Version parsing, checksum validation, cross-server scenarios

**Rationale:**
- TDD enforced by development guidelines
- Test data already exists (`tests/data/foothold/`)
- Prevents regressions during DCSServerBot integration
- Validates business logic independently of UI

### Integrity Verification: SHA-256 Checksums

**Decision:** Compute SHA-256 checksums on save, verify on restore

**Behavior:**
- Save: Compute and store in `metadata.json`
- Restore: Verify checksums before extraction, abort on mismatch
- CLI output: Show verification progress with Rich

**Rationale:**
- Detects corruption during transfer or storage
- SHA-256 is standard and fast enough for typical file sizes
- No additional dependencies (hashlib in stdlib)

**Alternatives Considered:**
- MD5: Rejected (cryptographically broken, not future-proof)
- CRC32: Rejected (insufficient collision resistance)
- No verification: Rejected (data integrity is critical for campaign saves)

### Manual Backup Import: Convert Existing Backups to Checkpoints

**Decision:** Support importing existing manual backups into checkpoint format with auto-detection and validation

**Modes:**
1. **CLI mode:** `foothold-checkpoint import /path/to/backup --server prod-1 --campaign afghanistan --name "Old backup"`
2. **Interactive mode:** Scan directory, detect campaigns, prompt for metadata

**Behavior:**
- Scan source directory for campaign files
- Detect campaign based on file naming patterns (reuse campaign detection logic)
- Validate file completeness (*.lua, *_CTLD_*.csv, *_storage.csv)
- Issue warnings (not errors) for missing expected files
- Prompt for or accept server/name/comment metadata
- Create checkpoint with current timestamp
- Compute checksums for imported files

**Rationale:**
- Enables migration of existing manual backups to structured checkpoint format
- Reuses existing campaign detection and checkpoint creation logic
- Warnings (not blocking errors) handle incomplete backups gracefully
- Interactive mode reduces friction for batch imports
- Preserves original filenames in metadata for traceability

**Validation Strategy:**
- Expected files per campaign: `{prefix}.lua`, `{prefix}_CTLD_FARPS.csv`, `{prefix}_CTLD_Save.csv`, `{prefix}_storage.csv`
- Warning messages for missing files (e.g., "Warning: {prefix}_storage.csv not found")
- Continue import with available files (user decision to abort if needed)
- `Foothold_Ranks.lua` optional (warn if missing but not critical)

**Alternatives Considered:**
- Strict validation (block on missing files): Rejected - too rigid for real-world incomplete backups
- No validation: Rejected - silent imports could create broken checkpoints
- Auto-detect server from path: Rejected - path structures vary, explicit is safer

## Risks / Trade-offs

**[Risk]** Campaign file patterns change, breaking detection
**→ Mitigation:** Use config-driven campaign mappings; update config, not code

**[Risk]** Large campaign files (>1GB storage.csv) slow down operations
**→ Mitigation:** Show progress bars with Rich; future: implement streaming ZIP

**[Risk]** Concurrent access to same checkpoint directory from multiple instances
**→ Mitigation:** Document as single-user tool; future: add file locking if needed

**[Risk]** Checkpoint restoration overwrites active campaign without warning
**→ Mitigation:** Require explicit server target; add confirmation prompt in interactive mode

**[Trade-off]** One checkpoint per campaign (not per-server bulk)
**→ Rationale:** Simplifies cross-server restore logic, clearer metadata; `--all` flag mitigates UX impact

**[Trade-off]** No automatic compression optimization
**→ Rationale:** ZIP default compression is sufficient; campaign files are already compressed (Lua tables, CSVs)

**[Trade-off]** Plugin structure prepared but not implemented
**→ Rationale:** Enables future work without rework; core logic fully testable standalone

## Future Considerations

**Web Interface:**
- Potential future enhancement: web-based UI for checkpoint management
- Would complement CLI/Discord bot modes
- Not implemented in v1 - CLI and plugin modes cover current needs
- Consider Flask/FastAPI if pursued

**Git-Based Versioning:**
- Alternative approach: use Git for checkpoint versioning instead of ZIP archives
- Benefits: built-in diffing, branching, history
- Challenges: binary file handling, learning curve, complexity
- Keep as exploration option for v2+

**Enhanced TUI Mode:**
- If simple prompts prove insufficient, consider richer TUI (Textual)
- Current approach (simple prompts) prioritized based on user preference
- Monitor user feedback before investing in complex TUI

## Open Questions

**Q:** Should we support checkpoint annotations after creation?
**A:** Defer to v2 - current design supports name/comment at creation time only

**Q:** Should Foothold_Ranks.lua restoration be opt-in or opt-out?
**A:** Opt-in (`--restore-ranks` flag) - default is to NOT restore ranks file (campaign-specific only)

**Q:** Compression level for ZIP archives?
**A:** Use Python zipfile default (ZIP_DEFLATED) - balance between speed and size

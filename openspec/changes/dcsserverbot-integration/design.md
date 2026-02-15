## Context

### Current State

**Foothold Checkpoint Tool v1.1.0** is a standalone CLI application for managing DCS Foothold campaign checkpoints:
- Core modules in `src/foothold_checkpoint/core/` (campaign detection, storage, config)
- CLI interface in `src/foothold_checkpoint/cli.py` using Typer
- Configuration in `~/.foothold-checkpoint/config.yaml` with explicit file lists
- Checkpoints stored as ZIP archives with SHA-256 integrity verification
- Full test coverage (304 tests, 95% coverage)
- Poetry-based dependency management

**DCSServerBot** is a modular Discord bot framework for DCS server management:
- Plugin-based architecture (each plugin = commands.py + listener.py)
- Configuration in `config/plugins/<plugin>.yaml` with DEFAULT + per-server sections
- Async event-driven model with `@command` decorators for Discord slash commands
- Role-based permissions via `@utils.app_has_role()`
- Rich Discord embeds for user interaction
- Integration with DCS servers via UDP communication

### Constraints

- Must maintain CLI backward compatibility (existing users, scripts)
- Plugin must follow DCSServerBot conventions (file structure, naming, lifecycle)
- Must share campaign file configuration between CLI and plugin (DRY principle)
- Poetry packaging required (project standard)
- Single checkpoints directory shared between CLI and plugin (no duplication)

### Stakeholders

- **Server Administrators**: Use CLI for automation, need both interfaces
- **Single Developer**: Manual config migration acceptable, no need for auto-migration

---

## Goals / Non-Goals

**Goals:**
- Discord-based checkpoint operations via slash commands (`/foothold save`, `/restore`, `/list`, `/delete`)
- Interactive Discord interface using Discord UI capabilities (autocomplete, select menus, buttons, modals)
- Role-based access control using Discord roles (e.g., DCS Admin)
- Rich Discord notifications for checkpoint events (save success, restore completion, errors)
- Maintain 100% CLI backward compatibility
- Share campaign configuration between CLI and plugin (no duplication)
- Package as both standalone CLI and DCSServerBot plugin
- Preserve existing test coverage and code quality standards

**Non-Goals:**
- Automated scheduled backups (deferred to v1.3.0)
- Web dashboard or REST API (deferred to v2.1.0+)
- Multi-tenancy or cloud storage integration (future consideration)
- Auto-migration from v1.1.0 to v2.0.0 config (manual migration acceptable)
- Changes to checkpoint format or storage mechanism
- DCS in-game Lua integration (not needed for Discord operations)

---

## Decisions

### D1: Repository and Plugin Location

**Decision:** Implement plugin in `VEAF-foothold-checkpoint-tool` repository under `src/foothold_checkpoint/plugin/`, not in `VEAF-DCSServerBot/plugins/foothold/`.

**Rationale:**
- **Single source of truth**: All checkpoint logic in one codebase
- **Easier maintenance**: Bug fixes and features update both CLI and plugin
- **Unified versioning**: CLI and plugin share same version number
- **Simpler testing**: Test both interfaces from same test suite
- **Better packaging**: Single PyPI package with optional Discord dependencies

**Alternatives Considered:**
- **Duplicate code in DCSServerBot repo**: Rejected - violates DRY, maintenance nightmare
- **Separate PyPI package**: Rejected - unnecessary complexity for single-user project
- **Git submodules**: Rejected - adds complexity without benefit

**Implementation:**
```
VEAF-foothold-checkpoint-tool/
  src/foothold_checkpoint/
    core/              # Existing core library (v1.1.0)
    cli.py             # Existing CLI (v1.1.0)
    plugin/            # NEW: DCSServerBot plugin
      __init__.py
      commands.py      # Discord slash commands
      listener.py      # DCS event listener (optional)
      permissions.py   # Role-based access control
      notifications.py # Discord embeds and notifications
      version.py
      schemas/
        foothold_schema.yaml  # Config validation
```

**Installation in DCSServerBot:**
- Copy/symlink `plugin/` directory to `VEAF-DCSServerBot/plugins/foothold/`
- Or build plugin ZIP for distribution

---

### D2: Configuration Architecture - Shared campaigns.yaml

**Decision:** Extract campaign definitions into separate `~/.foothold-checkpoint/campaigns.yaml` file, referenced by both CLI and plugin configs.

**Rationale:**
- **DRY principle**: Campaign file lists defined once, used everywhere
- **Consistency**: CLI and plugin always use same campaign definitions
- **Easier updates**: Foothold file naming changes only need one config update
- **Clear separation**: Campaign structure (shared) vs. mode-specific settings (separate)

**Alternatives Considered:**
- **Duplicate campaigns in both configs**: Rejected - maintenance burden, drift risk
- **CLI config as source of truth**: Rejected - DCSServerBot expects `config/plugins/` structure
- **Database for campaigns**: Rejected - over-engineering for static configuration

**Structure:**

**campaigns.yaml (shared):**
```yaml
# ~/.foothold-checkpoint/campaigns.yaml
campaigns:
  afghanistan:
    display_name: "Afghanistan"
    files:
      persistence:
        - "FootHold_afghanistan.lua"
      ctld_save:
        - "FootHold_afghanistan_CTLD_Save.csv"
      storage:
        files:
          - "foothold_afghanistan_storage.csv"
        optional: true
  
  caucasus:
    display_name: "Caucasus"
    files:
      persistence:
        - "FootHold_CA.lua"
        - "FootHold_Caucasus.lua"  # Historical names
      # ...
```

**config.yaml (CLI):**
```yaml
# ~/.foothold-checkpoint/config.yaml
campaigns_file: campaigns.yaml  # Reference to shared file
checkpoints_dir: ~/.foothold-checkpoints

servers:
  production-1:
    path: D:\DCS\Missions\Saves
    description: "Main server"
```

**foothold.yaml (Plugin):**
```yaml
# VEAF-DCSServerBot/config/plugins/foothold.yaml
DEFAULT:
  campaigns_file: ~/.foothold-checkpoint/campaigns.yaml  # Same reference
  checkpoints_dir: ~/.foothold-checkpoints               # Same directory
  
  permissions:
    save: ["DCS Admin", "Mission Designer"]
    restore: ["DCS Admin"]
    delete: ["DCS Admin"]
    list: ["DCS", "DCS Admin"]
  
  notifications:
    channel: "mission-logs"
    on_save: true
    on_restore: true
    on_failure: true
```

**Migration from v1.1.0:**
- Manual extraction of `campaigns:` section from config.yaml to campaigns.yaml
- Update config.yaml to add `campaigns_file: campaigns.yaml` reference
- Create foothold.yaml in DCSServerBot config

---

### D3: Core Library Dual-Mode Support

**Decision:** Refactor core modules (`storage.py`, `checkpoint.py`, `config.py`) to support both CLI and plugin modes via dependency injection and optional callbacks.

**Rationale:**
- **Code reuse**: Same checkpoint logic for CLI and Discord commands
- **Maintainability**: Bug fixes automatically apply to both interfaces
- **Testability**: Core logic tested independently of interface
- **Flexibility**: Easy to add third interface (REST API, web UI) later

**Pattern:**
```python
# src/foothold_checkpoint/core/storage.py

from typing import Optional, Callable, Awaitable

class EventHooks:
    """Optional callbacks for checkpoint operations"""
    on_save_start: Optional[Callable[[str], Awaitable[None]]] = None
    on_save_progress: Optional[Callable[[int, int], Awaitable[None]]] = None
    on_save_complete: Optional[Callable[[Path], Awaitable[None]]] = None
    on_error: Optional[Callable[[Exception], Awaitable[None]]] = None

async def save_checkpoint(
    campaign: str,
    server_path: Path,
    config: Config,
    name: Optional[str] = None,
    comment: Optional[str] = None,
    hooks: Optional[EventHooks] = None
) -> Path:
    """
    Save checkpoint with optional event hooks.
    
    CLI usage: hooks=None (no callbacks)
    Plugin usage: hooks=EventHooks(on_save_complete=send_discord_notification)
    """
    if hooks and hooks.on_save_start:
        await hooks.on_save_start(campaign)
    
    # ... checkpoint creation logic ...
    
    if hooks and hooks.on_save_complete:
        await hooks.on_save_complete(checkpoint_path)
    
    return checkpoint_path
```

**CLI stays synchronous:**
```python
# src/foothold_checkpoint/cli.py
def save_command(campaign: str, ...):
    # No hooks, direct call
    checkpoint = asyncio.run(save_checkpoint(campaign, ..., hooks=None))
    console.print(f"Saved: {checkpoint}")
```

**Plugin uses async hooks:**
```python
# src/foothold_checkpoint/plugin/commands.py
async def save_command(interaction: discord.Interaction, campaign: str):
    hooks = EventHooks(
        on_save_start=lambda c: interaction.followup.send(f"Saving {c}..."),
        on_save_complete=lambda p: send_notification(interaction, p)
    )
    checkpoint = await save_checkpoint(campaign, ..., hooks=hooks)
```

**Alternatives Considered:**
- **Separate CLI and plugin implementations**: Rejected - code duplication
- **Events/signals library**: Rejected - adds dependency for simple callbacks
- **Global event emitter**: Rejected - harder to test, implicit dependencies

---

### D4: Packaging with Poetry Optional Dependencies

**Decision:** Use Poetry dependency groups with `optional = true` for Discord dependencies, allowing installation as CLI-only or full plugin.

**Rationale:**
- **Lightweight CLI**: Users without Discord don't install discord.py (large dependency)
- **Standard packaging**: Poetry optional groups are idiomatic
- **Flexible installation**: `poetry install` (CLI) vs `poetry install --with plugin` (full)
- **PyPI compatibility**: Works with `pip install foothold-checkpoint[plugin]`

**pyproject.toml:**
```toml
[tool.poetry]
name = "foothold-checkpoint"
version = "2.0.0"

[tool.poetry.dependencies]
python = "^3.10"
# CLI dependencies (always installed)
typer = "^0.9.0"
click = "8.1.7"  # Pinned for Typer compatibility
pyyaml = "^6.0"
pydantic = "^2.0"
rich = "^13.0"

[tool.poetry.group.plugin]
optional = true

[tool.poetry.group.plugin.dependencies]
# Plugin-specific dependencies
discord-py = "^2.3.0"

[tool.poetry.scripts]
foothold-checkpoint = "foothold_checkpoint.cli:app"
```

**Installation:**
```bash
# CLI only
poetry install

# With plugin support
poetry install --with plugin

# In DCSServerBot environment
cd VEAF-DCSServerBot
poetry add ../VEAF-foothold-checkpoint-tool --extras plugin
```

**Distribution:**
- PyPI wheel: `foothold_checkpoint-2.0.0-py3-none-any.whl`
- Plugin ZIP: `foothold-plugin-v2.0.0.zip` (built via script, contains plugin/ + requirements.txt)

---

### D5: Discord Commands Implementation

**Decision:** Implement Discord slash commands following DCSServerBot conventions with `@command` decorator, `ServerTransformer`, autocomplete, and Discord embeds.

**Commands:**
```python
# src/foothold_checkpoint/plugin/commands.py

from core import Plugin, command, utils, Server, Status
from discord import app_commands
import discord

class Foothold(Plugin):
    
    @command(description='Save a checkpoint for a campaign')
    @app_commands.guild_only()
    @utils.app_has_role('DCS') 
    async def save(
        self, 
        interaction: discord.Interaction,
        server: app_commands.Transform[Server, utils.ServerTransformer()],
        campaign: str,  # Autocomplete from campaigns.yaml
        name: Optional[str] = None,
        comment: Optional[str] = None
    ):
        # Check permissions
        if not await self.check_permission(interaction, 'save'):
            await interaction.response.send_message(
                "❌ You don't have permission to save checkpoints.",
                ephemeral=True
            )
            return
        
        await interaction.response.defer(thinking=True)
        
        try:
            # Use core library with Discord hooks
            hooks = EventHooks(
                on_save_complete=lambda p: self.send_notification(
                    interaction, "save", campaign, p
                )
            )
            checkpoint = await save_checkpoint(
                campaign=campaign,
                server_path=server.instance.home / "Missions" / "Saves",
                config=self.get_config(server),
                name=name,
                comment=comment,
                hooks=hooks
            )
            
            # Rich Discord embed response
            embed = discord.Embed(
                title="✅ Checkpoint Saved",
                description=f"Campaign: **{campaign}**",
                color=discord.Color.green()
            )
            embed.add_field(name="Checkpoint", value=checkpoint.name)
            if comment:
                embed.add_field(name="Comment", value=comment)
            embed.set_footer(text=f"Server: {server.name}")
            
            await interaction.followup.send(embed=embed)
            
        except Exception as e:
            await interaction.followup.send(f"❌ Save failed: {e}")
            await self.send_notification(interaction, "error", campaign, error=e)
    
    @command(description='Restore a checkpoint')
    @utils.app_has_role('DCS Admin')  # More restrictive
    async def restore(self, interaction, server, checkpoint: str):
        # Similar pattern with restore_checkpoint()
        ...
    
    @command(description='List available checkpoints')
    @utils.app_has_role('DCS')
    async def list(self, interaction, server, campaign: Optional[str] = None):
        # Similar pattern with list_checkpoints()
        ...
    
    @command(description='Delete a checkpoint')
    @utils.app_has_role('DCS Admin')
    async def delete(self, interaction, server, checkpoint: str):
        # Similar pattern with delete_checkpoint()
        ...
```

**Autocomplete:**
```python
async def campaign_autocomplete(interaction, current: str):
    config = interaction.client.cogs['Foothold'].get_config()
    campaigns = load_campaigns(config['campaigns_file'])
    return [
        app_commands.Choice(name=c['display_name'], value=name)
        for name, c in campaigns.items()
        if not current or current.lower() in name.lower()
    ][:25]
```

---

### D6: Permissions System

**Decision:** Use DCSServerBot's built-in role system via `@utils.app_has_role()` decorator with operation-specific role configuration in foothold.yaml.

**Rationale:**
- **Native integration**: Uses existing DCSServerBot permission model
- **Familiar pattern**: Consistent with other plugins (backup, mission, etc.)
- **Flexible**: Different roles per operation (save vs restore vs delete)
- **Override-able**: Can customize per-server in config

**Configuration:**
```yaml
# config/plugins/foothold.yaml
DEFAULT:
  permissions:
    save: ["DCS Admin", "Mission Designer"]
    restore: ["DCS Admin"]
    delete: ["DCS Admin"]
    list: ["DCS", "DCS Admin", "Mission Designer"]
```

**Implementation:**
```python
async def check_permission(self, interaction: discord.Interaction, operation: str) -> bool:
    """Check if user has permission for operation"""
    config = self.get_config()
    allowed_roles = config.get('permissions', {}).get(operation, [])
    
    user_roles = [role.name for role in interaction.user.roles]
    return any(role in allowed_roles for role in user_roles)
```

---

### D7: Discord Notifications

**Decision:** Send rich Discord embeds to configured channel on checkpoint events (save, restore, delete, errors).

**Configuration:**
```yaml
DEFAULT:
  notifications:
    channel: "mission-logs"  # Channel name or ID
    on_save: true
    on_restore: true
    on_delete: true
    on_failure: true
```

**Implementation:**
```python
# src/foothold_checkpoint/plugin/notifications.py

async def send_notification(
    self, 
    interaction: discord.Interaction,
    event_type: str,  # "save", "restore", "delete", "error"
    campaign: str,
    checkpoint: Optional[Path] = None,
    error: Optional[Exception] = None
):
    config = self.get_config()
    
    # Check if notifications enabled for this event
    if not config['notifications'].get(f'on_{event_type}', True):
        return
    
    # Find notification channel
    channel_name = config['notifications']['channel']
    channel = discord.utils.get(interaction.guild.channels, name=channel_name)
    
    # Build embed
    if event_type == "save":
        embed = discord.Embed(
            title="📦 Checkpoint Saved",
            description=f"Campaign: **{campaign}**",
            color=discord.Color.green()
        )
        embed.add_field(name="Checkpoint", value=checkpoint.name)
        embed.add_field(name="Size", value=format_size(checkpoint.stat().st_size))
        
    elif event_type == "restore":
        embed = discord.Embed(
            title="♻️ Checkpoint Restored",
            description=f"Campaign: **{campaign}**",
            color=discord.Color.blue()
        )
        # ...
    
    elif event_type == "error":
        embed = discord.Embed(
            title="❌ Checkpoint Operation Failed",
            description=f"Campaign: **{campaign}**",
            color=discord.Color.red()
        )
        embed.add_field(name="Error", value=str(error))
    
    embed.set_footer(
        text=f"By {interaction.user.name}",
        icon_url=interaction.user.avatar.url
    )
    embed.timestamp = discord.utils.utcnow()
    
    await channel.send(embed=embed)
```

---

## Risks / Trade-offs

### R1: Configuration Migration Complexity
**Risk:** Users with existing v1.1.0 configs must manually split campaigns into separate file.

**Mitigation:**
- Clear migration guide in MIGRATION_v2.0.0.md with step-by-step instructions
- Example campaigns.yaml provided
- CLI detects old format and shows clear error with migration steps
- Single user (VEAF only), manual migration is acceptable

**Trade-off:** Accepting manual migration to maintain clean separation of concerns.

---

### R2: Dual-Mode Core Library Complexity
**Risk:** Core functions with optional hooks add cognitive overhead and testing complexity.

**Mitigation:**
- Clear documentation of hook system
- Hooks are truly optional (None = CLI mode, no callbacks)
- Comprehensive tests for both modes (with and without hooks)
- Type hints make hook interface explicit

**Trade-off:** Small complexity increase for significant code reuse benefit (no duplication).

---

### R3: Plugin Installation Friction
**Risk:** Installing plugin in DCSServerBot requires manual steps (copy/symlink).

**Mitigation:**
- Build plugin ZIP with all dependencies for drop-in installation
- Clear README_PLUGIN.md with installation instructions
- Consider adding to DCSServerBot plugin repository in future
- Poetry add command works for development setup

**Trade-off:** Manual setup acceptable for single-user scenario.

---

### R4: Discord.py Dependency Size
**Risk:** discord.py is large (~50MB with dependencies), impacts CLI-only installations.

**Mitigation:**
- Optional dependency group ensures CLI-only users don't install it
- PyPI extras allow selective installation: `pip install foothold-checkpoint[plugin]`
- Plugin-specific dependencies clearly documented

**Trade-off:** Users who want both CLI and plugin accept larger install.

---

### R5: Breaking Changes in Core Function Signatures
**Risk:** Adding optional `hooks` parameter changes function signatures, potential breakage.

**Mitigation:**
- Hooks parameter is optional with default None (backward compatible)
- All existing CLI calls don't provide hooks (continue working)
- Type hints make new parameter explicit
- Comprehensive backward compatibility tests

**Trade-off:** Minor API surface change for major functionality gain.

---

### R6: Event Hook Async/Await Requirement
**Risk:** Core library becomes fully async, complicates CLI synchronous usage.

**Mitigation:**
- CLI uses `asyncio.run()` wrapper for async functions
- Core functions already async for potential future use (async file I/O)
- Standard pattern in modern Python

**Trade-off:** All core functions become async, but benefits both CLI and plugin.

---

## Migration Plan

### Phase 1: Configuration Migration (Manual)
1. User creates `~/.foothold-checkpoint/campaigns.yaml`
2. User copies `campaigns:` section from config.yaml to campaigns.yaml
3. User adds `campaigns_file: campaigns.yaml` to config.yaml
4. User removes `campaigns:` section from config.yaml
5. CLI validates new config format, shows helpful errors if issues

### Phase 2: Plugin Installation
1. Build plugin: `poetry run python scripts/build_plugin.py`
2. Copy `foothold-plugin-v2.0.0.zip` to DCSServerBot host
3. Extract to `VEAF-DCSServerBot/plugins/`
4. Install dependencies: `cd plugins/foothold && poetry install`
5. Create `config/plugins/foothold.yaml` with permissions and notifications
6. Restart DCSServerBot

### Phase 3: Testing
1. Verify CLI still works with new config format
2. Test Discord commands in test channel
3. Verify permissions work correctly
4. Test notifications appear in configured channel
5. Perform checkpoint save/restore via Discord

### Phase 4: Rollback (if needed)
1. Revert config.yaml to v1.1.0 format (inline campaigns)
2. Downgrade foothold-checkpoint package to v1.1.0
3. Remove plugin from DCSServerBot
4. Checkpoints remain compatible (no format changes)

---

## Open Questions

### Q1: EventListener Integration
**Question:** Do we need a Foothold EventListener for DCS events (onMissionLoadEnd, etc.), or are Discord commands sufficient?

**Options:**
- **Option A:** No listener, commands only (simpler)
- **Option B:** Add listener for auto-checkpoint on mission events (more features)

**Lean toward:** Option A for v2.0.0, defer listener to v2.1.0 if needed.

---

### Q2: Checkpoint Browser UI
**Question:** Should we add interactive Discord views (buttons, dropdowns) for checkpoint selection in restore/delete?

**Options:**
- **Option A:** Text-based autocomplete (simpler, current pattern)
- **Option B:** Discord SelectView with checkpoint list (more user-friendly)

**Lean toward:** Option A for v2.0.0, nice-to-have for v2.1.0.

---

### Q3: Config Hot-Reload
**Question:** Should changes to campaigns.yaml be picked up without restarting bot/CLI?

**Options:**
- **Option A:** Requires restart (simpler)
- **Option B:** Watch file for changes, reload on modify

**Lean toward:** Option A (restart acceptable), defer to v2.1.0 if demand exists.

---

### Q4: Plugin Distribution
**Question:** Should we publish foothold-checkpoint to PyPI, or keep GitHub-only?

**Options:**
- **Option A:** GitHub releases only (current pattern)
- **Option B:** Publish to PyPI for easier installation

**Lean toward:** Option A for now (single user), reconsider if community adoption grows.

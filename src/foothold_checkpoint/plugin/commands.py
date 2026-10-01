"""Discord commands for Foothold checkpoint management.

This module implements the DCSServerBot plugin with Discord slash commands
for checkpoint operations: save, restore, list, delete.
"""

from pathlib import Path
from typing import Any

import discord
from core import Plugin
from discord import app_commands
from services.bot import DCSServerBot

# When packaged for DCSSB, structure is flat: foothold-checkpoint/commands.py imports foothold-checkpoint/core/
# So imports are always .core.* (relative to package root)
from .core.campaign import detect_campaigns
from .core.config import CampaignConfig, Config, load_campaigns
from .core.events import EventHooks
from .core.storage import (
    EmptyBackupError,
    check_undeclared_live_campaign,
    check_unknown_campaign_files,
    delete_checkpoint,
    format_undeclared_live_campaign_warning,
    list_checkpoints,
    restore_checkpoint,
    save_checkpoint,
)
from .formatters import (
    format_checkpoint_details_embed,
    format_delete_success_embed,
    format_error_embed,
    format_restore_success_embed,
    format_save_success_embed,
)
from .listener import FootholdEventListener
from .notifications import send_notification
from .permissions import check_permission, format_permission_denied
from .ui import (
    CampaignSelectView,
    CheckpointDeleteConfirm,
    CheckpointRestoreConfirm,
    PaginatedCheckpointBrowserView,
    PaginatedCheckpointDeleteBrowserView,
    PaginatedCheckpointSelectView,
)

#: Discord refuses more than 25 autocomplete choices in a single response.
AUTOCOMPLETE_LIMIT = 25


class FootholdCheckpoint(Plugin[FootholdEventListener]):
    """Foothold Checkpoint Management Plugin for DCSServerBot.

    Provides Discord slash commands for managing DCS Foothold campaign checkpoints:
    - /foothold-checkpoint save: Create checkpoint from current campaign state
    - /foothold-checkpoint restore: Restore checkpoint to server
    - /foothold-checkpoint list: List available checkpoints
    - /foothold-checkpoint delete: Delete checkpoint

    Integrates with foothold_checkpoint core library for checkpoint operations.
    """

    # Declare command group at class level so decorators can reference it
    checkpoint_group = app_commands.Group(
        name="foothold-checkpoint", description="Manage Foothold campaign checkpoints"
    )

    def __init__(
        self, bot: DCSServerBot, listener: type[FootholdEventListener], name: str | None = None
    ):
        """Initialize the Foothold plugin.

        Args:
            bot: DCSServerBot instance
            listener: EventListener class for DCS events
            name: Optional plugin name override (defaults to auto-detection from module path)
        """
        super().__init__(bot, listener, name=name)
        self.campaigns: dict[str, CampaignConfig] = {}
        self.core_config: Config | None = None

    async def cog_load(self) -> None:
        """Called when the cog is loaded.

        Loads plugin configuration and campaigns using DCSServerBot's config system.
        """
        await super().cog_load()

        try:
            # Load configuration using Plugin's built-in system
            # self.locals contains the DEFAULT section from foothold-checkpoint.yaml
            config_dict = self.locals

            if not config_dict.get("enabled", True):
                self.log.warning("Foothold plugin is disabled in configuration")
                return

            # Load campaigns from campaigns_file
            campaigns_file_path = config_dict.get("campaigns_file", "./campaigns.yaml")
            campaigns_file = Path(campaigns_file_path)

            if not campaigns_file.is_absolute():
                # Make relative to bot root
                campaigns_file = Path.cwd() / campaigns_file

            self.campaigns = load_campaigns(campaigns_file)

            # Create a minimal Config object for storage functions
            # The plugin doesn't use servers, so servers can be None
            # IMPORTANT: Only pass campaigns_file, NOT campaigns (Config validates mutual exclusivity)
            checkpoints_dir = Path(config_dict.get("checkpoints_dir", "./checkpoints"))
            if not checkpoints_dir.is_absolute():
                checkpoints_dir = Path.cwd() / checkpoints_dir

            self.core_config = Config(
                checkpoints_dir=checkpoints_dir,
                servers=None,
                campaigns_file=campaigns_file,
            )

            self.log.info(
                f"Loaded configuration with {len(self.campaigns)} campaigns from {campaigns_file}"
            )

        except Exception as e:
            self.log.error(f"Failed to load Foothold plugin: {e}", exc_info=True)
            raise

    async def cog_unload(self) -> None:
        """Called when the cog is unloaded.

        Cleanup resources and log unload event.
        """
        await super().cog_unload()
        self.campaigns = {}
        self.core_config = None

    def _get_config(self) -> dict[str, Any]:
        """Get plugin configuration (wrapper for self.locals).

        Returns DEFAULT section or merged DEFAULT + server-specific config.
        For this plugin, we primarily use DEFAULT since it's not server-specific.
        """
        return self.locals

    def _find_campaign(self, campaign: str) -> str | None:
        """Resolve a campaign name against the configuration, ignoring case.

        Checkpoint metadata is written at save time and outlives the config it
        came from, so an exact match is too strict: a campaign that was renamed
        to a different case would make an old checkpoint unrestorable.

        Args:
            campaign: Campaign name as stored in checkpoint metadata.

        Returns:
            The configured campaign id, or None when no campaign matches.
        """
        if campaign in self.campaigns:
            return campaign

        lowered = campaign.lower()
        for configured in self.campaigns:
            if configured.lower() == lowered:
                return configured

        return None

    @staticmethod
    def _format_unknown_files_warning(
        server: str,
        target_dir: Path,
        unknown_files: list[str],
    ) -> str:
        """Build the Discord message shown when the Saves directory holds unknown files.

        This warns, it does not refuse: an unconfigured campaign sitting on the
        server is no reason to stop backing up the configured ones. The operation
        that would actually lose data - a restore whose backup captured nothing -
        is stopped in the core instead.

        Args:
            server: Name of the DCS server being operated on.
            target_dir: The Missions/Saves directory that was inspected.
            unknown_files: Campaign-looking files missing from the configuration.

        Returns:
            A Discord-formatted warning message.
        """
        listed = "\n".join(f"- `{name}`" for name in unknown_files)

        return (
            f"⚠️ **Files on `{server}` that this plugin cannot see**\n\n"
            f"These are in `{target_dir}` but are missing from the campaign "
            f"configuration:\n{listed}\n\n"
            "They are never backed up, and a restore would write its files beside them "
            "rather than over them. If they belong to a campaign you rely on, its "
            "backups are not protecting anything.\n\n"
            "Ask your server admin to add these names to `campaigns.yaml`."
        )

    async def _check_permission(self, interaction: discord.Interaction, operation: str) -> bool:
        """Check if user has permission for operation.

        Args:
            interaction: Discord interaction
            operation: Operation name ('save', 'restore', 'list', 'delete')

        Returns:
            True if user has permission

        Raises:
            discord.app_commands.CheckFailure: If user lacks permission
        """
        config_dict = self._get_config()
        if not await check_permission(interaction, config_dict, operation):
            allowed_roles = config_dict.get("permissions", {}).get(operation, [])
            message = format_permission_denied(operation, allowed_roles)
            await interaction.response.send_message(message, ephemeral=True)
            return False
        return True

    # Autocomplete functions
    async def server_autocomplete(
        self,
        _interaction: discord.Interaction,
        current: str,
    ) -> list[app_commands.Choice[str]]:
        """Autocomplete for server parameter.

        Args:
            interaction: Discord interaction
            current: Current user input

        Returns:
            List of matching server choices
        """
        servers = list(self.bot.servers.keys())
        matches = [
            app_commands.Choice(name=server, value=server)
            for server in servers
            if current.lower() in server.lower()
        ]

        return matches[:AUTOCOMPLETE_LIMIT]

    # Discord Command: /foothold-checkpoint save
    @checkpoint_group.command(name="save", description="Save a checkpoint for a campaign")
    @app_commands.autocomplete(server=server_autocomplete)
    @app_commands.describe(
        server="DCS server - determines Missions/Saves directory",
    )
    async def save_command(
        self,
        interaction: discord.Interaction,
        server: str,
    ) -> None:
        """Save a checkpoint for the specified campaign(s) using interactive selection.

        Args:
            interaction: Discord interaction
            server: Server name from DCSSB servers
        """
        # Check permissions
        if not await self._check_permission(interaction, "save"):
            return

        # Validate server exists
        if server not in self.bot.servers:
            available_servers = ", ".join(self.bot.servers.keys())
            await interaction.response.send_message(
                f"❌ Unknown server: `{server}`\n" f"Available servers: {available_servers}",
                ephemeral=True,
            )
            return

        server_name = server

        # Always use interactive campaign selector
        if not self.campaigns:
            await interaction.response.send_message(
                "❌ No campaigns configured. Please configure campaigns in `campaigns.yaml`.",
                ephemeral=True,
            )
            return

        # Get DCSSB server instance to detect available campaigns
        dcssb_server = self.bot.servers[server_name]
        try:
            # Get Missions/Saves from server instance
            missions_saves_dir = Path(dcssb_server.instance.home) / "Missions" / "Saves"
            if not missions_saves_dir.exists():
                await interaction.response.send_message(
                    f"❌ Missions/Saves directory not found for server `{server}`: {missions_saves_dir}",
                    ephemeral=True,
                )
                return

            # Detect campaigns by listing files in the directory
            campaign_files = [f.name for f in missions_saves_dir.iterdir() if f.is_file()]
            self.log.debug(f"Found {len(campaign_files)} files in {missions_saves_dir}")
            self.log.debug(f"Files: {campaign_files[:10]}")
            self.log.debug(f"Config campaigns: {list(self.campaigns.keys())}")

            # Build a minimal config object with campaigns for detection
            # (self.core_config has campaigns_file but not campaigns loaded)
            from .core.config import Config

            temp_config = Config(
                checkpoints_dir=self.core_config.checkpoints_dir,
                campaigns=self.campaigns,
                servers=None,
            )

            detected_campaigns = detect_campaigns(campaign_files, temp_config)
            self.log.debug(f"Detected campaigns: {list(detected_campaigns.keys())}")

            if not detected_campaigns:
                # Show detailed error with file list for debugging
                files_info = ", ".join(campaign_files[:5]) if campaign_files else "no files"
                if len(campaign_files) > 5:
                    files_info += f" ...and {len(campaign_files) - 5} more"

                # Also show configured campaign file patterns for comparison
                config_info = "\n".join(
                    [
                        f"• **{cid}**: {', '.join(cfg.files.persistence.files[:2])}"
                        for cid, cfg in list(self.campaigns.items())[:3]
                    ]
                )

                await interaction.response.send_message(
                    f"❌ No campaign files found in `{missions_saves_dir}`.\n\n"
                    f"📂 **Files in directory ({len(campaign_files)} total):**\n{files_info}\n\n"
                    f"⚙️ **Configured campaigns (showing first 3):**\n{config_info}\n\n"
                    f"Make sure campaign file names in `campaigns.yaml` match the actual files on the server.",
                    ephemeral=True,
                )
                return

            # Filter self.campaigns to only include detected campaigns
            available_campaigns = {
                campaign_id: self.campaigns[campaign_id]
                for campaign_id in detected_campaigns
                if campaign_id in self.campaigns
            }

            if not available_campaigns:
                detected_names = ", ".join(detected_campaigns.keys())
                await interaction.response.send_message(
                    f"❌ Detected campaigns ({detected_names}) are not configured in `campaigns.yaml`.\n"
                    f"Please add campaign configurations for these campaigns.",
                    ephemeral=True,
                )
                return

        except AttributeError as e:
            self.log.error(f"Failed to access server installation path: {e}")
            await interaction.response.send_message(
                f"❌ Could not determine Missions/Saves path for server `{server}`. Check DCSSB server configuration.",
                ephemeral=True,
            )
            return

        # Show campaign selection view with only detected campaigns
        view = CampaignSelectView(available_campaigns)
        detected_count = len(available_campaigns)
        await interaction.response.send_message(
            f"📁 **Select campaign(s) to save from server `{server}`:**\n"
            f"📊 {detected_count} campaign{'s' if detected_count != 1 else ''} detected in Missions/Saves",
            view=view,
            ephemeral=True,
        )

        # Wait for user selection
        await view.wait()

        if view.selected_campaigns is None:
            # Timeout or cancelled
            return

        # Save selected campaigns
        campaigns_to_save = view.selected_campaigns

        # Get metadata from modal if user provided it
        name = None
        comment = None
        if view.metadata_modal:
            name = view.metadata_modal.checkpoint_name
            comment = view.metadata_modal.checkpoint_comment

        # Update message to show saving is in progress
        campaign_names = ", ".join(
            [available_campaigns[c].display_name or c for c in campaigns_to_save]
        )
        metadata_info = ""
        if name:
            metadata_info += f"\n📝 Name: **{name}**"
        if comment:
            metadata_info += f"\n💬 Comment: _{comment}_"
        await interaction.edit_original_response(
            content=f"✅ **Saving checkpoints for: {campaign_names}**{metadata_info}\n\n⏳ Please wait...",
            view=None,
        )

        # Save each selected campaign
        results = []
        errors = []

        # Build temp config with campaigns loaded (for save_checkpoint's detect_campaigns call)
        from .core.config import Config

        temp_config = Config(
            checkpoints_dir=self.core_config.checkpoints_dir, campaigns=self.campaigns, servers=None
        )

        # Files the configuration does not know are never captured by a save, and
        # the omission is invisible. Say so loudly - but do not block: an
        # unconfigured campaign on the server is no reason to stop backing up the
        # ones that are configured. A campaign whose own files are unrecognised
        # fails on its own below, with "No campaign files found".
        unknown_files: list[str] = []
        undeclared_live: str | None = None
        try:
            saves_dir = Path(self.bot.servers[server_name].instance.home) / "Missions" / "Saves"
        except (AttributeError, KeyError) as e:
            self.log.warning(f"Cannot locate Missions/Saves for {server_name}: {e}")
        else:
            unknown_files = check_unknown_campaign_files(saves_dir, temp_config)
            if unknown_files:
                self.log.warning(
                    f"Unconfigured Foothold files in {saves_dir}: {', '.join(unknown_files)}"
                )

            # Stronger than the warning above, and worth its own message: this is
            # not some stray file, it is the campaign people are playing right
            # now, and no checkpoint of it will exist.
            undeclared_live = check_undeclared_live_campaign(saves_dir, temp_config)
            if undeclared_live:
                self.log.error(
                    f"No checkpoint exists for the campaign running on {server_name}: "
                    f"the mission writes to {undeclared_live}, declared by no campaign"
                )

        for camp in campaigns_to_save:
            try:
                # Get campaign config
                actual_camp = self._find_campaign(camp)
                if actual_camp is None:
                    errors.append(f"Unknown campaign: {camp}")
                    continue
                camp = actual_camp

                config_dict = self._get_config()
                checkpoints_dir = Path(config_dict["checkpoints_dir"])

                # Determine source directory from DCSSB server instance
                dcssb_server = self.bot.servers[server_name]
                try:
                    # Get Missions/Saves from server instance
                    missions_saves_dir = Path(dcssb_server.instance.home) / "Missions" / "Saves"
                    if not missions_saves_dir.exists():
                        errors.append(f"{camp}: Missions/Saves not found at {missions_saves_dir}")
                        continue
                    source_dir = missions_saves_dir
                except AttributeError as e:
                    errors.append(f"{camp}: Cannot access server installation path - {e}")
                    continue

                async def on_progress(current: int, total: int) -> None:
                    """Update Discord UI with progress."""
                    self.log.debug(f"Save progress: {current}/{total}")

                hooks = EventHooks(on_save_progress=on_progress)

                # Execute save with temp_config that has campaigns loaded
                checkpoint_path = await save_checkpoint(
                    campaign_name=camp,
                    server_name=server_name,
                    source_dir=source_dir,
                    output_dir=checkpoints_dir,
                    config=temp_config,
                    name=name,
                    comment=comment,
                    hooks=hooks,
                )

                # Calculate size
                size_bytes = checkpoint_path.stat().st_size if checkpoint_path.exists() else 0
                size_mb = size_bytes / (1024 * 1024)
                size_human = f"{size_mb:.2f} MB"

                results.append(
                    {
                        "campaign": camp,
                        "filename": checkpoint_path.name,
                        "size": size_human,
                        "server": server_name,
                    }
                )

                # Send notification
                if interaction.guild:
                    self.log.info(
                        f"Attempting to send 'save' notification for campaign={camp}, "
                        f"checkpoint={checkpoint_path.name}, guild={interaction.guild.name}"
                    )
                    await send_notification(
                        guild=interaction.guild,
                        config=config_dict,
                        event_type="save",
                        campaign=camp,
                        user=interaction.user,
                        checkpoint=checkpoint_path,
                    )
                else:
                    self.log.warning("No guild in interaction - cannot send notification")

            except Exception as e:
                self.log.error(f"Failed to save checkpoint for {camp}: {e}", exc_info=True)
                errors.append(f"{camp}: {str(e)}")

        # Send results
        # Always delete "Please wait..." message from interactive selector
        await interaction.delete_original_response()

        if unknown_files:
            await interaction.followup.send(
                self._format_unknown_files_warning(server_name, saves_dir, unknown_files),
                ephemeral=True,
            )

        if undeclared_live:
            await interaction.followup.send(
                "❌ **The campaign being played was not saved**\n```\n"
                + format_undeclared_live_campaign_warning(
                    undeclared_live, server_name, saves_dir, temp_config
                )
                + "```",
                ephemeral=True,
            )

        if len(campaigns_to_save) == 1:
            # Single campaign - use detailed embed
            if results:
                result = results[0]
                embed = format_save_success_embed(
                    checkpoint_filename=result["filename"],
                    campaign=result["campaign"],
                    server=result["server"],
                    size=result["size"],
                    name=name,
                    comment=comment,
                )
                await interaction.followup.send(embed=embed, ephemeral=True)
            else:
                error_msg = errors[0] if errors else "Unknown error"
                embed = format_error_embed("save", Exception(error_msg))
                await interaction.followup.send(embed=embed, ephemeral=True)
        else:
            # Multiple campaigns - use summary embed
            embed = discord.Embed(
                title="📦 Bulk Save Complete",
                color=discord.Color.green() if results else discord.Color.red(),
                timestamp=discord.utils.utcnow(),
            )

            if results:
                results_text = "\n".join(
                    [f"✅ **{r['campaign']}**: `{r['filename']}` ({r['size']})" for r in results]
                )
                embed.add_field(name=f"Saved ({len(results)})", value=results_text, inline=False)

            if errors:
                errors_text = "\n".join([f"❌ {e}" for e in errors])
                embed.add_field(name=f"Errors ({len(errors)})", value=errors_text, inline=False)

            embed.set_footer(text=f"Saved by {interaction.user.name} from server {server}")
            await interaction.followup.send(embed=embed, ephemeral=True)

    # Discord Command: /foothold-checkpoint restore
    @checkpoint_group.command(name="restore", description="Restore a checkpoint")
    @app_commands.autocomplete(server=server_autocomplete)
    @app_commands.describe(
        server="DCS server - determines Missions/Saves directory",
    )
    async def restore_command(
        self,
        interaction: discord.Interaction,
        server: str,
    ) -> None:
        """Restore a checkpoint using interactive selection.

        Args:
            interaction: Discord interaction
            server: Server name from DCSSB servers
        """
        # Check permissions
        if not await self._check_permission(interaction, "restore"):
            return

        # Validate server exists
        if server not in self.bot.servers:
            available_servers = ", ".join(self.bot.servers.keys())
            await interaction.response.send_message(
                f"❌ Unknown server: `{server}`\n" f"Available servers: {available_servers}",
                ephemeral=True,
            )
            return

        # Always use interactive selector for checkpoint
        # Auto-backup is always enabled for safety
        auto_backup = True

        await interaction.response.defer(thinking=True, ephemeral=True)

        config_dict = self._get_config()
        checkpoints_dir = Path(config_dict["checkpoints_dir"])

        # Get checkpoints
        checkpoints_list = await list_checkpoints(
            checkpoint_dir=checkpoints_dir, campaign_filter=None
        )

        if not checkpoints_list:
            await interaction.followup.send(
                "❌ No checkpoints available to restore.", ephemeral=True
            )
            return

        # Show paginated checkpoint selection view
        view = PaginatedCheckpointSelectView(checkpoints_list)
        await interaction.followup.send(
            view._get_header_text(),
            view=view,
            ephemeral=True,
        )

        # Wait for user selection
        await view.wait()

        if view.selected_checkpoint is None:
            # Timeout or cancelled
            return

        # Use selected checkpoint
        selected = view.selected_checkpoint
        checkpoint = selected["filename"]
        campaign = selected.get("campaign", "unknown")

        # Show confirmation dialog with full checkpoint details
        confirm_view = CheckpointRestoreConfirm(selected, server, auto_backup)

        # Use detailed embed formatter
        from .formatters import format_checkpoint_details_embed

        details_embed = format_checkpoint_details_embed(selected)
        details_embed.title = "⚠️ Confirm Restoration"
        details_embed.color = discord.Color.blue()

        warning_text = f"This will restore the checkpoint to server **{server}**."
        if auto_backup:
            warning_text += "\n✅ An auto-backup will be created before restoration."
        else:
            warning_text += "\n⚠️ **No backup** will be created!"

        details_embed.add_field(name="⚠️ Warning", value=warning_text, inline=False)

        await interaction.followup.send(
            embed=details_embed, view=confirm_view, ephemeral=True, wait=True
        )

        # Wait for confirmation
        await confirm_view.wait()

        if not confirm_view.confirmed:
            # User cancelled
            return

        try:
            # Get campaign config. Checkpoint metadata predates the current
            # config, so match case-insensitively rather than refusing outright.
            actual_campaign = self._find_campaign(campaign)
            if actual_campaign is None:
                await interaction.followup.send(
                    f"❌ Unknown campaign: {campaign}\n"
                    f"Known campaigns: {', '.join(sorted(self.campaigns))}",
                    ephemeral=True,
                )
                return
            campaign = actual_campaign

            config_dict = self._get_config()
            checkpoints_dir = Path(config_dict["checkpoints_dir"])
            checkpoint_path = checkpoints_dir / checkpoint

            # Determine target directory from DCSSB server instance
            dcssb_server = self.bot.servers[server]
            try:
                # Get Missions/Saves from server instance
                missions_saves_dir = Path(dcssb_server.instance.home) / "Missions" / "Saves"
                if not missions_saves_dir.exists():
                    await interaction.followup.send(
                        f"❌ Missions/Saves directory not found for server `{server}`: {missions_saves_dir}",
                        ephemeral=True,
                    )
                    return
                target_dir = missions_saves_dir
            except AttributeError as e:
                self.log.error(f"Failed to access server installation path: {e}")
                await interaction.followup.send(
                    f"❌ Could not determine Missions/Saves path for server `{server}`. Check DCSSB server configuration.",
                    ephemeral=True,
                )
                return

            server_name = server

            # Build temp config with campaigns loaded (for create_auto_backup's detect_campaigns call)
            from .core.config import Config

            temp_config = Config(
                checkpoints_dir=self.core_config.checkpoints_dir,
                campaigns=self.campaigns,
                servers=None,
            )

            # Files the configuration does not know are flagged here, but the
            # decision to stop belongs to restore_checkpoint: it refuses only when
            # its automatic backup captured nothing, which is the case where state
            # would actually be lost. Refusing on their mere presence would block
            # restoring one campaign because another is unconfigured.
            unknown_files = check_unknown_campaign_files(target_dir, temp_config)
            if unknown_files:
                self.log.warning(
                    f"Unconfigured Foothold files in {target_dir}: {', '.join(unknown_files)}"
                )

            # Create event hooks. The backup path is captured here rather than
            # guessed afterwards: auto-backups are named after their campaign,
            # not "auto-backup-*", so globbing for them never matched anything.
            captured_backup: dict[str, str] = {}

            async def on_progress(current: int, total: int) -> None:
                """Update Discord UI with progress."""
                self.log.debug(f"Restore progress: {current}/{total}")

            async def on_backup_complete(backup_path: Path) -> None:
                """Remember the backup that was actually created."""
                captured_backup["filename"] = Path(backup_path).name

            hooks = EventHooks(
                on_restore_progress=on_progress,
                on_backup_complete=on_backup_complete,
            )

            # Execute restore with skip_overwrite_check=True since we already confirmed via UI
            await restore_checkpoint(
                checkpoint_path=checkpoint_path,
                target_dir=target_dir,
                config=temp_config,  # Use temp_config with campaigns loaded
                server_name=server_name,
                auto_backup=auto_backup,
                hooks=hooks,
                skip_overwrite_check=True,  # Skip CLI confirmation since we already confirmed via Discord UI
            )

            # Send success response
            backup_filename = captured_backup.get("filename") if auto_backup else None

            embed = format_restore_success_embed(
                checkpoint_filename=checkpoint,
                campaign=campaign,
                server=server_name,
                backup_created=auto_backup,
                backup_filename=backup_filename,
            )
            await interaction.followup.send(embed=embed, ephemeral=True)

            # Send notification
            if interaction.guild:
                config_dict = self._get_config()
                await send_notification(
                    guild=interaction.guild,
                    config=config_dict,
                    event_type="restore",
                    campaign=campaign,
                    user=interaction.user,
                    checkpoint=checkpoint_path,
                    auto_backup=str(auto_backup),
                )

        except EmptyBackupError as e:
            # The safety net caught nothing, so nothing was written. Say so in
            # plain terms rather than through the generic error embed.
            self.log.error(f"Restore aborted, backup captured nothing: {e}", exc_info=True)
            await interaction.followup.send(
                f"⛔ **Restore aborted — nothing was changed.**\n\n{e}",
                ephemeral=True,
            )
            if interaction.guild:
                await send_notification(
                    guild=interaction.guild,
                    config=self._get_config(),
                    event_type="error",
                    campaign=campaign,
                    user=interaction.user,
                    error=e,
                )

        except Exception as e:
            self.log.error(f"Failed to restore checkpoint: {e}", exc_info=True)
            embed = format_error_embed("restore", e)
            await interaction.followup.send(embed=embed, ephemeral=True)

            # Send error notification
            if interaction.guild:
                config_dict = self._get_config()
                await send_notification(
                    guild=interaction.guild,
                    config=config_dict,
                    event_type="error",
                    campaign=campaign,
                    user=interaction.user,
                    error=e,
                )

    # Discord Command: /foothold-checkpoint list
    @checkpoint_group.command(name="list", description="List available checkpoints")
    async def list_command(
        self,
        interaction: discord.Interaction,
    ) -> None:
        """List available checkpoints with interactive browser.

        Args:
            interaction: Discord interaction
        """
        # Check permissions
        if not await self._check_permission(interaction, "list"):
            return

        await interaction.response.defer(thinking=True, ephemeral=True)

        try:
            config_dict = self._get_config()
            checkpoints_dir = Path(config_dict["checkpoints_dir"])

            # Get checkpoints
            checkpoints_list = await list_checkpoints(
                checkpoint_dir=checkpoints_dir, campaign_filter=None
            )

            if not checkpoints_list:
                await interaction.followup.send("❌ No checkpoints found.", ephemeral=True)
                return

            # Create interactive paginated browser view with filters
            view = PaginatedCheckpointBrowserView(
                checkpoints=checkpoints_list, format_details_func=format_checkpoint_details_embed
            )

            # Get initial embed (first checkpoint after applying default filter)
            filtered = view._get_filtered_checkpoints()
            if filtered:
                initial_embed = format_checkpoint_details_embed(filtered[0])
                header_text = view._get_header_text(filtered)
            else:
                initial_embed = None
                header_text = "📦 No checkpoints found"

            # Build initial message
            await interaction.followup.send(
                content=header_text,
                embed=initial_embed,
                view=view,
                ephemeral=True,
            )

        except Exception as e:
            self.log.error(f"Failed to list checkpoints: {e}", exc_info=True)
            embed = format_error_embed("list", e)
            await interaction.followup.send(embed=embed, ephemeral=True)

    # Discord Command: /foothold-checkpoint delete
    @checkpoint_group.command(name="delete", description="Delete a checkpoint")
    async def delete_command(
        self,
        interaction: discord.Interaction,
    ) -> None:
        """Delete a checkpoint using interactive selection.

        Args:
            interaction: Discord interaction
        """
        # Check permissions
        if not await self._check_permission(interaction, "delete"):
            return

        # Always use interactive browser
        await interaction.response.defer(thinking=True, ephemeral=True)

        config_dict = self._get_config()
        checkpoints_dir = Path(config_dict["checkpoints_dir"])

        # Get checkpoints
        checkpoints_list = await list_checkpoints(
            checkpoint_dir=checkpoints_dir, campaign_filter=None
        )

        if not checkpoints_list:
            await interaction.followup.send(
                "❌ No checkpoints available to delete.", ephemeral=True
            )
            return

        # Import formatter before using it
        from .formatters import format_checkpoint_details_embed

        # Create interactive paginated browser view with Delete button and filters
        view = PaginatedCheckpointDeleteBrowserView(
            checkpoints=checkpoints_list, format_details_func=format_checkpoint_details_embed
        )

        # Get initial embed (first checkpoint after applying default filter)
        filtered = view._get_filtered_checkpoints()
        if filtered:
            initial_embed = format_checkpoint_details_embed(filtered[0])
            header_text = view._get_header_text(filtered)
        else:
            initial_embed = None
            header_text = "🗑️ No checkpoints found"

        # Build initial message
        await interaction.followup.send(
            content=header_text,
            embed=initial_embed,
            view=view,
            ephemeral=True,
        )

        # Wait for user interaction
        await view.wait()

        if not view.delete_requested:
            # Timeout or user didn't click Delete
            return

        # Use selected checkpoint from browser
        selected_checkpoint_dict = checkpoints_list[view.current_index]
        checkpoint = selected_checkpoint_dict["filename"]
        campaign = selected_checkpoint_dict.get("campaign", "unknown")

        # Store the browser state for potential restoration on cancel
        browser_checkpoints = checkpoints_list
        browser_index = view.current_index
        browser_type_filter = view.type_filter
        browser_campaign_filter = view.campaign_filter
        browser_page = view.current_page

        # Create restore function for cancel button
        async def restore_browser(cancel_interaction: discord.Interaction) -> None:
            """Restore the browser view after cancellation."""
            from .formatters import format_checkpoint_details_embed

            # Recreate the browser view with same filters
            new_view = PaginatedCheckpointDeleteBrowserView(
                checkpoints=browser_checkpoints, format_details_func=format_checkpoint_details_embed
            )
            new_view.current_index = browser_index
            new_view.type_filter = browser_type_filter
            new_view.campaign_filter = browser_campaign_filter
            new_view.current_page = browser_page
            new_view._build_ui()

            # Get the filtered checkpoints and current checkpoint embed
            filtered = new_view._get_filtered_checkpoints()
            current_embed = format_checkpoint_details_embed(filtered[browser_index])
            header_text = new_view._get_header_text(filtered)

            # Update message to show browser again
            await cancel_interaction.response.edit_message(
                content=header_text,
                embed=current_embed,
                view=new_view,
            )

        confirm_view = CheckpointDeleteConfirm(
            selected_checkpoint_dict,
            restore_browser_func=restore_browser,
        )

        # Use detailed embed formatter
        from .formatters import format_checkpoint_details_embed

        details_embed = format_checkpoint_details_embed(selected_checkpoint_dict)
        details_embed.title = "⚠️ Confirm Deletion"
        details_embed.color = discord.Color.orange()
        details_embed.add_field(
            name="⚠️ Warning", value="This action cannot be undone!", inline=False
        )

        # Replace the browser message with confirmation dialog
        await interaction.edit_original_response(embed=details_embed, view=confirm_view)

        # Wait for confirmation
        await confirm_view.wait()

        if not confirm_view.confirmed:
            # User cancelled - browser has been restored by the cancel button
            return

        # Now execute deletion (user has confirmed via UI, so use force=True)
        try:
            config_dict = self._get_config()
            checkpoints_dir = Path(config_dict["checkpoints_dir"])
            checkpoint_path = checkpoints_dir / checkpoint

            # Execute delete with force=True since we already confirmed via UI
            await delete_checkpoint(checkpoint_path=checkpoint_path, force=True)

            # Update with success message
            embed = format_delete_success_embed(checkpoint_filename=checkpoint, campaign=campaign)
            await interaction.edit_original_response(content=None, embed=embed, view=None)

            # Send notification
            if interaction.guild:
                config_dict = self._get_config()
                self.log.info(
                    f"Attempting to send 'delete' notification for campaign={campaign}, "
                    f"checkpoint={checkpoint_path.name}, guild={interaction.guild.name}"
                )
                await send_notification(
                    guild=interaction.guild,
                    config=config_dict,
                    event_type="delete",
                    campaign=campaign,
                    user=interaction.user,
                    checkpoint=checkpoint_path,
                )
            else:
                self.log.warning("No guild in interaction - cannot send delete notification")

        except Exception as e:
            self.log.error(f"Failed to delete checkpoint: {e}", exc_info=True)
            embed = format_error_embed("delete", e)
            await interaction.edit_original_response(content=None, embed=embed, view=None)

            # Send error notification
            if interaction.guild:
                config_dict = self._get_config()
                await send_notification(
                    guild=interaction.guild,
                    config=config_dict,
                    event_type="error",
                    campaign=campaign,
                    user=interaction.user,
                    error=e,
                )


async def setup(bot: DCSServerBot) -> None:
    """Setup function called by DCSServerBot to load the plugin.

    This is the entry point that DCSSB calls when loading plugins/{name}/commands.py.

    Args:
        bot: DCSServerBot instance
    """
    # IMPORTANT: Pass explicit name to avoid DCSSB deriving wrong name from module path
    plugin = FootholdCheckpoint(bot, FootholdEventListener, name="foothold-checkpoint")

    # add_cog automatically registers all commands decorated with @app_commands.command
    # No need to manually add commands to tree
    await bot.add_cog(plugin)

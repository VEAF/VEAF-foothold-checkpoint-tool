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
    delete_checkpoint,
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
    CheckpointBrowserView,
    CheckpointDeleteBrowserView,
    CheckpointDeleteConfirm,
    CheckpointRestoreConfirm,
    CheckpointSelectView,
)


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
        return [
            app_commands.Choice(name=server, value=server)
            for server in servers
            if current.lower() in server.lower()
        ][:25]  # Discord autocomplete limit

    # Discord Command: /foothold-checkpoint save
    @checkpoint_group.command(name="save", description="Save a checkpoint for a campaign")
    @app_commands.autocomplete(server=server_autocomplete)
    @app_commands.describe(
        server="DCS server (required) - determines Missions/Saves directory",
        campaign="Campaign to save (leave empty for interactive selection)",
        name="Optional custom name for the checkpoint",
        comment="Optional comment describing the checkpoint",
    )
    async def save_command(
        self,
        interaction: discord.Interaction,
        server: str,
        campaign: str | None = None,
        name: str | None = None,
        comment: str | None = None,
    ) -> None:
        """Save a checkpoint for the specified campaign(s).

        Args:
            interaction: Discord interaction
            server: Server name from DCSSB servers - required
            campaign: Campaign name to save (None for interactive selection)
            name: Optional custom checkpoint name
            comment: Optional checkpoint comment
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

        # If no campaign specified, show interactive selector
        if campaign is None:
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

            # Get metadata from modal if user provided it (override command parameters)
            if view.metadata_modal:
                # Use modal values if provided, otherwise keep command parameter values
                modal_name = view.metadata_modal.checkpoint_name
                modal_comment = view.metadata_modal.checkpoint_comment
                if modal_name:
                    name = modal_name
                if modal_comment:
                    comment = modal_comment

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
        else:
            # Single campaign specified - validate it exists in server's Missions/Saves
            # Defer for potentially long operation
            await interaction.response.defer(thinking=True, ephemeral=True)

            # Validate campaign is detected in server
            dcssb_server = self.bot.servers[server_name]
            try:
                missions_saves_dir = Path(dcssb_server.instance.home) / "Missions" / "Saves"
                if not missions_saves_dir.exists():
                    await interaction.followup.send(
                        f"❌ Missions/Saves directory not found for server `{server}`: {missions_saves_dir}",
                        ephemeral=True,
                    )
                    return

                # Detect campaigns by listing files in the directory
                campaign_files = [f.name for f in missions_saves_dir.iterdir() if f.is_file()]

                # Build a minimal config object with campaigns for detection
                from .core.config import Config

                temp_config = Config(
                    checkpoints_dir=self.core_config.checkpoints_dir,
                    campaigns=self.campaigns,
                    servers=None,
                )

                detected_campaigns = detect_campaigns(campaign_files, temp_config)

                # Check if specified campaign is detected
                if campaign not in detected_campaigns:
                    available = (
                        ", ".join(detected_campaigns.keys()) if detected_campaigns else "none"
                    )
                    await interaction.followup.send(
                        f"❌ Campaign `{campaign}` not found in server `{server}`.\n"
                        f"📊 Detected campaigns: {available}\n\n"
                        f"Make sure the campaign files exist in `{missions_saves_dir}`.",
                        ephemeral=True,
                    )
                    return

            except AttributeError as e:
                self.log.error(f"Failed to access server installation path: {e}")
                await interaction.followup.send(
                    f"❌ Could not determine Missions/Saves path for server `{server}`. Check DCSSB server configuration.",
                    ephemeral=True,
                )
                return

            campaigns_to_save = [campaign]

        # Save each selected campaign
        results = []
        errors = []

        # Build temp config with campaigns loaded (for save_checkpoint's detect_campaigns call)
        from .core.config import Config

        temp_config = Config(
            checkpoints_dir=self.core_config.checkpoints_dir, campaigns=self.campaigns, servers=None
        )

        for camp in campaigns_to_save:
            try:
                # Get campaign config
                if camp not in self.campaigns:
                    errors.append(f"Unknown campaign: {camp}")
                    continue

                # Verify campaign exists in config
                _ = self.campaigns[camp]  # Validates campaign exists
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
                if campaign is None:
                    await interaction.followup.send(embed=embed, ephemeral=True)
                else:
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
        server="DCS server (required) - determines Missions/Saves directory",
        checkpoint="Checkpoint to restore (leave empty for interactive selection)",
        campaign="Campaign to restore to (optional, defaults to checkpoint's original campaign)",
        auto_backup="Create automatic backup before restoring (default: True)",
    )
    async def restore_command(
        self,
        interaction: discord.Interaction,
        server: str,
        checkpoint: str | None = None,
        campaign: str | None = None,
        auto_backup: bool = True,
    ) -> None:
        """Restore a checkpoint for the specified campaign.

        Args:
            interaction: Discord interaction
            server: Server name from DCSSB servers - required
            checkpoint: Optional checkpoint filename to restore
            campaign: Optional campaign name to restore to
            auto_backup: Whether to create auto-backup before restore
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

        # Track selected checkpoint dict for detailed confirmation
        selected_checkpoint_dict = None

        # If no checkpoint specified, show interactive selector
        if checkpoint is None:
            await interaction.response.defer(thinking=True, ephemeral=True)

            config_dict = self._get_config()
            checkpoints_dir = Path(config_dict["checkpoints_dir"])

            # Get checkpoints
            checkpoints_list = await list_checkpoints(
                checkpoint_dir=checkpoints_dir, campaign_filter=campaign
            )

            if not checkpoints_list:
                await interaction.followup.send(
                    "❌ No checkpoints available to restore.", ephemeral=True
                )
                return

            # Show checkpoint selection view
            view = CheckpointSelectView(checkpoints_list)
            await interaction.followup.send(
                f"🔄 **Select checkpoint to restore to server `{server}`:**",
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
            selected_checkpoint_dict = selected  # Save for confirmation dialog
            checkpoint = selected["filename"]
            # If campaign not specified, use checkpoint's campaign
            if campaign is None:
                campaign = selected.get("campaign")

        # If checkpoint still None, error
        if checkpoint is None:
            await interaction.response.send_message("❌ No checkpoint specified.", ephemeral=True)
            return

        # Build checkpoint dict for confirmation dialog
        if campaign is None:
            campaign = "unknown"

        if selected_checkpoint_dict:
            checkpoint_dict = selected_checkpoint_dict
        else:
            checkpoint_dict = {
                "filename": checkpoint,
                "campaign": campaign,
            }

        # Show confirmation dialog with full checkpoint details
        confirm_view = CheckpointRestoreConfirm(checkpoint_dict, server, auto_backup)

        # Use detailed embed formatter
        from .formatters import format_checkpoint_details_embed

        details_embed = format_checkpoint_details_embed(checkpoint_dict)
        details_embed.title = "⚠️ Confirm Restoration"
        details_embed.color = discord.Color.blue()

        warning_text = f"This will restore the checkpoint to server **{server}**."
        if auto_backup:
            warning_text += "\n✅ An auto-backup will be created before restoration."
        else:
            warning_text += "\n⚠️ **No backup** will be created!"

        details_embed.add_field(name="⚠️ Warning", value=warning_text, inline=False)

        if interaction.response.is_done():
            await interaction.followup.send(
                embed=details_embed, view=confirm_view, ephemeral=True, wait=True
            )
        else:
            await interaction.response.send_message(
                embed=details_embed, view=confirm_view, ephemeral=True
            )

        # Wait for confirmation
        await confirm_view.wait()

        if not confirm_view.confirmed:
            # User cancelled
            return

        # Defer response for long operation (if not already deferred)
        if not interaction.response.is_done():
            await interaction.response.defer(thinking=True, ephemeral=True)

        try:
            # Get campaign config
            if campaign not in self.campaigns:
                await interaction.followup.send(f"❌ Unknown campaign: {campaign}", ephemeral=True)
                return

            # Verify campaign exists in config
            _ = self.campaigns[campaign]  # Validates campaign exists
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

            # Create event hooks
            async def on_progress(current: int, total: int) -> None:
                """Update Discord UI with progress."""
                self.log.debug(f"Restore progress: {current}/{total}")

            hooks = EventHooks(on_restore_progress=on_progress)

            # Build temp config with campaigns loaded (for create_auto_backup's detect_campaigns call)
            from .core.config import Config

            temp_config = Config(
                checkpoints_dir=self.core_config.checkpoints_dir,
                campaigns=self.campaigns,
                servers=None,
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
            backup_filename = None
            if auto_backup:
                # Try to find the backup file that was just created
                # Auto-backups are named: auto-backup-YYYYMMDD-HHMMSS.zip
                backup_pattern = "auto-backup-*.zip"
                backups = list(checkpoints_dir.glob(backup_pattern))
                if backups:
                    # Get the most recent one
                    backup_filename = sorted(backups, key=lambda p: p.stat().st_mtime)[-1].name

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
    @app_commands.describe(campaign="Optional: Filter by campaign")
    async def list_command(
        self,
        interaction: discord.Interaction,
        campaign: str | None = None,
    ) -> None:
        """List available checkpoints with interactive browser.

        Args:
            interaction: Discord interaction
            campaign: Optional campaign filter
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
                checkpoint_dir=checkpoints_dir, campaign_filter=campaign
            )

            if not checkpoints_list:
                message = "❌ No checkpoints found"
                if campaign:
                    message = f"{message} for campaign '{campaign}'"
                await interaction.followup.send(f"{message}.", ephemeral=True)
                return

            # Create interactive browser view
            view = CheckpointBrowserView(
                checkpoints=checkpoints_list, format_details_func=format_checkpoint_details_embed
            )

            # Get initial embed (first checkpoint)
            initial_embed = format_checkpoint_details_embed(checkpoints_list[0])

            # Build initial message
            filter_info = f" for campaign **{campaign}**" if campaign else ""
            await interaction.followup.send(
                content=f"📦 **Checkpoint 1/{len(checkpoints_list)}**{filter_info} - Select from dropdown to view details:",
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
    @app_commands.describe(
        checkpoint="Checkpoint to delete (leave empty for interactive selection)",
        campaign="Campaign filter (optional)",
    )
    async def delete_command(
        self,
        interaction: discord.Interaction,
        checkpoint: str | None = None,
        campaign: str | None = None,
    ) -> None:
        """Delete a checkpoint.

        Args:
            interaction: Discord interaction
            checkpoint: Optional checkpoint filename to delete
            campaign: Optional campaign filter
        """
        # Check permissions
        if not await self._check_permission(interaction, "delete"):
            return

        selected_checkpoint_dict = None

        # If no checkpoint specified, show interactive browser
        if checkpoint is None:
            await interaction.response.defer(thinking=True, ephemeral=True)

            config_dict = self._get_config()
            checkpoints_dir = Path(config_dict["checkpoints_dir"])

            # Get checkpoints
            checkpoints_list = await list_checkpoints(
                checkpoint_dir=checkpoints_dir, campaign_filter=campaign
            )

            if not checkpoints_list:
                await interaction.followup.send(
                    "❌ No checkpoints available to delete.", ephemeral=True
                )
                return

            # Import formatter before using it
            from .formatters import format_checkpoint_details_embed

            # Create interactive browser view with Delete button
            view = CheckpointDeleteBrowserView(
                checkpoints=checkpoints_list, format_details_func=format_checkpoint_details_embed
            )

            # Get initial embed (first checkpoint)
            initial_embed = format_checkpoint_details_embed(checkpoints_list[0])

            # Build initial message
            filter_info = f" for campaign **{campaign}**" if campaign else ""
            await interaction.followup.send(
                content=f"🗑️ **Checkpoint 1/{len(checkpoints_list)}**{filter_info} - Select from dropdown to view details, then click Delete:",
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
            campaign = selected_checkpoint_dict.get("campaign", campaign)

            # Store the browser state for potential restoration on cancel
            browser_checkpoints = checkpoints_list
            browser_index = view.current_index
            browser_campaign_filter = campaign

        # If still no checkpoint, error
        if checkpoint is None:
            await interaction.response.send_message("❌ No checkpoint specified.", ephemeral=True)
            return

        # Show confirmation dialog with full checkpoint details
        if campaign is None:
            campaign = "unknown"

        # Use checkpoint dict from browser or build minimal one
        if selected_checkpoint_dict is None:
            checkpoint_dict = {
                "filename": checkpoint,
                "campaign": campaign,
            }
        else:
            checkpoint_dict = selected_checkpoint_dict

        # Create restore function for cancel button
        async def restore_browser(cancel_interaction: discord.Interaction) -> None:
            """Restore the browser view after cancellation."""
            from .formatters import format_checkpoint_details_embed

            # Recreate the browser view
            new_view = CheckpointDeleteBrowserView(
                checkpoints=browser_checkpoints, format_details_func=format_checkpoint_details_embed
            )
            new_view.current_index = browser_index

            # Get the current checkpoint embed
            current_embed = format_checkpoint_details_embed(browser_checkpoints[browser_index])

            # Update message to show browser again
            filter_info = (
                f" for campaign **{browser_campaign_filter}**" if browser_campaign_filter else ""
            )
            await cancel_interaction.response.edit_message(
                content=f"🗑️ **Checkpoint {browser_index + 1}/{len(browser_checkpoints)}**{filter_info} - Select from dropdown to view details, then click Delete:",
                embed=current_embed,
                view=new_view,
            )

        confirm_view = CheckpointDeleteConfirm(
            checkpoint_dict,
            restore_browser_func=restore_browser if "browser_checkpoints" in locals() else None,
        )

        # Use detailed embed formatter
        from .formatters import format_checkpoint_details_embed

        details_embed = format_checkpoint_details_embed(checkpoint_dict)
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

"""Discord commands for Foothold checkpoint management.

This module implements the DCSServerBot plugin with Discord slash commands
for checkpoint operations: save, restore, list, delete.
"""

from pathlib import Path
from typing import Any

import discord
from discord import app_commands
from discord.ext import commands

from ..core.config import CampaignConfig, Config, load_campaigns
from ..core.events import EventHooks
from ..core.storage import (
    delete_checkpoint,
    list_checkpoints,
    restore_checkpoint,
    save_checkpoint,
)
from .listener import FootholdEventListener
from .notifications import send_notification
from .permissions import check_permission, format_permission_denied
from .schemas import PluginConfig


class Foothold(commands.Cog):
    """Foothold Checkpoint Management Plugin for DCSServerBot.

    Provides Discord slash commands for managing DCS Foothold campaign checkpoints:
    - /foothold save: Create checkpoint from current campaign state
    - /foothold restore: Restore checkpoint to server
    - /foothold list: List available checkpoints
    - /foothold delete: Delete checkpoint

    Integrates with foothold_checkpoint core library for checkpoint operations.
    """

    def __init__(self, bot: commands.Bot):
        """Initialize the Foothold plugin.

        Args:
            bot: Discord bot instance
        """
        self.bot = bot
        self.log = bot.log if hasattr(bot, 'log') else bot.logger
        self.listener: FootholdEventListener | None = None
        self.config: PluginConfig | None = None
        self.config_dict: dict[str, Any] = {}
        self.campaigns: dict[str, CampaignConfig] = {}
        self.core_config: Config | None = None

    async def cog_load(self) -> None:
        """Called when the cog is loaded.

        Loads plugin configuration, campaigns, and initializes event listener.
        """
        try:
            # Load configuration (bot-specific method would be called here)
            # For development: self.config = self.bot.get_config()
            # For now, we'll initialize with None and log warning
            self.log.warning("Plugin configuration loading not yet implemented")

            # Initialize event listener
            self.listener = FootholdEventListener()

            self.log.info("Foothold plugin loaded successfully")

        except Exception as e:
            self.log.error(f"Failed to load Foothold plugin: {e}")
            raise

    async def cog_unload(self) -> None:
        """Called when the cog is unloaded.

        Cleanup resources and log unload event.
        """
        self.log.info("Foothold plugin unloaded")
        self.listener = None
        self.config = None
        self.campaigns = {}

    def load_config_from_dict(self, config_dict: dict[str, Any]) -> None:
        """Load configuration from dictionary (for bot integration).

        Args:
            config_dict: Configuration dictionary from bot's config system
        """
        self.config = PluginConfig(**config_dict)
        self.config_dict = self.config.to_dict()

        # Load campaigns from campaigns_file
        campaigns_file = Path(config_dict['campaigns_file'])
        self.campaigns = load_campaigns(campaigns_file)

        # Create a minimal Config object for storage functions
        # The plugin doesn't use servers, so servers can be None
        self.core_config = Config(
            servers=None,
            campaigns=self.campaigns,
            campaigns_file=campaigns_file
        )

        self.log.info(f"Loaded configuration with {len(self.campaigns)} campaigns")

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
        if not await check_permission(interaction, self.config_dict, operation):
            allowed_roles = self.config_dict.get('permissions', {}).get(operation, [])
            message = format_permission_denied(operation, allowed_roles)
            await interaction.response.send_message(message, ephemeral=True)
            return False
        return True

    # Discord Command: /foothold save
    @app_commands.command(name="save", description="Save a checkpoint for a campaign")
    @app_commands.describe(
        campaign="Campaign to save",
        name="Optional custom name for the checkpoint",
        comment="Optional comment describing the checkpoint"
    )
    async def save_command(
        self,
        interaction: discord.Interaction,
        campaign: str,
        name: str | None = None,
        comment: str | None = None
    ) -> None:
        """Save a checkpoint for the specified campaign.

        Args:
            interaction: Discord interaction
            campaign: Campaign name to save
            name: Optional custom checkpoint name
            comment: Optional checkpoint comment
        """
        # Check permissions
        if not await self._check_permission(interaction, 'save'):
            return

        # Defer response for long operation
        await interaction.response.defer(thinking=True)

        try:
            # Get campaign config
            if campaign not in self.campaigns:
                await interaction.followup.send(
                    f"❌ Unknown campaign: {campaign}",
                    ephemeral=True
                )
                return

            campaign_config = self.campaigns[campaign]
            checkpoints_dir = Path(self.config_dict['checkpoints_dir'])

            # Plugin mode doesn't have server_name per se, use placeholder
            server_name = "bot"
            source_dir = campaign_config.path

            # Create event hooks for progress updates
            async def on_progress(current: int, total: int) -> None:
                """Update Discord UI with progress."""
                self.log.debug(f"Save progress: {current}/{total}")

            hooks = EventHooks(on_save_progress=on_progress)

            # Execute save
            checkpoint_path = await save_checkpoint(
                campaign_name=campaign,
                server_name=server_name,
                source_dir=source_dir,
                output_dir=checkpoints_dir,
                config=self.core_config,
                name=name,
                comment=comment,
                hooks=hooks
            )

            # Send success response
            embed = discord.Embed(
                title="✅ Checkpoint Saved",
                description=f"Campaign: **{campaign}**",
                color=discord.Color.green()
            )
            embed.add_field(name="Checkpoint", value=checkpoint_path.name)

            if checkpoint_path.exists():
                size_mb = checkpoint_path.stat().st_size / (1024 * 1024)
                embed.add_field(name="Size", value=f"{size_mb:.2f} MB")

            if comment:
                embed.add_field(name="Comment", value=comment, inline=False)

            embed.set_footer(
                text=f"Saved by {interaction.user.name}",
                icon_url=interaction.user.avatar.url if interaction.user.avatar else None
            )
            embed.timestamp = discord.utils.utcnow()

            await interaction.followup.send(embed=embed)

            # Send notification if configured
            if interaction.guild:
                await send_notification(
                    guild=interaction.guild,
                    config=self.config_dict,
                    event_type='save',
                    campaign=campaign,
                    user=interaction.user,
                    checkpoint=checkpoint_path
                )

        except Exception as e:
            self.log.error(f"Failed to save checkpoint: {e}", exc_info=True)

            embed = discord.Embed(
                title="❌ Save Failed",
                description=str(e),
                color=discord.Color.red()
            )
            await interaction.followup.send(embed=embed, ephemeral=True)

            # Send error notification
            if interaction.guild:
                await send_notification(
                    guild=interaction.guild,
                    config=self.config_dict,
                    event_type='error',
                    campaign=campaign,
                    user=interaction.user,
                    error=e
                )

    # Discord Command: /foothold restore
    @app_commands.command(name="restore", description="Restore a checkpoint")
    @app_commands.describe(
        checkpoint="Checkpoint to restore",
        campaign="Campaign to restore to",
        auto_backup="Create automatic backup before restoring (default: True)"
    )
    async def restore_command(
        self,
        interaction: discord.Interaction,
        checkpoint: str,
        campaign: str,
        auto_backup: bool = True
    ) -> None:
        """Restore a checkpoint for the specified campaign.

        Args:
            interaction: Discord interaction
            checkpoint: Checkpoint filename to restore
            campaign: Campaign name to restore to
            auto_backup: Whether to create auto-backup before restore
        """
        # Check permissions
        if not await self._check_permission(interaction, 'restore'):
            return

        # Defer response for long operation
        await interaction.response.defer(thinking=True)

        try:
            # Get campaign config
            if campaign not in self.campaigns:
                await interaction.followup.send(
                    f"❌ Unknown campaign: {campaign}",
                    ephemeral=True
                )
                return

            campaign_config = self.campaigns[campaign]
            checkpoints_dir = Path(self.config_dict['checkpoints_dir'])
            checkpoint_path = checkpoints_dir / checkpoint

            # Determine target directory from campaign config
            target_dir = campaign_config.path
            server_name = "bot"

            # Create event hooks
            async def on_progress(current: int, total: int) -> None:
                """Update Discord UI with progress."""
                self.log.debug(f"Restore progress: {current}/{total}")

            hooks = EventHooks(on_restore_progress=on_progress)

            # Execute restore
            await restore_checkpoint(
                checkpoint_path=checkpoint_path,
              target_dir=target_dir,
                config=self.core_config,
                server_name=server_name,
                auto_backup=auto_backup,
                hooks=hooks
            )

            # Send success response
            embed = discord.Embed(
                title="✅ Checkpoint Restored",
                description=f"Campaign: **{campaign}**",
                color=discord.Color.blue()
            )
            embed.add_field(name="Checkpoint", value=checkpoint)
            if auto_backup:
                embed.add_field(name="Auto-backup", value="✅ Created")

            embed.set_footer(
                text=f"Restored by {interaction.user.name}",
                icon_url=interaction.user.avatar.url if interaction.user.avatar else None
            )
            embed.timestamp = discord.utils.utcnow()

            await interaction.followup.send(embed=embed)

            # Send notification
            if interaction.guild:
                await send_notification(
                    guild=interaction.guild,
                    config=self.config_dict,
                    event_type='restore',
                    campaign=campaign,
                    user=interaction.user,
                    checkpoint=checkpoint_path,
                    auto_backup=str(auto_backup)
                )

        except Exception as e:
            self.log.error(f"Failed to restore checkpoint: {e}", exc_info=True)

            embed = discord.Embed(
                title="❌ Restore Failed",
                description=str(e),
                color=discord.Color.red()
            )
            await interaction.followup.send(embed=embed, ephemeral=True)

            # Send error notification
            if interaction.guild:
                await send_notification(
                    guild=interaction.guild,
                    config=self.config_dict,
                    event_type='error',
                    campaign=campaign,
                    user=interaction.user,
                    error=e
                )

    # Discord Command: /foothold list
    @app_commands.command(name="list", description="List available checkpoints")
    @app_commands.describe(
        campaign="Optional: Filter by campaign",
        show_details="Show detailed file information"
    )
    async def list_command(
        self,
        interaction: discord.Interaction,
        campaign: str | None = None,
        show_details: bool = False
    ) -> None:
        """List available checkpoints.

        Args:
            interaction: Discord interaction
            campaign: Optional campaign filter
            show_details: Whether to show detailed file information
        """
        # Check permissions
        if not await self._check_permission(interaction, 'list'):
            return

        await interaction.response.defer(thinking=True)

        try:
            checkpoints_dir = Path(self.config_dict['checkpoints_dir'])

            # Get checkpoints
            checkpoints_list = await list_checkpoints(
                checkpoint_dir=checkpoints_dir,
                campaign_filter=campaign
            )

            if not checkpoints_list:
                message = "No checkpoints found"
                if campaign:
                    message += f" for campaign '{campaign}'"
                await interaction.followup.send(message, ephemeral=True)
                return

            # Create embed response
            embed = discord.Embed(
                title="📦 Available Checkpoints",
                color=discord.Color.blue()
            )

            if campaign:
                embed.description = f"Campaign: **{campaign}**"

            # Group checkpoints by campaign
            by_campaign: dict[str, list[dict[str, Any]]] = {}
            for cp in checkpoints_list:
                camp = cp['campaign']
                if camp not in by_campaign:
                    by_campaign[camp] = []
                by_campaign[camp].append(cp)

            # Add fields for each campaign
            for camp, cps in sorted(by_campaign.items()):
                lines = []
                for cp in cps[:10]:  # Limit to 10 per campaign to avoid embed size limits
                    line = f"• `{cp['filename']}`"
                    if show_details:
                        size_mb = cp.get('size', 0) / (1024 * 1024)
                        line += f" ({size_mb:.1f} MB)"
                    if cp.get('comment'):
                        line += f" - {cp['comment'][:50]}"
                    lines.append(line)

                if len(cps) > 10:
                    lines.append(f"... and {len(cps) - 10} more")

                embed.add_field(
                    name=f"{camp} ({len(cps)})",
                    value="\n".join(lines),
                    inline=False
                )

            embed.set_footer(text=f"Total: {len(checkpoints_list)} checkpoints")

            await interaction.followup.send(embed=embed)

        except Exception as e:
            self.log.error(f"Failed to list checkpoints: {e}", exc_info=True)

            embed = discord.Embed(
                title="❌ List Failed",
                description=str(e),
                color=discord.Color.red()
            )
            await interaction.followup.send(embed=embed, ephemeral=True)

    # Discord Command: /foothold delete
    @app_commands.command(name="delete", description="Delete a checkpoint")
    @app_commands.describe(
        checkpoint="Checkpoint to delete",
        campaign="Campaign of the checkpoint"
    )
    async def delete_command(
        self,
        interaction: discord.Interaction,
        checkpoint: str,
        campaign: str
    ) -> None:
        """Delete a checkpoint.

        Args:
            interaction: Discord interaction
            checkpoint: Checkpoint filename to delete
            campaign: Campaign name
        """
        # Check permissions
        if not await self._check_permission(interaction, 'delete'):
            return

        await interaction.response.defer(thinking=True)

        try:
            checkpoints_dir = Path(self.config_dict['checkpoints_dir'])
            checkpoint_path = checkpoints_dir / checkpoint

            # Execute delete
            await delete_checkpoint(checkpoint_path=checkpoint_path)

            # Send success response
            embed = discord.Embed(
                title="🗑️ Checkpoint Deleted",
                description=f"Campaign: **{campaign}**",
                color=discord.Color.orange()
            )
            embed.add_field(name="Checkpoint", value=checkpoint)
            embed.add_field(name="⚠️ Warning", value="Deletion is permanent", inline=False)

            embed.set_footer(
                text=f"Deleted by {interaction.user.name}",
                icon_url=interaction.user.avatar.url if interaction.user.avatar else None
            )
            embed.timestamp = discord.utils.utcnow()

            await interaction.followup.send(embed=embed)

            # Send notification
            if interaction.guild:
                await send_notification(
                    guild=interaction.guild,
                    config=self.config_dict,
                    event_type='delete',
                    campaign=campaign,
                    user=interaction.user,
                    checkpoint=checkpoint_path
                )

        except Exception as e:
            self.log.error(f"Failed to delete checkpoint: {e}", exc_info=True)

            embed = discord.Embed(
                title="❌ Delete Failed",
                description=str(e),
                color=discord.Color.red()
            )
            await interaction.followup.send(embed=embed, ephemeral=True)

            # Send error notification
            if interaction.guild:
                await send_notification(
                    guild=interaction.guild,
                    config=self.config_dict,
                    event_type='error',
                    campaign=campaign,
                    user=interaction.user,
                    error=e
                )


async def setup(bot: commands.Bot) -> None:
    """Setup function to register the plugin with the bot.

    Args:
        bot: Discord bot instance
    """
    await bot.add_cog(Foothold(bot))

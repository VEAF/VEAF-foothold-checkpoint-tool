"""Discord notification system for checkpoint events."""

from pathlib import Path
from typing import Any

import discord


async def send_notification(
    guild: discord.Guild,
    config: dict[str, Any],
    event_type: str,
    campaign: str,
    user: discord.User,
    checkpoint: Path | None = None,
    error: Exception | None = None,
    **kwargs: Any
) -> None:
    """Send Discord notification for checkpoint event.
    
    Args:
        guild: Discord guild where event occurred
        config: Plugin configuration with notifications settings
        event_type: Type of event ('save', 'restore', 'delete', 'error')
        campaign: Campaign name
        user: User who triggered the operation
        checkpoint: Checkpoint path (for success events)
        error: Exception (for error events)
        **kwargs: Additional event-specific data
        
    Example:
        >>> await send_notification(
        ...     guild=interaction.guild,
        ...     config=config,
        ...     event_type='save',
        ...     campaign='afghanistan',
        ...     user=interaction.user,
        ...     checkpoint=Path('afghanistan_2026-02-16.zip')
        ... )
    """
    # Check if notifications are enabled for this event type
    notifications = config.get('notifications', {})
    if not notifications.get(f'on_{event_type}', True):
        return
    
    # Find notification channel
    channel_name = notifications.get('channel', 'mission-logs')
    channel = discord.utils.get(guild.channels, name=channel_name)
    
    if not channel:
        # Log warning but don't fail operation
        print(f"Warning: Notification channel '{channel_name}' not found")
        return
    
    # Create embed based on event type
    embed = create_embed(event_type, campaign, user, checkpoint, error, **kwargs)
    
    try:
        await channel.send(embed=embed)
    except discord.errors.Forbidden:
        print(f"Warning: Missing permissions to send to channel '{channel_name}'")
    except Exception as e:
        print(f"Warning: Failed to send notification: {e}")


def create_embed(
    event_type: str,
    campaign: str,
    user: discord.User,
    checkpoint: Path | None,
    error: Exception | None,
    **kwargs: Any
) -> discord.Embed:
    """Create Discord embed for checkpoint event.

    Args:
        event_type: Type of event ('save', 'restore', 'delete', 'error')
        campaign: Campaign name
        user: User who triggered the operation
        checkpoint: Checkpoint path (for success events)
        error: Exception (for error events)
        **kwargs: Additional event-specific data

    Returns:
        Discord Embed object with appropriate styling and content
    """
    if event_type == 'save':
        embed = discord.Embed(
            title="📦 Checkpoint Saved",
            description=f"Campaign: **{campaign}**",
            color=discord.Color.green()
        )
        if checkpoint:
            embed.add_field(name="Checkpoint", value=checkpoint.name)
            if checkpoint.exists():
                size_mb = checkpoint.stat().st_size / (1024 * 1024)
                embed.add_field(name="Size", value=f"{size_mb:.2f} MB")

    elif event_type == 'restore':
        embed = discord.Embed(
            title="♻️ Checkpoint Restored",
            description=f"Campaign: **{campaign}**",
            color=discord.Color.blue()
        )
        if checkpoint:
            embed.add_field(name="Checkpoint", value=checkpoint.name)
        if 'auto_backup' in kwargs:
            embed.add_field(name="Auto-backup", value=kwargs['auto_backup'])

    elif event_type == 'delete':
        embed = discord.Embed(
            title="🗑️ Checkpoint Deleted",
            description=f"Campaign: **{campaign}**",
            color=discord.Color.orange()
        )
        if checkpoint:
            embed.add_field(name="Checkpoint", value=checkpoint.name)
        embed.add_field(name="⚠️ Warning", value="Deletion is permanent", inline=False)

    elif event_type == 'error':
        embed = discord.Embed(
            title="❌ Operation Failed",
            description=f"Campaign: **{campaign}**",
            color=discord.Color.red()
        )
        if error:
            embed.add_field(name="Error", value=str(error), inline=False)

    else:
        embed = discord.Embed(
            title="Checkpoint Event",
            description=f"Campaign: **{campaign}**",
            color=discord.Color.greyple()
        )

    # Add footer with user attribution
    embed.set_footer(
        text=f"By {user.name}",
        icon_url=user.avatar.url if user.avatar else discord.Embed.Empty
    )
    embed.timestamp = discord.utils.utcnow()

    return embed

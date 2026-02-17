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
    **kwargs: Any,
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
    import logging

    logger = logging.getLogger("foothold-checkpoint")

    logger.info(
        f"send_notification called: event_type={event_type}, campaign={campaign}, "
        f"user={user.name}, guild={guild.name}, checkpoint={checkpoint}"
    )

    # Check if notifications are enabled for this event type
    notifications = config.get("notifications", {})
    logger.debug(f"Notifications config: {notifications}")

    event_key = f"on_{event_type}"
    event_enabled = notifications.get(event_key, True)
    logger.info(f"Event '{event_type}' notification enabled: {event_enabled} (key: {event_key})")

    if not event_enabled:
        logger.info(f"Notification skipped: event type '{event_type}' is disabled in config")
        return

    # Find notification channel (supports both ID and name)
    channel_config = notifications.get("channel")
    logger.info(f"Channel config: {channel_config} (type: {type(channel_config).__name__})")

    if not channel_config:
        logger.warning("Notification skipped: no channel configured in notifications.channel")
        return  # No channel configured

    # Try to parse as integer channel ID first (preferred method)
    channel = None
    if isinstance(channel_config, int):
        logger.info(f"Channel config is integer: {channel_config}")
        channel = guild.get_channel(channel_config)
        logger.info(f"guild.get_channel({channel_config}) returned: {channel}")
    elif isinstance(channel_config, str):
        logger.info(f"Channel config is string: '{channel_config}'")
        # Try parsing string as integer ID
        try:
            channel_id = int(channel_config)
            logger.info(f"Parsed as integer ID: {channel_id}")
            channel = guild.get_channel(channel_id)
            logger.info(f"guild.get_channel({channel_id}) returned: {channel}")
        except ValueError:
            # Fall back to name-based search
            logger.info(f"Not an integer, searching by name: '{channel_config}'")
            channel = discord.utils.get(guild.channels, name=channel_config)
            logger.info(
                f"discord.utils.get(guild.channels, name='{channel_config}') returned: {channel}"
            )

    if not channel:
        # Log warning but don't fail operation
        logger.warning(
            f"Notification channel '{channel_config}' not found in guild '{guild.name}'. "
            f"Available channels (first 20): {[(ch.id, ch.name, type(ch).__name__) for ch in guild.channels[:20]]}"
        )
        return

    logger.info(f"Found channel: {channel.name} (ID: {channel.id}, Type: {type(channel).__name__})")

    # Create embed based on event type
    embed = create_embed(event_type, campaign, user, checkpoint, error, **kwargs)
    logger.info(f"Created embed: title='{embed.title}', color={embed.color}")

    try:
        logger.info(
            f"Attempting to send notification to channel {channel.name} (ID: {channel.id})..."
        )
        message = await channel.send(embed=embed)
        logger.info(f"Notification sent successfully! Message ID: {message.id}")
    except discord.errors.Forbidden as e:
        logger.error(
            f"Missing permissions to send notification to channel '{channel_config}' "
            f"(ID: {channel.id}, Name: {channel.name}). Check bot permissions in that channel. Error: {e}"
        )
    except Exception as e:
        logger.error(f"Failed to send notification: {e}", exc_info=True)


def create_embed(
    event_type: str,
    campaign: str,
    user: discord.User,
    checkpoint: Path | None,
    error: Exception | None,
    **kwargs: Any,
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
    if event_type == "save":
        embed = discord.Embed(
            title="📦 Checkpoint Saved",
            description=f"Campaign: **{campaign}**",
            color=discord.Color.green(),
        )
        if checkpoint:
            embed.add_field(name="Checkpoint", value=checkpoint.name)
            if checkpoint.exists():
                size_mb = checkpoint.stat().st_size / (1024 * 1024)
                embed.add_field(name="Size", value=f"{size_mb:.2f} MB")

    elif event_type == "restore":
        embed = discord.Embed(
            title="♻️ Checkpoint Restored",
            description=f"Campaign: **{campaign}**",
            color=discord.Color.blue(),
        )
        if checkpoint:
            embed.add_field(name="Checkpoint", value=checkpoint.name)
        if "auto_backup" in kwargs:
            embed.add_field(name="Auto-backup", value=kwargs["auto_backup"])

    elif event_type == "delete":
        embed = discord.Embed(
            title="🗑️ Checkpoint Deleted",
            description=f"Campaign: **{campaign}**",
            color=discord.Color.orange(),
        )
        if checkpoint:
            embed.add_field(name="Checkpoint", value=checkpoint.name)
        embed.add_field(name="⚠️ Warning", value="Deletion is permanent", inline=False)

    elif event_type == "error":
        embed = discord.Embed(
            title="❌ Operation Failed",
            description=f"Campaign: **{campaign}**",
            color=discord.Color.red(),
        )
        if error:
            embed.add_field(name="Error", value=str(error), inline=False)

    else:
        embed = discord.Embed(
            title="Checkpoint Event",
            description=f"Campaign: **{campaign}**",
            color=discord.Color.greyple(),
        )

    # Add footer with user attribution
    embed.set_footer(
        text=f"By {user.name}", icon_url=user.avatar.url if user.avatar else discord.Embed.Empty
    )
    embed.timestamp = discord.utils.utcnow()

    return embed

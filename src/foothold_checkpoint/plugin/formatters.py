"""Rich formatting functions for Discord embeds."""

from datetime import datetime
from typing import Any

import discord


def format_checkpoint_list_embed(
    checkpoints: list[dict[str, Any]],
    campaign_filter: str | None = None,
    page: int = 1,
    per_page: int = 5,  # Reduced from 10 for Discord embed size limits
) -> discord.Embed:
    """Format checkpoint list as a rich Discord embed with readable two-line format.

    Creates a clean display with filename on first line and details on second line.
    Uses horizontal separators between checkpoints for better readability.

    Args:
        checkpoints: List of checkpoint metadata dicts
        campaign_filter: Optional campaign name filter for title
        page: Current page number (1-indexed)
        per_page: Number of checkpoints per page (reduced to 5 for embed limits)

    Returns:
        Discord embed with formatted checkpoint list
    """
    # Calculate pagination
    total = len(checkpoints)
    start = (page - 1) * per_page
    end = min(start + per_page, total)
    page_checkpoints = checkpoints[start:end]

    # Create embed
    title = f"📦 Checkpoints for {campaign_filter}" if campaign_filter else "📦 All Checkpoints"

    embed = discord.Embed(
        title=title,
        description=f"Showing {start + 1}-{end} of {total} checkpoint(s)",
        color=discord.Color.blue(),
        timestamp=datetime.utcnow(),
    )

    # Group by campaign for cleaner display
    campaigns: dict[str, list[dict[str, Any]]] = {}
    for cp in page_checkpoints:
        campaign = cp["campaign"]
        if campaign not in campaigns:
            campaigns[campaign] = []
        campaigns[campaign].append(cp)

    # Add fields for each campaign with two-line format
    for campaign, cps in campaigns.items():
        # Build readable two-line format for this campaign's checkpoints
        lines = ["```"]

        for idx, cp in enumerate(cps):
            # Add separator between checkpoints (except before first)
            if idx > 0:
                lines.append("─" * 45)

            # Line 1: Filename
            filename = cp["filename"]
            if len(filename) > 43:
                filename = filename[:40] + "..."
            lines.append(filename)

            # Line 2: Date, Time, Size (aligned columns)
            timestamp_str = cp["timestamp"]
            if "." in timestamp_str:
                timestamp_str = timestamp_str.split(".")[0]
            # "2024-02-14T10:30:00" -> "02-14" and "10:30"
            date_part = timestamp_str[5:10] if len(timestamp_str) > 10 else ""
            time_part = timestamp_str[11:16] if len(timestamp_str) > 16 else ""

            size_str = cp["size_human"]

            # Format: "DATE      TIME     SIZE"
            details_line = f"{date_part:<10}{time_part:<9}{size_str:>8}"
            lines.append(details_line)

        lines.append("```")

        field_content = "\n".join(lines)

        # Safety check: Discord field value max is 1024 chars
        if len(field_content) > 1000:
            # Fallback: truncate and add warning
            lines = lines[: min(len(lines), 15)]
            lines.append("... (list truncated)")
            lines.append("```")
            field_content = "\n".join(lines)

        # Add field for this campaign
        embed.add_field(
            name=f"📁 {campaign} ({len(cps)} checkpoint{'' if len(cps) == 1 else 's'})",
            value=field_content,
            inline=False,
        )

    # Add footer with pagination info
    if total > per_page:
        total_pages = (total + per_page - 1) // per_page
        embed.set_footer(text=f"Page {page}/{total_pages} • Use page parameter to see more")
    else:
        embed.set_footer(text="Tip: Use show_details:true to see full checkpoint info")

    return embed


def format_checkpoint_details_embed(checkpoint: dict[str, Any]) -> discord.Embed:
    """Format detailed checkpoint information as an embed.

    Args:
        checkpoint: Checkpoint metadata dict

    Returns:
        Discord embed with checkpoint details
    """
    # Parse timestamp
    timestamp_str = checkpoint["timestamp"]
    if "." in timestamp_str:
        timestamp_str = timestamp_str.split(".")[0]

    # Build description with fixed-width padding to ensure consistent embed width
    # Use invisible braille character repeated to force minimum width
    description = checkpoint.get("comment") or "_No description_"
    # Add invisible padding line to force consistent width (approximately 80 chars wide)
    width_padding = "⠀" * 80
    description_with_padding = f"{description}\n{width_padding}"

    # Create embed
    embed = discord.Embed(
        title=f"📦 {checkpoint.get('name') or checkpoint['filename']}",
        description=description_with_padding,
        color=discord.Color.green(),
        timestamp=datetime.fromisoformat(timestamp_str),
    )

    # Add fields
    embed.add_field(name="📁 Campaign", value=checkpoint["campaign"], inline=True)
    embed.add_field(name="🖥️ Server", value=checkpoint["server"], inline=True)
    embed.add_field(name="💾 Size", value=checkpoint["size_human"], inline=True)
    embed.add_field(name="📄 Filename", value=f"`{checkpoint['filename']}`", inline=False)

    # Add file list if available - always include this field for consistent embed height
    if "files" in checkpoint and checkpoint["files"]:
        # Limit to 10 files for consistent display
        files_to_show = checkpoint["files"][:10]
        files_text = "\n".join([f"• `{f}`" for f in files_to_show])
        if len(checkpoint["files"]) > 10:
            files_text += f"\n_...and {len(checkpoint['files']) - 10} more_"
        # Pad with empty lines to ensure consistent height (10 lines total)
        line_count = len(files_to_show)
        if line_count < 10 and len(checkpoint["files"]) <= 10:
            files_text += "\n⠀" * (10 - line_count)  # Invisible character for spacing
    else:
        # No files - show placeholder with padding to maintain height
        files_text = "_No files listed_\n⠀" * 9  # 10 lines total

    embed.add_field(name="📑 Files", value=files_text, inline=False)

    embed.set_footer(text="Checkpoint created")

    return embed


def format_save_success_embed(
    checkpoint_filename: str,
    campaign: str,
    server: str,
    size: str,
    name: str | None = None,
    comment: str | None = None,
) -> discord.Embed:
    """Format successful save operation as an embed.

    Args:
        checkpoint_filename: Name of created checkpoint file
        campaign: Campaign name
        server: Server name
        size: Human-readable size string
        name: Optional checkpoint name
        comment: Optional checkpoint comment

    Returns:
        Discord embed for save success
    """
    embed = discord.Embed(
        title="✅ Checkpoint Saved",
        description=f"Checkpoint created for **{campaign}**",
        color=discord.Color.green(),
        timestamp=datetime.utcnow(),
    )

    embed.add_field(name="📄 Filename", value=f"`{checkpoint_filename}`", inline=False)
    embed.add_field(name="🖥️ Server", value=server, inline=True)
    embed.add_field(name="💾 Size", value=size, inline=True)

    if name:
        embed.add_field(name="🏷️ Name", value=name, inline=False)
    if comment:
        embed.add_field(name="💬 Comment", value=comment, inline=False)

    return embed


def format_restore_success_embed(
    checkpoint_filename: str,
    campaign: str,
    server: str,
    backup_created: bool,
    backup_filename: str | None = None,
) -> discord.Embed:
    """Format successful restore operation as an embed.

    Args:
        checkpoint_filename: Name of restored checkpoint file
        campaign: Campaign name
        server: Server name
        backup_created: Whether auto-backup was created
        backup_filename: Name of backup file if created

    Returns:
        Discord embed for restore success
    """
    embed = discord.Embed(
        title="✅ Checkpoint Restored",
        description=f"Checkpoint restored to **{campaign}**",
        color=discord.Color.blue(),
        timestamp=datetime.utcnow(),
    )

    embed.add_field(name="📄 Restored From", value=f"`{checkpoint_filename}`", inline=False)
    embed.add_field(name="🖥️ Server", value=server, inline=True)

    if backup_created and backup_filename:
        embed.add_field(name="💾 Auto-Backup", value=f"Created: `{backup_filename}`", inline=False)

    embed.set_footer(text="⚠️ Server restart may be required for changes to take effect")

    return embed


def format_delete_success_embed(checkpoint_filename: str, campaign: str) -> discord.Embed:
    """Format successful delete operation as an embed.

    Args:
        checkpoint_filename: Name of deleted checkpoint file
        campaign: Campaign name

    Returns:
        Discord embed for delete success
    """
    embed = discord.Embed(
        title="🗑️ Checkpoint Deleted",
        description=f"Checkpoint removed from **{campaign}**",
        color=discord.Color.orange(),
        timestamp=datetime.utcnow(),
    )

    embed.add_field(name="📄 Deleted", value=f"`{checkpoint_filename}`", inline=False)
    embed.set_footer(text="⚠️ This action cannot be undone")

    return embed


def format_error_embed(operation: str, error: Exception) -> discord.Embed:
    """Format error message as an embed.

    Args:
        operation: Operation that failed (save, restore, list, delete)
        error: Exception that occurred

    Returns:
        Discord embed for error message
    """
    embed = discord.Embed(
        title=f"❌ {operation.capitalize()} Failed",
        description=str(error),
        color=discord.Color.red(),
        timestamp=datetime.utcnow(),
    )

    # Add helpful hints based on error type
    if "not found" in str(error).lower():
        embed.set_footer(text="💡 Tip: Use /foothold-checkpoint list to see available checkpoints")
    elif "permission" in str(error).lower():
        embed.set_footer(text="💡 Tip: Check file permissions and server ownership")

    return embed

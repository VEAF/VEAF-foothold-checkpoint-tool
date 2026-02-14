"""High-level checkpoint storage operations.

This module provides functions for saving, restoring, listing, and deleting
Foothold campaign checkpoints with integrity verification.
"""

from collections.abc import Callable
from datetime import datetime
from pathlib import Path

from foothold_checkpoint.core.campaign import group_campaign_files
from foothold_checkpoint.core.checkpoint import create_checkpoint


def save_checkpoint(
    campaign_name: str,
    server_name: str,
    source_dir: str | Path,
    output_dir: str | Path,
    created_at: datetime | None = None,
    name: str | None = None,
    comment: str | None = None,
    progress_callback: Callable[[str, int, int], None] | None = None,
) -> Path:
    """Save a checkpoint for a single campaign.

    Scans the source directory for campaign files matching the campaign name,
    includes Foothold_Ranks.lua if present, and creates a timestamped ZIP
    checkpoint in the output directory with metadata and checksums.

    Args:
        campaign_name: Name of the campaign (normalized, lowercase). Used to
            match campaign files (e.g., "afghanistan" matches
            "foothold_afghanistan*.lua/csv").
        server_name: Name of the server where checkpoint is created. Stored
            in metadata for reference.
        source_dir: Path to the directory containing campaign files (typically
            server Saves directory).
        output_dir: Path to the directory where checkpoint ZIP will be saved.
        created_at: Optional timestamp for the checkpoint. If None, uses current
            UTC time. Must be timezone-aware (UTC recommended).
        name: Optional user-provided name for the checkpoint
            (e.g., "Before Mission 5").
        comment: Optional user-provided comment/description for the checkpoint.
        progress_callback: Optional callback function called during checkpoint
            creation. Called as: callback(message: str, current: int, total: int).
            Example: callback("Computing checksums", 1, 3)

    Returns:
        Path to the created checkpoint ZIP file.

    Raises:
        ValueError: If no campaign files are found for the specified campaign name.
        FileNotFoundError: If source_dir does not exist.
        PermissionError: If source_dir is not readable or output_dir is not writable.
        OSError: If checkpoint creation fails (disk full, etc.).

    Examples:
        >>> checkpoint = save_checkpoint(
        ...     campaign_name="afghanistan",
        ...     server_name="production-1",
        ...     source_dir=Path("C:/DCS/Server/Missions/Saves"),
        ...     output_dir=Path("C:/checkpoints"),
        ...     name="Before major update"
        ... )
        >>> print(checkpoint.name)
        afghanistan_2024-02-14_10-30-00.zip
    """
    source_dir = Path(source_dir)
    output_dir = Path(output_dir)

    # Validate source directory exists and is accessible
    if not source_dir.exists():
        raise FileNotFoundError(
            f"Source directory '{source_dir}' does not exist. "
            f"Please check the server path in your configuration."
        )

    if not source_dir.is_dir():
        raise NotADirectoryError(
            f"Source path '{source_dir}' is not a directory. "
            f"Expected a directory containing campaign files."
        )

    # Test readability by attempting to list directory
    try:
        list(source_dir.iterdir())
    except PermissionError as e:
        raise PermissionError(
            f"Source directory '{source_dir}' is not readable. "
            f"Check file system permissions."
        ) from e

    # Create output directory if it doesn't exist
    if output_dir.exists() and not output_dir.is_dir():
        raise NotADirectoryError(
            f"Output path '{output_dir}' exists but is not a directory. "
            f"Please specify a directory path for checkpoint storage."
        )

    output_dir.mkdir(parents=True, exist_ok=True)

    # Find all files in source directory
    all_files = list(source_dir.glob("*"))
    filenames = [f.name for f in all_files if f.is_file()]

    # Group files by campaign and find matching files
    grouped = group_campaign_files(filenames)

    # Find campaign files (case-insensitive match)
    campaign_files_names = None
    for camp_name, files in grouped.items():
        if camp_name.lower() == campaign_name.lower():
            campaign_files_names = files
            break

    if not campaign_files_names:
        raise ValueError(
            f"No campaign files found for campaign '{campaign_name}' in {source_dir}. "
            f"Available campaigns: {', '.join(grouped.keys()) if grouped else 'none'}"
        )

    # Build full paths for campaign files
    campaign_files = [source_dir / fname for fname in campaign_files_names]

    # Add Foothold_Ranks.lua if it exists
    ranks_file = source_dir / "Foothold_Ranks.lua"
    if ranks_file.exists():
        campaign_files.append(ranks_file)

    # Create the checkpoint using low-level function
    checkpoint_path = create_checkpoint(
        campaign_name=campaign_name,
        server_name=server_name,
        campaign_files=campaign_files,
        output_dir=output_dir,
        created_at=created_at,
        name=name,
        comment=comment,
        progress_callback=progress_callback,
    )

    return checkpoint_path


def save_all_campaigns(
    server_name: str,
    source_dir: str | Path,
    output_dir: str | Path,
    created_at: datetime | None = None,
    name: str | None = None,
    comment: str | None = None,
    progress_callback: Callable[[str, int, int], None] | None = None,
    continue_on_error: bool = True,
) -> dict[str, Path]:
    """Save checkpoints for all detected campaigns in source directory.

    Scans the source directory for campaign files, detects all campaigns,
    and creates a separate checkpoint for each one. If continue_on_error is True,
    failures on individual campaigns do not stop processing of other campaigns.

    Args:
        server_name: Name of the server where checkpoints are created.
        source_dir: Path to the directory containing campaign files.
        output_dir: Path to the directory where checkpoint ZIPs will be saved.
        created_at: Optional timestamp for all checkpoints. If None, uses current
            UTC time. All checkpoints will have the same timestamp.
        name: Optional user-provided name applied to all checkpoints.
        comment: Optional user-provided comment applied to all checkpoints.
        progress_callback: Optional callback for progress tracking.
            Called as: callback(message: str, current: int, total: int).
        continue_on_error: If True, continue saving other campaigns when one fails.
            If False, raise error immediately on first failure.

    Returns:
        Dictionary mapping campaign names (lowercase, normalized) to their
        checkpoint file Paths. Failed campaigns are omitted from the results.

    Raises:
        FileNotFoundError: If source_dir does not exist.
        PermissionError: If source_dir is not readable or output_dir not writable.
        Exception: If continue_on_error=False and any campaign save fails.

    Examples:
        >>> results = save_all_campaigns(
        ...     server_name="production-1",
        ...     source_dir=Path("C:/DCS/Server/Missions/Saves"),
        ...     output_dir=Path("C:/checkpoints"),
        ...     name="Daily backup"
        ... )
        >>> for campaign, path in results.items():
        ...     print(f"{campaign}: {path.name}")
        afghanistan: afghanistan_2024-02-14_10-30-00.zip
        syria: syria_2024-02-14_10-30-00.zip
    """
    source_dir = Path(source_dir)
    output_dir = Path(output_dir)

    # Find all files in source directory
    all_files = list(source_dir.glob("*"))
    filenames = [f.name for f in all_files if f.is_file()]

    # Group files by campaign
    grouped = group_campaign_files(filenames)

    if not grouped:
        return {}

    # Create checkpoints for each campaign
    results: dict[str, Path] = {}
    total_campaigns = len(grouped)

    for idx, (campaign_name, _) in enumerate(grouped.items(), start=1):
        try:
            if progress_callback:
                progress_callback(
                    f"Saving campaign {idx}/{total_campaigns}: {campaign_name}",
                    idx,
                    total_campaigns,
                )

            checkpoint_path = save_checkpoint(
                campaign_name=campaign_name,
                server_name=server_name,
                source_dir=source_dir,
                output_dir=output_dir,
                created_at=created_at,
                name=name,
                comment=comment,
                progress_callback=progress_callback,
            )

            results[campaign_name] = checkpoint_path

        except Exception:
            if not continue_on_error:
                raise
            # Log error but continue (in production, would use proper logging)
            # For now, silently skip failed campaigns

    return results


"""High-level checkpoint storage operations.

This module provides functions for saving, restoring, listing, and deleting
Foothold campaign checkpoints with integrity verification.
"""

from collections.abc import Callable
from datetime import datetime, timezone
from pathlib import Path
from typing import TYPE_CHECKING, Any, cast

from foothold_checkpoint.core.campaign import detect_campaigns
from foothold_checkpoint.core.checkpoint import create_checkpoint

if TYPE_CHECKING:
    from foothold_checkpoint.core.config import Config
    from foothold_checkpoint.core.events import EventHooks


async def save_checkpoint(
    campaign_name: str,
    server_name: str,
    source_dir: str | Path,
    output_dir: str | Path,
    config: "Config",
    created_at: datetime | None = None,
    name: str | None = None,
    comment: str | None = None,
    progress_callback: Callable[[str, int, int], None] | None = None,
    hooks: "EventHooks | None" = None,
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
        config: Configuration object containing campaign definitions.
        created_at: Optional timestamp for the checkpoint. If None, uses current
            UTC time. Must be timezone-aware (UTC recommended).
        name: Optional user-provided name for the checkpoint
            (e.g., "Before Mission 5").
        comment: Optional user-provided comment/description for the checkpoint.
        progress_callback: Optional callback function called during checkpoint
            creation. Called as: callback(message: str, current: int, total: int).
            Example: callback("Computing checksums", 1, 3)
        hooks: Optional event hooks for operation notifications. Used by plugin
            for Discord notifications. Set to None for CLI mode.

    Returns:
        Path to the created checkpoint ZIP file.

    Raises:
        ValueError: If no campaign files are found for the specified campaign name.
        FileNotFoundError: If source_dir does not exist.
        PermissionError: If source_dir is not readable or output_dir is not writable.
        OSError: If checkpoint creation fails (disk full, etc.).

    Examples:
        >>> # CLI mode (no hooks)
        >>> checkpoint = await save_checkpoint(
        ...     campaign_name="afghanistan",
        ...     server_name="production-1",
        ...     source_dir=Path("C:/DCS/Server/Missions/Saves"),
        ...     output_dir=Path("C:/checkpoints"),
        ...     config=config,
        ...     name="Before major update"
        ... )

        >>> # Plugin mode (with Discord hooks)
        >>> checkpoint = await save_checkpoint(
        ...     campaign_name="afghanistan",
        ...     server_name="production-1",
        ...     source_dir=Path("C:/DCS/Server/Missions/Saves"),
        ...     output_dir=Path("C:/checkpoints"),
        ...     config=config,
        ...     hooks=discord_hooks,
        ... )
    """
    from foothold_checkpoint.core.events import safe_invoke_hook

    try:
        # Trigger on_save_start hook
        if hooks:
            await safe_invoke_hook(hooks.on_save_start, campaign_name, hook_name="on_save_start")

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
        grouped = detect_campaigns(filenames, config)

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

        # Wrap progress callback to also trigger on_save_progress hook
        def combined_progress_callback(message: str, current: int, total: int) -> None:
            # Call original callback if provided
            if progress_callback:
                progress_callback(message, current, total)

            # Trigger on_save_progress hook (sync wrapper for async hook)
            if hooks and hooks.on_save_progress:
                import asyncio

                asyncio.create_task(
                    safe_invoke_hook(
                        hooks.on_save_progress, current, total, hook_name="on_save_progress"
                    )
                )

        # Create the checkpoint using low-level function
        checkpoint_path = create_checkpoint(
            campaign_name=campaign_name,
            server_name=server_name,
            campaign_files=campaign_files,
            output_dir=output_dir,
            created_at=created_at,
            name=name,
            comment=comment,
            progress_callback=combined_progress_callback,
        )

        # Trigger on_save_complete hook
        if hooks:
            await safe_invoke_hook(
                hooks.on_save_complete, checkpoint_path, hook_name="on_save_complete"
            )

        return checkpoint_path

    except Exception as e:
        # Trigger on_error hook
        if hooks:
            await safe_invoke_hook(hooks.on_error, e, hook_name="on_error")
        raise


async def save_all_campaigns(
    server_name: str,
    source_dir: str | Path,
    output_dir: str | Path,
    config: "Config",
    created_at: datetime | None = None,
    name: str | None = None,
    comment: str | None = None,
    progress_callback: Callable[[str, int, int], None] | None = None,
    hooks: "EventHooks | None" = None,
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
        config: Configuration object containing campaign definitions.
        created_at: Optional timestamp for all checkpoints. If None, uses current
            UTC time. All checkpoints will have the same timestamp.
        name: Optional user-provided name applied to all checkpoints.
        comment: Optional user-provided comment applied to all checkpoints.
        progress_callback: Optional callback for progress tracking.
            Called as: callback(message: str, current: int, total: int).
        hooks: Optional event hooks for operation notifications.
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
        >>> results = await save_all_campaigns(
        ...     server_name="production-1",
        ...     source_dir=Path("C:/DCS/Server/Missions/Saves"),
        ...     output_dir=Path("C:/checkpoints"),
        ...     config=config,
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
    grouped = detect_campaigns(filenames, config)

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

            checkpoint_path = await save_checkpoint(
                campaign_name=campaign_name,
                server_name=server_name,
                source_dir=source_dir,
                output_dir=output_dir,
                config=config,
                created_at=created_at,
                name=name,
                comment=comment,
                progress_callback=progress_callback,
                hooks=hooks,
            )

            results[campaign_name] = checkpoint_path

        except Exception:
            if not continue_on_error:
                raise
            # Log error but continue (in production, would use proper logging)
            # For now, silently skip failed campaigns

    return results


def check_restore_conflicts(
    checkpoint_path: str | Path,
    target_dir: str | Path,
    restore_ranks: bool = False,
) -> list[str]:
    """Check which files would be overwritten during restoration.

    Args:
        checkpoint_path: Path to the checkpoint ZIP file.
        target_dir: Path to the directory where files would be extracted.
        restore_ranks: If True, include Foothold_Ranks.lua in check.

    Returns:
        List of filenames that already exist and would be overwritten.

    Raises:
        FileNotFoundError: If checkpoint_path or target_dir doesn't exist.
        ValueError: If checkpoint is not a valid ZIP or metadata is missing.
    """
    import zipfile

    checkpoint_path = Path(checkpoint_path)
    target_dir = Path(target_dir)

    # Validate checkpoint file exists
    if not checkpoint_path.exists():
        raise FileNotFoundError("Checkpoint file not found")

    # Validate checkpoint is a valid ZIP
    if not zipfile.is_zipfile(checkpoint_path):
        raise ValueError("Invalid checkpoint file (not a valid ZIP archive)")

    # Validate target directory exists
    if not target_dir.exists():
        raise FileNotFoundError("Target directory does not exist")

    # Open ZIP and get file list
    with zipfile.ZipFile(checkpoint_path, "r") as zf:
        # Get list of files that would be restored
        all_files_in_zip = [
            name for name in zf.namelist() if name != "metadata.json" and not name.endswith("/")
        ]

        # Filter out Foothold_Ranks.lua if not requested
        files_to_restore = []
        for filename in all_files_in_zip:
            if filename == "Foothold_Ranks.lua" and not restore_ranks:
                continue
            files_to_restore.append(filename)

        # Check which files already exist
        existing_files = []
        for filename in files_to_restore:
            target_file = target_dir / filename
            if target_file.exists():
                existing_files.append(filename)

        return existing_files


async def create_auto_backup(
    checkpoint_path: Path,
    target_dir: Path,
    server_name: str,
    checkpoints_dir: Path,
    config: "Config",
    progress_callback: Callable[[str, int, int], None] | None = None,
    hooks: "EventHooks | None" = None,
) -> Path | None:
    """Create an automatic backup before restoring a checkpoint.

    Creates a timestamped checkpoint of the current state before performing
    a restore operation. This provides a safety net to revert changes if needed.

    Args:
        checkpoint_path: Path to the checkpoint that will be restored (used to extract campaign name).
        target_dir: Directory containing current campaign files to backup.
        server_name: Name of the server (used in metadata).
        checkpoints_dir: Directory where the auto-backup checkpoint will be saved.
        config: Configuration object containing campaign definitions.
        progress_callback: Optional callback for progress tracking.
        hooks: Optional event hooks for operation notifications.

    Returns:
        Path to the created auto-backup checkpoint, or None if backup failed.

    Raises:
        ValueError: If checkpoint metadata is invalid or campaign files not found.
        OSError: If backup creation fails.

    Example:
        >>> backup = await create_auto_backup(
        ...     checkpoint_path=Path("checkpoints/ca_20260215.zip"),
        ...     target_dir=Path("C:/DCS/Server/Missions/Saves"),
        ...     server_name="foothold2",
        ...     checkpoints_dir=Path("C:/checkpoints"),
        ...     config=config
        ... )
    """
    import json
    import zipfile

    # Read metadata from the checkpoint to get campaign name
    try:
        with zipfile.ZipFile(checkpoint_path, "r") as zf:
            if "metadata.json" not in zf.namelist():
                raise ValueError("Invalid checkpoint (missing metadata)")

            metadata_json = zf.read("metadata.json").decode("utf-8")
            metadata = json.loads(metadata_json)
            campaign_name = metadata.get("campaign_name")

            if not campaign_name:
                raise ValueError("Campaign name not found in checkpoint metadata")

    except (zipfile.BadZipFile, json.JSONDecodeError, KeyError) as e:
        raise ValueError(f"Failed to read checkpoint metadata: {e}") from e

    # Generate auto-backup name with UTC timestamp
    timestamp = datetime.now(timezone.utc)
    backup_name = f"auto-backup-{timestamp.strftime('%Y%m%d-%H%M%S')}"

    # Generate descriptive comment
    backup_comment = f"Automatic backup before restoring {checkpoint_path.stem}"

    # Create the backup checkpoint
    try:
        backup_path = await save_checkpoint(
            campaign_name=campaign_name,
            server_name=server_name,
            source_dir=target_dir,
            output_dir=checkpoints_dir,
            config=config,
            created_at=timestamp,
            name=backup_name,
            comment=backup_comment,
            progress_callback=progress_callback,
            hooks=hooks,
        )
        return backup_path

    except ValueError as e:
        # No campaign files found - this is OK, nothing to backup
        if "No campaign files found" in str(e):
            return None
        raise


def _get_canonical_filename(filename: str, campaign_name: str, config: "Config") -> str:
    """Get canonical (current) filename for a file that may have evolved names.

    When a campaign's files have been renamed over time, the config lists
    multiple accepted names for the same file (old and new). This function
    returns the first name in the list (the canonical/current name) if the
    given filename matches any name in the list.

    Args:
        filename: Original filename from checkpoint (may be old name)
        campaign_name: Campaign ID to look up in config
        config: Configuration object with campaign definitions

    Returns:
        Canonical filename (first in list) if found, otherwise original filename

    Examples:
        >>> # Config has: persistence.files = ["new.lua", "old.lua"]
        >>> _get_canonical_filename("old.lua", "campaign", config)
        "new.lua"  # Returns canonical name
        >>> _get_canonical_filename("new.lua", "campaign", config)
        "new.lua"  # Already canonical
        >>> _get_canonical_filename("unknown.lua", "campaign", config)
        "unknown.lua"  # Not in config, return as-is
    """
    # Check if campaigns dict is available and campaign exists in config
    if config.campaigns is None or campaign_name not in config.campaigns:
        return filename

    campaign = config.campaigns[campaign_name]

    # Check each file type list
    for file_type_name in ["persistence", "ctld_save", "ctld_farps", "storage"]:
        file_type = getattr(campaign.files, file_type_name)
        if filename in file_type.files and file_type.files:
            # Return first name (canonical/current)
            return str(file_type.files[0])

    # File not found in any list - return original name
    return filename


async def restore_checkpoint(
    checkpoint_path: str | Path,
    target_dir: str | Path,
    restore_ranks: bool = False,
    progress_callback: Callable[[str, int, int], None] | None = None,
    config: "Config | None" = None,  # noqa: UP007
    skip_overwrite_check: bool = False,
    server_name: str | None = None,
    auto_backup: bool = True,
    hooks: "EventHooks | None" = None,
) -> list[Path]:
    """Restore a checkpoint to a target directory.

    Extracts campaign files from a checkpoint ZIP archive to the specified
    target directory after verifying file integrity with SHA-256 checksums.
    By default, excludes Foothold_Ranks.lua unless explicitly requested.

    Before restoring, automatically creates a backup checkpoint of the current
    state (if auto_backup=True and server_name is provided). This provides a
    safety net to revert changes if needed.

    Args:
        checkpoint_path: Path to the checkpoint ZIP file to restore.
        target_dir: Path to the directory where files will be extracted.
        restore_ranks: If True, restore Foothold_Ranks.lua. If False (default),
            exclude ranks file from restoration.
        progress_callback: Optional callback function called during restoration.
            Called as: callback(message: str, current: int, total: int).
        config: Optional configuration object containing campaign name mappings.
            If provided, files will be renamed to use current campaign names
            (e.g., GCW_Modern → Germany_Modern). Also used for auto-backup.
            If None, original filenames are preserved (backward compatibility).
        skip_overwrite_check: If True, skip checking for existing files and
            confirmation prompt. Useful when confirmation was already done
            externally (default: False).
        server_name: Optional server name for auto-backup metadata. Required if
            auto_backup is True and config is provided.
        auto_backup: If True and config is provided, automatically create a backup
            checkpoint before restoring (default: True). The backup is saved with
            a timestamped name (auto-backup-YYYYMMDD-HHMMSS).
        hooks: Optional event hooks for operation notifications.

    Returns:
        List of Path objects for the restored files (with potentially renamed paths).

    Raises:
        FileNotFoundError: If checkpoint_path doesn't exist or target_dir doesn't exist.
        ValueError: If checkpoint is not a valid ZIP, metadata is missing/invalid,
            checksum verification fails, or server_name missing with auto_backup=True.
        PermissionError: If target_dir is not writable.
        RuntimeError: If user cancels overwrite confirmation.
        OSError: If restoration fails (e.g., disk full) or auto-backup creation fails.
    """
    import json
    import zipfile

    from foothold_checkpoint.core.events import safe_invoke_hook

    try:
        checkpoint_path = Path(checkpoint_path)
        target_dir = Path(target_dir)

        # Validate checkpoint file exists FIRST
        if not checkpoint_path.exists():
            raise FileNotFoundError("Checkpoint file not found")

        # Validate checkpoint is a valid ZIP BEFORE trying to open it
        if not zipfile.is_zipfile(checkpoint_path):
            raise ValueError("Invalid checkpoint file (not a valid ZIP archive)")

        # Read metadata to get campaign name for hook
        try:
            with zipfile.ZipFile(checkpoint_path, "r") as zf:
                if "metadata.json" in zf.namelist():
                    metadata_json = zf.read("metadata.json").decode("utf-8")
                    try:
                        metadata = json.loads(metadata_json)
                    except json.JSONDecodeError as e:
                        raise ValueError(f"Invalid metadata JSON: {e}") from e
                    campaign_name_for_hook = metadata.get("campaign_name", "unknown")
                else:
                    campaign_name_for_hook = "unknown"
        except zipfile.BadZipFile as e:
            raise ValueError(f"Invalid checkpoint file (not a valid ZIP archive): {e}") from e

        # Trigger on_restore_start hook
        if hooks:
            await safe_invoke_hook(
                hooks.on_restore_start,
                checkpoint_path.stem,
                campaign_name_for_hook,
                hook_name="on_restore_start",
            )

        # Validate target directory exists
        if not target_dir.exists():
            raise FileNotFoundError("Target directory does not exist")

        if not target_dir.is_dir():
            raise NotADirectoryError("Target path is not a directory")

        # Check target directory is writable
        if not _is_writable(target_dir):
            raise PermissionError(f"Target directory is not writable: {target_dir}")

        # Create automatic backup before restoring (if enabled and config provided)
        backup_path = None
        if auto_backup and config is not None:
            # Validate server_name is provided for auto-backup
            if server_name is None:
                raise ValueError(
                    "server_name is required when auto_backup=True with config provided"
                )

            if progress_callback:
                progress_callback("Creating automatic backup", 0, 1)

            try:
                backup_path = await create_auto_backup(
                    checkpoint_path=checkpoint_path,
                    target_dir=target_dir,
                    server_name=server_name,
                    checkpoints_dir=config.checkpoints_dir,
                    config=config,
                    progress_callback=progress_callback,
                    hooks=hooks,
                )
                if backup_path:
                    if progress_callback:
                        progress_callback(f"Auto-backup created: {backup_path.name}", 1, 1)
                    # Trigger on_backup_complete hook
                    if hooks:
                        await safe_invoke_hook(
                            hooks.on_backup_complete, backup_path, hook_name="on_backup_complete"
                        )
            except ValueError as e:
                # If no campaign files to backup, continue with restore
                if "No campaign files found" not in str(e):
                    raise
            except OSError as e:
                # Auto-backup failure is critical - don't proceed with restore
                raise OSError(f"Failed to create automatic backup: {e}") from e

        # Open ZIP and read metadata
        with zipfile.ZipFile(checkpoint_path, "r") as zf:
            # Check metadata.json exists
            if "metadata.json" not in zf.namelist():
                raise ValueError("Invalid checkpoint (missing metadata)")

            # Read and parse metadata.json
            try:
                metadata_json = zf.read("metadata.json").decode("utf-8")
                metadata = json.loads(metadata_json)
            except json.JSONDecodeError as e:
                raise ValueError(f"Invalid metadata JSON: {e}") from e

            # Get list of files to restore
            all_files_in_zip = [
                name
                for name in zf.namelist()
                if name != "metadata.json" and not name.endswith("/")
            ]

            # Filter out Foothold_Ranks.lua if not requested
            files_to_restore = []
            for filename in all_files_in_zip:
                if filename == "Foothold_Ranks.lua" and not restore_ranks:
                    continue
                files_to_restore.append(filename)

            if not files_to_restore:
                return []

            # Verify checksums before extraction (silently - progress during extraction only)
            # This avoids spinner/progress interference with confirmation prompts
            file_checksums = metadata.get("files", {})

            for _, filename in enumerate(files_to_restore, start=1):
                # Extract file to temp location for checksum verification
                file_data = zf.read(filename)

                # Compute checksum of extracted data
                import hashlib

                computed_checksum = hashlib.sha256(file_data).hexdigest()

                # Compare with metadata checksum
                expected_checksum = file_checksums.get(filename)
                if expected_checksum:
                    # Remove 'sha256:' prefix if present
                    if expected_checksum.startswith("sha256:"):
                        expected_checksum = expected_checksum[7:]  # len("sha256:") = 7

                    if computed_checksum != expected_checksum:
                        raise ValueError(
                            f"Checksum mismatch for file {filename}: "
                            f"expected {expected_checksum}, got {computed_checksum}"
                        )

            # Check for existing files and prompt for confirmation (unless skipped)
            if not skip_overwrite_check:
                existing_files = []
                for filename in files_to_restore:
                    target_file = target_dir / filename
                    if target_file.exists():
                        existing_files.append(filename)

                if existing_files:
                    # Prompt for confirmation
                    confirmation = input(
                        f"Files will be overwritten ({len(existing_files)} files). Continue? (y/n): "
                    )
                    if confirmation.lower() != "y":
                        raise RuntimeError("Restoration cancelled by user")

            # Extract files (with progress updates)
            if progress_callback:
                progress_callback("Extracting files", 0, len(files_to_restore))

            restored_files: list[Path] = []

            # Get campaign_name from metadata for file renaming
            campaign_name = metadata.get("campaign_name") if config else None

            for idx, filename in enumerate(files_to_restore, start=1):
                if progress_callback:
                    progress_callback(f"Extracting {filename}", idx, len(files_to_restore))

                # Trigger on_restore_progress hook
                if hooks:
                    await safe_invoke_hook(
                        hooks.on_restore_progress, idx, len(files_to_restore), hook_name="on_restore_progress"
                    )

                file_data = zf.read(filename)

                # Determine target filename (with potential renaming if config provided)
                target_filename = filename
                if config and campaign_name:
                    # Check if file should be renamed to canonical name
                    target_filename = _get_canonical_filename(filename, campaign_name, config)

                target_file = target_dir / target_filename

                # Write file
                target_file.write_bytes(file_data)
                restored_files.append(target_file)

        # Trigger on_restore_complete hook
        if hooks:
            restored_file_names = [str(f) for f in restored_files]
            await safe_invoke_hook(
                hooks.on_restore_complete, restored_file_names, hook_name="on_restore_complete"
            )

        return restored_files

    except Exception as e:
        # Trigger on_error hook
        if hooks:
            await safe_invoke_hook(hooks.on_error, e, hook_name="on_error")
        raise


async def list_checkpoints(
    checkpoint_dir: str | Path,
    server_filter: str | None = None,
    campaign_filter: str | None = None,
) -> list[dict]:
    """List all checkpoints in the checkpoint directory.

    Scans the checkpoint directory for valid checkpoint ZIP files and returns
    their metadata. Optionally filters by server and/or campaign name.

    Args:
        checkpoint_dir: Path to the directory containing checkpoint files.
        server_filter: Optional server name to filter checkpoints.
        campaign_filter: Optional campaign name to filter checkpoints.

    Returns:
        List of dictionaries containing checkpoint metadata. Each dictionary has:
        - filename: Name of the checkpoint file (str)
        - campaign: Campaign name (str)
        - server: Server name (str)
        - timestamp: ISO timestamp string (str)
        - size_bytes: File size in bytes (int)
        - size_human: Human-readable file size (str, e.g., "1.2 MB")
        - name: Optional user-provided name (str | None)
        - comment: Optional user-provided comment (str | None)

        List is sorted by timestamp (newest first).

    Raises:
        FileNotFoundError: If checkpoint directory doesn't exist.

    Examples:
        >>> # List all checkpoints
        >>> checkpoints = await list_checkpoints("/path/to/checkpoints")
        >>> for cp in checkpoints:
        ...     print(f"{cp['filename']}: {cp['campaign']} on {cp['server']}")

        >>> # Filter by server
        >>> checkpoints = await list_checkpoints("/path/to/checkpoints", server_filter="prod-1")

        >>> # Filter by both server and campaign
        >>> checkpoints = await list_checkpoints(
        ...     "/path/to/checkpoints",
        ...     server_filter="prod-1",
        ...     campaign_filter="afghanistan"
        ... )
    """
    import json
    import zipfile

    checkpoint_dir = Path(checkpoint_dir)

    # Validate checkpoint directory
    if not checkpoint_dir.exists():
        raise FileNotFoundError(f"Checkpoint directory not found: {checkpoint_dir}")

    checkpoints = []

    # Scan for ZIP files in checkpoint directory
    for checkpoint_path in checkpoint_dir.glob("*.zip"):
        try:
            # Read metadata without extracting entire ZIP
            with zipfile.ZipFile(checkpoint_path, "r") as zf:
                # Check if metadata.json exists
                if "metadata.json" not in zf.namelist():
                    continue

                # Read and parse metadata
                metadata_bytes = zf.read("metadata.json")
                metadata = json.loads(metadata_bytes.decode("utf-8"))

                # Extract required fields (using Pydantic field names)
                campaign = metadata.get("campaign_name")
                server = metadata.get("server_name")
                timestamp = metadata.get("created_at")

                if not all([campaign, server, timestamp]):
                    # Skip if missing required fields
                    continue

                # Apply filters (case-insensitive)
                if server_filter and server.lower() != server_filter.lower():
                    continue
                if campaign_filter and campaign.lower() != campaign_filter.lower():
                    continue

                # Calculate file size
                size_bytes = checkpoint_path.stat().st_size
                size_human = _format_file_size(size_bytes)

                # Get list of files in the checkpoint (excluding metadata.json)
                files_in_checkpoint = [
                    name
                    for name in zf.namelist()
                    if name != "metadata.json" and not name.endswith("/")
                ]

                # Build checkpoint info dictionary
                checkpoint_info = {
                    "filename": checkpoint_path.name,
                    "campaign": campaign,
                    "server": server,
                    "timestamp": timestamp,
                    "size_bytes": size_bytes,
                    "size_human": size_human,
                    "name": metadata.get("name"),
                    "comment": metadata.get("comment"),
                    "files": files_in_checkpoint,  # List of files in checkpoint
                }

                checkpoints.append(checkpoint_info)

        except (zipfile.BadZipFile, json.JSONDecodeError, KeyError, OSError):
            # Skip corrupted or invalid checkpoint files
            continue

    # Sort by timestamp (newest first)
    checkpoints.sort(key=lambda cp: cp["timestamp"], reverse=True)

    return checkpoints


async def delete_checkpoint(
    checkpoint_path: str | Path,
    force: bool = False,
    confirm_callback: Callable[[dict], bool] | None = None,
    hooks: "EventHooks | None" = None,
) -> dict | None:
    """Delete a checkpoint file from storage.

    Validates that the file is a valid checkpoint (ZIP with metadata.json) before deletion.
    In non-force mode, requires a confirmation callback to prompt the user.

    Args:
        checkpoint_path: Path to the checkpoint file to delete.
        force: If True, delete immediately without confirmation. Default False.
        confirm_callback: Callback function that receives metadata dict and returns bool.
                         Required when force=False. Should return True to confirm deletion.
        hooks: Optional event hooks for operation notifications.

    Returns:
        Metadata dict if deletion successful, None if user cancelled.

    Raises:
        FileNotFoundError: If checkpoint file does not exist.
        ValueError: If file is not a valid checkpoint (not a ZIP or missing metadata).
        ValueError: If force=False and confirm_callback is not provided.
        PermissionError: If user lacks permission to delete the file.
        OSError: If deletion fails for other reasons (file in use, disk error, etc.).

    Example:
        >>> # Force delete without confirmation
        >>> metadata = await delete_checkpoint("afghan_2024-02-13_14-30-00.zip", force=True)
        >>> print(f"Deleted {metadata['campaign_name']} checkpoint")

        >>> # Interactive deletion with confirmation
        >>> def confirm(meta):
        ...     print(f"Delete {meta['campaign_name']} from {meta['server_name']}?")
        ...     return input("(y/n): ").lower() == 'y'
        >>> await delete_checkpoint("checkpoint.zip", confirm_callback=confirm)
    """
    import json
    import zipfile
    from zipfile import BadZipFile

    from foothold_checkpoint.core.events import safe_invoke_hook

    try:
        checkpoint_path = Path(checkpoint_path)

        # Validate file exists
        if not checkpoint_path.exists():
            raise FileNotFoundError(f"Checkpoint file not found: {checkpoint_path.name}")

        # Validate it's a ZIP file
        if not zipfile.is_zipfile(checkpoint_path):
            raise ValueError(
                f"Not a valid checkpoint file: {checkpoint_path.name} is not a ZIP archive"
            )

        # Read and validate metadata
        try:
            with zipfile.ZipFile(checkpoint_path, "r") as zf:
                metadata_content = zf.read("metadata.json")
                metadata = cast(dict[Any, Any], json.loads(metadata_content))
        except BadZipFile as e:
            raise ValueError(
                f"Not a valid checkpoint file: {checkpoint_path.name} is corrupted"
            ) from e
        except KeyError as e:
            raise ValueError(
                f"Not a valid checkpoint (missing metadata): {checkpoint_path.name}"
            ) from e
        except json.JSONDecodeError as e:
            raise ValueError(
                f"Cannot read checkpoint metadata: {checkpoint_path.name} has invalid JSON"
            ) from e

        # Validate metadata has required fields
        required_fields = ["campaign_name", "server_name", "created_at"]
        missing_fields = [f for f in required_fields if f not in metadata]
        if missing_fields:
            raise ValueError(f"Cannot read checkpoint metadata: missing fields {missing_fields}")

        # Trigger on_delete_start hook
        checkpoint_name = checkpoint_path.stem
        if hooks:
            await safe_invoke_hook(
                hooks.on_delete_start, checkpoint_name, hook_name="on_delete_start"
            )

        # Handle confirmation
        if not force:
            if confirm_callback is None:
                raise ValueError("Confirmation callback required when force=False")

            # Call confirmation callback with metadata
            if not confirm_callback(metadata):
                # User cancelled
                return None

        # Delete the checkpoint file
        try:
            checkpoint_path.unlink()
        except PermissionError as e:
            raise PermissionError(
                f"Permission denied: cannot delete {checkpoint_path.name}"
            ) from e
        except OSError:
            # Re-raise as-is for other OS errors (file in use, disk errors, etc.)
            raise

        # Trigger on_delete_complete hook
        if hooks:
            await safe_invoke_hook(
                hooks.on_delete_complete, checkpoint_name, hook_name="on_delete_complete"
            )

        return metadata

    except Exception as e:
        # Trigger on_error hook
        if hooks:
            await safe_invoke_hook(hooks.on_error, e, hook_name="on_error")
        raise


def _format_file_size(size_bytes: int) -> str:
    """Format file size in human-readable format.

    Args:
        size_bytes: File size in bytes.

    Returns:
        Human-readable file size string (e.g., "1.2 MB", "450 KB").

    Examples:
        >>> _format_file_size(1024)
        '1.0 KB'
        >>> _format_file_size(1536)
        '1.5 KB'
        >>> _format_file_size(1048576)
        '1.0 MB'
        >>> _format_file_size(1073741824)
        '1.0 GB'
    """
    units = ["B", "KB", "MB", "GB", "TB"]
    size = float(size_bytes)
    unit_index = 0

    while size >= 1024.0 and unit_index < len(units) - 1:
        size /= 1024.0
        unit_index += 1

    return f"{size:.1f} {units[unit_index]}"


async def import_checkpoint(
    source_dir: str | Path,
    campaign_name: str,
    server_name: str,
    output_dir: str | Path,
    config: "Config",
    name: str | None = None,
    comment: str | None = None,
    created_at: datetime | None = None,
    return_warnings: bool = False,
) -> Path | tuple[Path, list[str]]:
    """Import campaign files from a directory and create a checkpoint.

    Scans the source directory for Foothold campaign files matching the specified
    campaign name and creates a checkpoint from them. Uses current timestamp by default.

    Args:
        source_dir: Directory containing campaign files to import.
        campaign_name: Name of the campaign to import (exact match).
        server_name: Name of the server for metadata.
        output_dir: Directory where checkpoint ZIP will be created.
        config: Configuration object containing campaign definitions.
        name: Optional user-friendly name for the checkpoint.
        comment: Optional comment describing the checkpoint.
        created_at: Optional timestamp (defaults to current UTC time).
        return_warnings: If True, returns tuple of (path, warnings list).

    Returns:
        Path to the created checkpoint ZIP file.
        If return_warnings=True, returns tuple of (Path, list of warning strings).

    Raises:
        FileNotFoundError: If source directory does not exist.
        ValueError: If source path is not a directory or no campaign files found.
        PermissionError: If source directory is not readable.

    Example:
        >>> # Import from manual backup directory
        >>> checkpoint = await import_checkpoint(
        ...     source_dir="/path/to/backup",
        ...     campaign_name="afghanistan",
        ...     server_name="prod-1",
        ...     output_dir="/path/to/checkpoints",
        ...     config=config,
        ...     name="Old Manual Backup",
        ... )

        >>> # Get warnings about missing files
        >>> checkpoint, warnings = await import_checkpoint(
        ...     source_dir="/path/to/incomplete",
        ...     campaign_name="afghanistan",
        ...     server_name="prod-1",
        ...     output_dir="/path/to/checkpoints",
        ...     config=config,
        ...     return_warnings=True,
        ... )
        >>> for warning in warnings:
        ...     print(f"Warning: {warning}")
    """
    source_dir = Path(source_dir)
    output_dir = Path(output_dir)

    # Validate source directory
    if not source_dir.exists():
        raise FileNotFoundError(f"Import directory not found: {source_dir}")

    if not source_dir.is_dir():
        raise ValueError(f"Not a directory: {source_dir}")

    # Create output directory if it doesn't exist
    output_dir.mkdir(parents=True, exist_ok=True)

    # Scan for campaign files matching the campaign name
    all_files = list(source_dir.iterdir())
    filenames = [f.name for f in all_files if f.is_file()]

    # Use campaign module to detect and group files
    from foothold_checkpoint.core.campaign import detect_campaigns

    grouped = detect_campaigns(filenames, config)

    # Check if specified campaign exists
    if campaign_name not in grouped:
        # Try case-insensitive match
        campaign_name_lower = campaign_name.lower()
        matching_campaign = None
        for camp_name in grouped:
            if camp_name.lower() == campaign_name_lower:
                matching_campaign = camp_name
                break

        if not matching_campaign:
            raise ValueError(
                f"No campaign files found for campaign '{campaign_name}' in {source_dir}"
            )
        # Use the matched campaign name
        campaign_files_names = grouped[matching_campaign]
    else:
        campaign_files_names = grouped[campaign_name]

    # Build full paths for campaign files
    campaign_files = [source_dir / fname for fname in campaign_files_names]

    # Also check for Foothold_Ranks.lua (shared file)
    ranks_file = source_dir / "Foothold_Ranks.lua"
    if ranks_file.is_file():
        campaign_files.append(ranks_file)

    if not campaign_files:
        raise ValueError(f"No campaign files found for '{campaign_name}'")

    # Check for expected files from config and generate warnings for missing required files
    warnings = []

    # Get campaign config to check for missing required files
    campaign_config = config.campaigns.get(campaign_name) if config.campaigns else None
    if campaign_config:
        campaign_files_names_lower = [f.lower() for f in campaign_files_names]

        # Check each file type in the config
        for file_type_name in ["persistence", "ctld_save", "ctld_farps", "storage"]:
            file_type = getattr(campaign_config.files, file_type_name, None)
            if file_type and not file_type.optional:
                # Check if any file from this type is present
                configured_files = file_type.files
                if configured_files:
                    found = any(
                        configured_file.lower() in campaign_files_names_lower
                        for configured_file in configured_files
                    )
                    if not found:
                        # Get friendly name for file type
                        type_descriptions = {
                            "persistence": "Campaign script file",
                            "ctld_save": "CTLD Save data",
                            "ctld_farps": "CTLD FARPS data",
                            "storage": "Storage data file",
                        }
                        desc = type_descriptions.get(file_type_name, file_type_name)
                        # Show the first configured filename as example
                        example = (
                            configured_files[0]
                            if configured_files
                            else f"(no {file_type_name} configured)"
                        )
                        warnings.append(f"{desc} not found: {example}")

    # Check for ranks file (always optional but good to warn)
    if not ranks_file.exists():
        warnings.append("Shared ranks file not found: Foothold_Ranks.lua")

    # Use create_checkpoint to build the checkpoint
    from foothold_checkpoint.core.checkpoint import create_checkpoint

    # Set default timestamp to current time
    if created_at is None:
        created_at = datetime.now(timezone.utc)

    checkpoint_path = create_checkpoint(
        campaign_name=campaign_name,
        server_name=server_name,
        campaign_files=campaign_files,
        output_dir=output_dir,
        created_at=created_at,
        name=name,
        comment=comment,
    )

    if return_warnings:
        return checkpoint_path, warnings

    return checkpoint_path


def _is_writable(path: Path) -> bool:
    """Check if a directory is writable.

    Args:
        path: Path to check for write permissions.

    Returns:
        True if writable, False otherwise.
    """
    import os

    return os.access(path, os.W_OK)

"""High-level checkpoint storage operations.

This module provides functions for saving, restoring, listing, and deleting
Foothold campaign checkpoints with integrity verification.
"""

from collections.abc import Callable
from datetime import datetime, timezone
from pathlib import Path
from typing import TYPE_CHECKING, Any, cast

from foothold_checkpoint.core.campaign import group_campaign_files, rename_campaign_file
from foothold_checkpoint.core.checkpoint import create_checkpoint

if TYPE_CHECKING:
    from foothold_checkpoint.core.config import Config


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
            f"Source directory '{source_dir}' is not readable. " f"Check file system permissions."
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


def restore_checkpoint(
    checkpoint_path: str | Path,
    target_dir: str | Path,
    restore_ranks: bool = False,
    progress_callback: Callable[[str, int, int], None] | None = None,
    config: "Config | None" = None,  # noqa: UP007
    skip_overwrite_check: bool = False,
) -> list[Path]:
    """Restore a checkpoint to a target directory.

    Extracts campaign files from a checkpoint ZIP archive to the specified
    target directory after verifying file integrity with SHA-256 checksums.
    By default, excludes Foothold_Ranks.lua unless explicitly requested.

    Args:
        checkpoint_path: Path to the checkpoint ZIP file to restore.
        target_dir: Path to the directory where files will be extracted.
        restore_ranks: If True, restore Foothold_Ranks.lua. If False (default),
            exclude ranks file from restoration.
        progress_callback: Optional callback function called during restoration.
            Called as: callback(message: str, current: int, total: int).
        config: Optional configuration object containing campaign name mappings.
            If provided, files will be renamed to use current campaign names
            (e.g., GCW_Modern → Germany_Modern). If None, original filenames
            are preserved (backward compatibility).
        skip_overwrite_check: If True, skip checking for existing files and
            confirmation prompt. Useful when confirmation was already done
            externally (default: False).

    Returns:
        List of Path objects for the restored files (with potentially renamed paths).

    Raises:
        FileNotFoundError: If checkpoint_path doesn't exist or target_dir doesn't exist.
        ValueError: If checkpoint is not a valid ZIP, metadata is missing/invalid,
            or checksum verification fails.
        PermissionError: If target_dir is not writable.
        RuntimeError: If user cancels overwrite confirmation.
        OSError: If restoration fails (e.g., disk full).
    """
    import json
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

    if not target_dir.is_dir():
        raise NotADirectoryError("Target path is not a directory")

    # Check target directory is writable
    if not _is_writable(target_dir):
        raise PermissionError(f"Target directory is not writable: {target_dir}")

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
            name for name in zf.namelist() if name != "metadata.json" and not name.endswith("/")
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

        for idx, filename in enumerate(files_to_restore, start=1):
            if progress_callback:
                progress_callback(f"Extracting {filename}", idx, len(files_to_restore))

            file_data = zf.read(filename)

            # Rename file if config is provided (campaign name evolution)
            if config is not None:
                target_filename = rename_campaign_file(filename, config)
            else:
                target_filename = filename

            target_file = target_dir / target_filename

            # Write file
            target_file.write_bytes(file_data)
            restored_files.append(target_file)

    return restored_files


def list_checkpoints(
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
        >>> checkpoints = list_checkpoints("/path/to/checkpoints")
        >>> for cp in checkpoints:
        ...     print(f"{cp['filename']}: {cp['campaign']} on {cp['server']}")

        >>> # Filter by server
        >>> checkpoints = list_checkpoints("/path/to/checkpoints", server_filter="prod-1")

        >>> # Filter by both server and campaign
        >>> checkpoints = list_checkpoints(
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
                }

                checkpoints.append(checkpoint_info)

        except (zipfile.BadZipFile, json.JSONDecodeError, KeyError, OSError):
            # Skip corrupted or invalid checkpoint files
            continue

    # Sort by timestamp (newest first)
    checkpoints.sort(key=lambda cp: cp["timestamp"], reverse=True)

    return checkpoints


def delete_checkpoint(
    checkpoint_path: str | Path,
    force: bool = False,
    confirm_callback: Callable[[dict], bool] | None = None,
) -> dict | None:
    """Delete a checkpoint file from storage.

    Validates that the file is a valid checkpoint (ZIP with metadata.json) before deletion.
    In non-force mode, requires a confirmation callback to prompt the user.

    Args:
        checkpoint_path: Path to the checkpoint file to delete.
        force: If True, delete immediately without confirmation. Default False.
        confirm_callback: Callback function that receives metadata dict and returns bool.
                         Required when force=False. Should return True to confirm deletion.

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
        >>> metadata = delete_checkpoint("afghan_2024-02-13_14-30-00.zip", force=True)
        >>> print(f"Deleted {metadata['campaign_name']} checkpoint")

        >>> # Interactive deletion with confirmation
        >>> def confirm(meta):
        ...     print(f"Delete {meta['campaign_name']} from {meta['server_name']}?")
        ...     return input("(y/n): ").lower() == 'y'
        >>> delete_checkpoint("checkpoint.zip", confirm_callback=confirm)
    """
    import json
    import zipfile
    from zipfile import BadZipFile

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
        raise ValueError(f"Not a valid checkpoint file: {checkpoint_path.name} is corrupted") from e
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
        raise PermissionError(f"Permission denied: cannot delete {checkpoint_path.name}") from e
    except OSError:
        # Re-raise as-is for other OS errors (file in use, disk errors, etc.)
        raise

    return metadata


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


def import_checkpoint(
    source_dir: str | Path,
    campaign_name: str,
    server_name: str,
    output_dir: str | Path,
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
        >>> checkpoint = import_checkpoint(
        ...     source_dir="/path/to/backup",
        ...     campaign_name="afghanistan",
        ...     server_name="prod-1",
        ...     output_dir="/path/to/checkpoints",
        ...     name="Old Manual Backup",
        ... )

        >>> # Get warnings about missing files
        >>> checkpoint, warnings = import_checkpoint(
        ...     source_dir="/path/to/incomplete",
        ...     campaign_name="afghanistan",
        ...     server_name="prod-1",
        ...     output_dir="/path/to/checkpoints",
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
    from foothold_checkpoint.core.campaign import group_campaign_files

    grouped = group_campaign_files(filenames)

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

    # Check for expected files and generate warnings
    warnings = []
    expected_patterns = [
        (f"foothold_{campaign_name}.lua", "Campaign script file"),
        (f"foothold_{campaign_name}_storage.csv", "Storage data file"),
        (f"foothold_{campaign_name}_CTLD_FARPS.csv", "CTLD FARPS data"),
        (f"foothold_{campaign_name}_CTLD_Save.csv", "CTLD Save data"),
    ]

    for pattern, description in expected_patterns:
        # Check case-insensitively
        found = any(
            fname.lower() == pattern.lower() or
            # Also check with version suffixes
            (
                fname.lower().startswith(pattern.lower().rsplit(".", 1)[0])
                and fname.lower().endswith(pattern.lower().rsplit(".", 1)[1])
            )
            for fname in campaign_files_names
        )
        if not found:
            warnings.append(f"{description} not found: {pattern}")

    # Check for ranks file
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

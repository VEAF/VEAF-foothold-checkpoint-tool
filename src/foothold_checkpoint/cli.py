"""Command-line interface for foothold-checkpoint tool."""

import signal
import sys
from pathlib import Path
from types import FrameType
from typing import Annotated, Any, Optional  # noqa: UP035 - Required for Typer compatibility

import typer
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TaskID, TextColumn
from rich.prompt import Prompt

from foothold_checkpoint.core.campaign import detect_campaigns, group_campaign_files
from foothold_checkpoint.core.checkpoint import create_checkpoint
from foothold_checkpoint.core.config import load_config
from foothold_checkpoint.core.storage import (
    check_restore_conflicts,
    delete_checkpoint,
    import_checkpoint,
    list_checkpoints,
    restore_checkpoint,
)

# Package version
__version__ = "0.1.0"

# Global state for CLI options
_quiet_mode = False
_config_path: Path | None = None

# Console for Rich output
console = Console()

# Create Typer app with metadata
app = typer.Typer(
    name="foothold-checkpoint",
    help="CLI tool for managing DCS Foothold campaign checkpoints with integrity verification",
    add_completion=False,
)


def find_key_case_insensitive(dictionary: dict[str, Any], key: str) -> str | None:
    """Find a key in a dictionary using case-insensitive matching.

    Also tries appending '_Modern' if exact match not found (Foothold convention).

    Args:
        dictionary: Dictionary to search in
        key: Key to find (case-insensitive)

    Returns:
        The actual key from the dictionary if found, None otherwise
    """
    key_lower = key.lower()

    # First pass: exact match
    for dict_key in dictionary:
        if dict_key.lower() == key_lower:
            return str(dict_key)

    # Second pass: try with '_Modern' suffix (Foothold default era)
    key_with_modern = f"{key}_Modern"
    key_with_modern_lower = key_with_modern.lower()
    for dict_key in dictionary:
        if dict_key.lower() == key_with_modern_lower:
            return str(dict_key)

    return None


def is_numeric_selection(text: str) -> bool:
    """Check if a string looks like a numeric selection (e.g., '1', '1,3,5', '1-3').

    Args:
        text: String to check

    Returns:
        True if text contains only digits, commas, hyphens, and spaces
    """
    # Remove whitespace and check if remaining chars are only digits, commas, hyphens
    cleaned = text.replace(" ", "")
    return bool(cleaned) and all(c in "0123456789,-" for c in cleaned)


def parse_selection(selection: str, max_value: int) -> list[int]:
    """Parse a multi-selection string into a list of indices.

    Supports:
    - Single numbers: "3" -> [3]
    - Comma-separated: "1,3,5" -> [1, 3, 5]
    - Ranges: "1-3" -> [1, 2, 3]
    - Mixed: "1,3-5,7" -> [1, 3, 4, 5, 7]

    Args:
        selection: Selection string from user input
        max_value: Maximum valid index value

    Returns:
        List of selected indices (sorted, no duplicates)

    Raises:
        ValueError: If selection format is invalid or values out of range
    """
    indices: set[int] = set()

    # Split by comma
    parts = selection.split(",")

    for part in parts:
        part = part.strip()

        # Check if it's a range (e.g., "1-3")
        if "-" in part:
            try:
                start, end = part.split("-", 1)
                start_idx = int(start.strip())
                end_idx = int(end.strip())

                if start_idx < 1 or end_idx > max_value or start_idx > end_idx:
                    raise ValueError(
                        f"Invalid range: {part}. Must be between 1 and {max_value}, "
                        f"with start <= end"
                    )

                indices.update(range(start_idx, end_idx + 1))
            except ValueError as e:
                if "invalid literal" in str(e):
                    raise ValueError(f"Invalid range format: {part}. Use format like '1-3'") from e
                raise
        else:
            # Single number
            try:
                idx = int(part)
                if idx < 1 or idx > max_value:
                    raise ValueError(f"Invalid selection: {idx}. Must be between 1 and {max_value}")
                indices.add(idx)
            except ValueError as e:
                if "invalid literal" in str(e):
                    raise ValueError(f"Invalid number: {part}") from e
                raise

    return sorted(indices)


def config_callback(value: str | None) -> Path | None:
    """Validate and set custom config path.

    Args:
        value: Path to custom config file

    Returns:
        Path object if config file exists, None if not provided

    Raises:
        typer.Exit: If config file doesn't exist
    """
    global _config_path

    if value is None:
        # Use default config path (will be handled by config module)
        _config_path = None
        return None

    config_path = Path(value)
    if not config_path.exists():
        console.print(f"[red]Error:[/red] Config file not found: {config_path}")
        raise typer.Exit(1)

    if not config_path.is_file():
        console.print(f"[red]Error:[/red] Config path is not a file: {config_path}")
        raise typer.Exit(1)

    _config_path = config_path
    return config_path


def quiet_callback(value: bool) -> None:
    """Set quiet mode for suppressed output.

    Args:
        value: True if --quiet flag was provided
    """
    global _quiet_mode
    _quiet_mode = value


def is_quiet_mode() -> bool:
    """Check if quiet mode is enabled.

    Returns:
        True if --quiet flag was provided, False otherwise
    """
    return _quiet_mode


def get_config_path() -> Path | None:
    """Get the custom config path if specified.

    Returns:
        Path to custom config file, or None for default
    """
    return _config_path


def interrupt_handler(_signum: int, _frame: FrameType | None) -> None:
    """Handle interrupt signal (Ctrl+C) gracefully.

    Args:
        _signum: Signal number (unused)
        _frame: Current stack frame (unused)

    Raises:
        SystemExit: Always exits with code 130 (128 + SIGINT)
    """
    console.print("\n[yellow]Operation cancelled by user[/yellow]")
    sys.exit(130)  # Standard exit code for SIGINT (128 + 2)


# Register interrupt handler
signal.signal(signal.SIGINT, interrupt_handler)


@app.callback(invoke_without_command=True)
def main_callback(
    ctx: typer.Context,
    version: Annotated[
        bool,
        typer.Option(
            "--version",
            is_flag=True,
            flag_value=True,
            help="Show version and exit",
        ),
    ] = False,
    config: Annotated[  # noqa: ARG001 - handled by eager callback
        Optional[str],  # noqa: UP007 - Typer requires Optional
        typer.Option(
            "--config",
            callback=config_callback,
            is_eager=True,
            help="Path to custom configuration file",
        ),
    ] = None,
    quiet: Annotated[
        bool,
        typer.Option(
            "--quiet",
            is_flag=True,
            flag_value=True,
            help="Suppress non-essential output",
        ),
    ] = False,
) -> None:
    """Foothold Checkpoint Tool - Manage DCS Foothold campaign checkpoints.

    This tool provides commands to save, restore, list, delete, and import
    campaign checkpoints with integrity verification.
    """
    # Handle version flag
    if version:
        console.print(f"foothold-checkpoint version {__version__}")
        raise typer.Exit(0)

    # Handle quiet flag (reset to False if not provided)
    global _quiet_mode
    _quiet_mode = quiet

    # If no subcommand was invoked and not in quiet mode, show interactive menu
    if ctx.invoked_subcommand is None and not _quiet_mode:
        console.print("[cyan]Foothold Checkpoint Tool[/cyan] - Select a command:\n")
        console.print("  [cyan]1.[/cyan] Save checkpoint")
        console.print("  [cyan]2.[/cyan] Restore checkpoint")
        console.print("  [cyan]3.[/cyan] List checkpoints")
        console.print("  [cyan]4.[/cyan] Delete checkpoint")
        console.print("  [cyan]5.[/cyan] Import checkpoint")
        console.print("  [cyan]Q.[/cyan] Quit\n")

        choice = Prompt.ask("Select option", default="1")

        if choice.upper() == "Q":
            console.print("[yellow]Goodbye![/yellow]")
            raise typer.Exit(0)
        elif choice == "1":
            ctx.invoke(save_command)
        elif choice == "2":
            ctx.invoke(restore_command)
        elif choice == "3":
            ctx.invoke(list_command)
        elif choice == "4":
            ctx.invoke(delete_command)
        elif choice == "5":
            ctx.invoke(import_command)
        else:
            console.print(f"[red]Invalid choice:[/red] '{choice}'")
            raise typer.Exit(1)


@app.command("save")
def save_command(
    server: Annotated[
        Optional[str],  # noqa: UP007 - Typer requires Optional
        typer.Option(
            "--server",
            "-s",
            help="Server name from configuration",
        ),
    ] = None,
    campaign: Annotated[
        Optional[str],  # noqa: UP007 - Typer requires Optional
        typer.Option(
            "--campaign",
            "-c",
            help="Campaign name to save",
        ),
    ] = None,
    save_all: Annotated[
        bool,
        typer.Option(
            "--all",
            "-a",
            is_flag=True,
            flag_value=True,
            help="Save all detected campaigns",
        ),
    ] = False,
    name: Annotated[
        Optional[str],  # noqa: UP007 - Typer requires Optional
        typer.Option(
            "--name",
            "-n",
            help="Optional name for the checkpoint",
        ),
    ] = None,
    comment: Annotated[
        Optional[str],  # noqa: UP007 - Typer requires Optional
        typer.Option(
            "--comment",
            "-m",
            help="Optional comment/description for the checkpoint",
        ),
    ] = None,
) -> None:
    """Save a campaign checkpoint.

    Create a checkpoint (backup) of a Foothold campaign from a DCS server's mission directory.
    The checkpoint includes all campaign files with integrity checksums.

    Examples:
        Save a specific campaign:
        $ foothold-checkpoint save --server prod-1 --campaign afghanistan

        Save all campaigns on a server:
        $ foothold-checkpoint save --server prod-1 --all

        Save with optional metadata:
        $ foothold-checkpoint save --server prod-1 --campaign syria --name "Mission 5" --comment "Before update"

    Interactive mode (prompts for missing information):
        $ foothold-checkpoint save
    """
    try:
        # Validate conflicting flags
        if campaign is not None and save_all:
            console.print("[red]Error:[/red] Cannot use both --campaign and --all flags together")
            console.print("Please specify either a campaign name OR use --all, not both")
            raise typer.Exit(1)

        # Load configuration
        config_file = _config_path if _config_path is not None else Path("config.yaml")
        config = load_config(config_file)

        # Step 1: Get server name (from flag or prompt)
        if server is None:
            available_servers = list(config.servers.keys())
            if not available_servers:
                console.print("[red]Error:[/red] No servers configured in config file")
                raise typer.Exit(1)

            if not _quiet_mode:
                console.print("\n[cyan]Available servers:[/cyan]")
                for idx, srv in enumerate(available_servers, 1):
                    console.print(f"  {srv} ({idx})")

            # Accept both number and server name (validate manually)
            while True:
                selection = Prompt.ask("\nSelect server", default="1")
                # Try as number first
                if selection.isdigit():
                    idx = int(selection)
                    if 1 <= idx <= len(available_servers):
                        server = available_servers[idx - 1]
                        break
                # Try as server name
                elif selection in available_servers:
                    server = selection
                    break
                else:
                    console.print(f"[red]Invalid selection:[/red] '{selection}'")
                    console.print(
                        f"Please enter a number (1-{len(available_servers)}) or a server name"
                    )

        # Validate server exists (case-insensitive)
        actual_server = find_key_case_insensitive(config.servers, server)
        if actual_server is None:
            available = ", ".join(config.servers.keys())
            console.print(f"[red]Error:[/red] Server '{server}' not found in configuration")
            console.print(f"Available servers: {available}")
            raise typer.Exit(1)

        # Use the actual server name from config
        server = actual_server
        server_config = config.servers[server]
        # Add Missions/Saves to server path (DCS standard directory structure)
        mission_dir = Path(server_config.path) / "Missions" / "Saves"

        # Validate mission directory exists
        if not mission_dir.exists():
            console.print(
                f"[red]Error:[/red] Mission saves directory does not exist: {mission_dir}\n"
                f"[yellow]Hint:[/yellow] Server path should point to the DCS server root directory.\n"
                f"       The tool automatically looks in 'Missions/Saves' subdirectory."
            )
            raise typer.Exit(1)

        # Step 2: Detect campaigns in mission directory
        campaign_files = [f for f in mission_dir.iterdir() if f.is_file()]
        campaigns = detect_campaigns([f.name for f in campaign_files], config)

        if not campaigns:
            console.print(f"[red]Error:[/red] No campaigns detected in {mission_dir}")
            raise typer.Exit(1)

        # Step 3: Determine which campaigns to save
        campaigns_to_save: list[str] = []

        if save_all:
            # Save all detected campaigns
            campaigns_to_save = list(campaigns.keys())
        elif campaign is not None:
            # Save specific campaign (case-insensitive)
            actual_campaign = find_key_case_insensitive(campaigns, campaign)
            if actual_campaign is None:
                available = ", ".join(campaigns.keys())
                console.print(
                    f"[red]Error:[/red] Campaign '{campaign}' not found in mission directory"
                )
                console.print(f"Available campaigns: {available}")
                raise typer.Exit(1)
            # Use the actual campaign name
            campaign = actual_campaign
            campaigns_to_save = [campaign]
        else:
            # Prompt for campaign selection
            campaign_list = list(campaigns.keys())
            if not _quiet_mode:
                console.print("\n[cyan]Detected campaigns:[/cyan]")
                for idx, camp in enumerate(campaign_list, 1):
                    file_count = len(campaigns[camp])
                    console.print(
                        f"  {camp} ({idx}) - {file_count} file{'s' if file_count > 1 else ''}"
                    )
                console.print("  [yellow]all[/yellow] (A) - save all campaigns")

            # Accept numbers (1-N), campaign names, 'A' or 'all' (validate manually)
            while True:
                selected = Prompt.ask("\nSelect campaign", default="1")
                # Try 'all' options
                if selected.upper() in ["A", "ALL"]:
                    campaigns_to_save = campaign_list
                    break
                # Try as number
                elif selected.isdigit():
                    idx = int(selected)
                    if 1 <= idx <= len(campaign_list):
                        campaigns_to_save = [campaign_list[idx - 1]]
                        break
                # Try as campaign name (case-insensitive)
                else:
                    # Build dict for case-insensitive lookup
                    campaign_dict = {c: c for c in campaign_list}
                    actual_campaign = find_key_case_insensitive(campaign_dict, selected)
                    if actual_campaign:
                        campaigns_to_save = [actual_campaign]
                        break
                    else:
                        console.print(f"[red]Invalid selection:[/red] '{selected}'")
                        console.print(
                            f"Please enter a number (1-{len(campaign_list)}), campaign name, or 'A' for all"
                        )

        # Step 4: Get optional name and comment (prompt if not provided as flags)
        checkpoint_name = name
        checkpoint_comment = comment

        # Only prompt for name/comment in interactive mode:
        # - Not quiet mode
        # - Saving a single campaign (not --all)
        # - Neither --campaign nor --all flags were provided (pure interactive mode)
        in_interactive_mode = campaign is None and not save_all

        if checkpoint_name is None and not _quiet_mode and not save_all and in_interactive_mode:
            # Only prompt for name/comment if in full interactive mode
            checkpoint_name = Prompt.ask(
                "Checkpoint name (optional, press Enter to skip)", default=""
            )
            if checkpoint_name == "":
                checkpoint_name = None

        if checkpoint_comment is None and not _quiet_mode and not save_all and in_interactive_mode:
            checkpoint_comment = Prompt.ask(
                "Checkpoint comment (optional, press Enter to skip)", default=""
            )
            if checkpoint_comment == "":
                checkpoint_comment = None

        # Step 5: Create checkpoints
        checkpoints_dir = Path(config.checkpoints_dir)
        checkpoints_dir.mkdir(parents=True, exist_ok=True)

        created_checkpoints: list[Path] = []

        for camp_name in campaigns_to_save:
            camp_files = campaigns[camp_name]
            camp_file_paths = [mission_dir / fname for fname in camp_files]

            if not _quiet_mode:
                console.print(f"\n[cyan]Saving checkpoint for campaign:[/cyan] {camp_name}")

            # Create progress callback for Rich progress display
            progress_callback = None
            if not _quiet_mode:
                with Progress(
                    SpinnerColumn(),
                    TextColumn("[progress.description]{task.description}"),
                    console=console,
                    transient=True,  # Auto-clear spinner when done
                ) as progress:
                    task = progress.add_task(f"Creating checkpoint for {camp_name}...", total=None)

                    def update_progress(
                        message: str, current: int, total: int, _task: TaskID = task
                    ) -> None:
                        progress.update(_task, description=f"{message} ({current}/{total})")

                    progress_callback = update_progress

                    try:
                        checkpoint_path = create_checkpoint(
                            campaign_name=camp_name,
                            server_name=server,
                            campaign_files=camp_file_paths,
                            output_dir=checkpoints_dir,
                            name=checkpoint_name,
                            comment=checkpoint_comment,
                            progress_callback=progress_callback,
                        )
                        created_checkpoints.append(checkpoint_path)
                    except FileNotFoundError as e:
                        console.print(f"[red]Error:[/red] {e}")
                        raise typer.Exit(1) from e
            else:
                # Quiet mode: no progress display
                try:
                    checkpoint_path = create_checkpoint(
                        campaign_name=camp_name,
                        server_name=server,
                        campaign_files=camp_file_paths,
                        output_dir=checkpoints_dir,
                        name=checkpoint_name,
                        comment=checkpoint_comment,
                        progress_callback=None,
                    )
                    created_checkpoints.append(checkpoint_path)
                except FileNotFoundError as e:
                    console.print(f"[red]Error:[/red] {e}")
                    raise typer.Exit(1) from e

        # Step 6: Display success message
        if not _quiet_mode:
            console.print(
                f"\n[green]✓ Success![/green] Created {len(created_checkpoints)} checkpoint(s):"
            )
            for cp_path in created_checkpoints:
                console.print(f"  - {cp_path.name}")
        else:
            # In quiet mode, just print the paths
            for cp_path in created_checkpoints:
                console.print(str(cp_path))

    except FileNotFoundError as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1) from e
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1) from e


@app.command("restore")
def restore_command(
    checkpoint_file: Annotated[
        Optional[str],  # noqa: UP007 - Typer requires Optional
        typer.Argument(
            help="Checkpoint to restore: file path, number from list, or selection (e.g., '1', '1,3', '1-3'). Omit to select interactively."
        ),
    ] = None,
    server: Annotated[
        Optional[str],  # noqa: UP007 - Typer requires Optional
        typer.Option(
            "--server",
            "-s",
            help="Target server name from configuration",
        ),
    ] = None,
    restore_ranks: Annotated[
        bool,
        typer.Option(
            "--restore-ranks",
            is_flag=True,
            flag_value=True,
            help="Include Foothold_Ranks.lua in restoration",
        ),
    ] = False,
) -> None:
    """Restore a checkpoint to a target server directory.

    The checkpoint can be specified as:
    - A file path: 'checkpoints/afghanistan_20240315.zip'
    - A number from the list: '1' (restores the first checkpoint)
    - Multiple selections: '1,3,5' or '1-3' (restores multiple checkpoints)
    - Omitted for interactive selection

    If --server is not provided, prompts for server selection.

    The restore process verifies file integrity, excludes Foothold_Ranks.lua by
    default, and prompts for confirmation if files will be overwritten.

    Examples:

        # Restore by number (from list command)
        $ foothold-checkpoint restore 1 --server test-server

        # Restore multiple checkpoints
        $ foothold-checkpoint restore 1,3,5 --server test-server

        # Restore specific checkpoint file by path
        $ foothold-checkpoint restore afghanistan_checkpoint.zip --server test-server

        # Restore with ranks file included
        $ foothold-checkpoint restore 1 --server prod-1 --restore-ranks

        # Interactive mode (select checkpoint and server)
        $ foothold-checkpoint restore
    """
    try:
        # Step 1: Load configuration
        config_file = _config_path if _config_path else Path("config.yaml")
        config = load_config(config_file)

        # Step 2: Get checkpoint file(s)
        checkpoint_paths: list[Path]
        if checkpoint_file:
            # Check if checkpoint_file is a numeric selection (e.g., "1", "1,3", "1-3")
            if is_numeric_selection(checkpoint_file):
                # Resolve numeric selection by listing checkpoints
                checkpoints = list_checkpoints(config.checkpoints_dir)

                if not checkpoints:
                    console.print("[red]Error:[/red] No checkpoints found in checkpoint directory")
                    raise typer.Exit(1)

                try:
                    selected_indices = parse_selection(checkpoint_file, len(checkpoints))
                except ValueError as e:
                    console.print(f"[red]Error:[/red] Invalid checkpoint selection: {e}")
                    raise typer.Exit(1) from e

                # Build list of checkpoint paths from indices
                checkpoint_paths = [
                    Path(config.checkpoints_dir) / checkpoints[idx - 1]["filename"]
                    for idx in selected_indices
                ]

                # Show what was selected (helpful feedback)
                if not _quiet_mode:
                    console.print("[cyan]Selected checkpoint(s):[/cyan]")
                    for idx in selected_indices:
                        console.print(f"  {idx}. {checkpoints[idx - 1]['filename']}")
            else:
                # Treat as file path (existing behavior)
                checkpoint_path = Path(checkpoint_file)
                # Validate checkpoint file exists
                if not checkpoint_path.exists():
                    console.print(f"[red]Error:[/red] Checkpoint file not found: {checkpoint_path}")
                    raise typer.Exit(1)
                checkpoint_paths = [checkpoint_path]
        else:
            # Interactive mode: list and prompt for checkpoint selection
            if not _quiet_mode:
                console.print("[cyan]Available checkpoints:[/cyan]")

            # List all checkpoints
            checkpoints = list_checkpoints(config.checkpoints_dir)

            if not checkpoints:
                console.print("[red]Error:[/red] No checkpoints found in checkpoint directory")
                raise typer.Exit(1)

            # Display checkpoints with numbering
            if not _quiet_mode:
                for idx, cp in enumerate(checkpoints, start=1):
                    # Build display string with optional name/comment
                    display_parts = [
                        f"  {idx}. {cp['filename']}",
                        f"[dim](Campaign: {cp['campaign']}, Server: {cp['server']},",
                        f"Created: {cp['timestamp']})",
                    ]

                    # Add name if present
                    if cp.get("name"):
                        display_parts.insert(2, f"[blue]Name: {cp['name']}[/blue],")

                    # Add comment if present
                    if cp.get("comment"):
                        display_parts.insert(-1, f"[white]Comment: {cp['comment']}[/white],")

                    console.print(" ".join(display_parts))

            # Prompt for selection (supports multiple: "1,3,5" or "1-3")
            console.print(
                "\n[dim]Tip: You can select multiple checkpoints (e.g., '1,3,5' or '1-3')[/dim]"
            )
            selection_str = Prompt.ask("\nSelect checkpoint number(s)", default="1")

            try:
                selected_indices = parse_selection(selection_str, len(checkpoints))
            except ValueError as e:
                console.print(f"[red]Error:[/red] {e}")
                raise typer.Exit(1) from e

            # Build list of checkpoint paths
            checkpoint_paths = [
                Path(config.checkpoints_dir) / checkpoints[idx - 1]["filename"]
                for idx in selected_indices
            ]

        # Step 3: Get target server
        if server is None:
            # Prompt for server selection
            available_servers = list(config.servers.keys())
            if not available_servers:
                console.print("[red]Error:[/red] No servers configured")
                raise typer.Exit(1)

            if not _quiet_mode:
                console.print("\n[cyan]Available servers:[/cyan]")
                for idx, srv in enumerate(available_servers, 1):
                    console.print(f"  {srv} ({idx})")

            # Accept both number and server name (validate manually)
            while True:
                selection = Prompt.ask("\nSelect target server", default="1")
                if selection.isdigit():
                    idx = int(selection)
                    if 1 <= idx <= len(available_servers):
                        server = available_servers[idx - 1]
                        break
                elif selection in available_servers:
                    server = selection
                    break
                else:
                    console.print(f"[red]Invalid selection:[/red] '{selection}'")
                    console.print(
                        f"Please enter a number (1-{len(available_servers)}) or a server name"
                    )

        # Validate server exists in config (case-insensitive)
        actual_server = find_key_case_insensitive(config.servers, server)
        if actual_server is None:
            console.print(
                f"[red]Error:[/red] Server '{server}' not found in configuration.\n"
                f"Available servers: {', '.join(config.servers.keys())}"
            )
            raise typer.Exit(1)

        # Use the actual server name from config
        server = actual_server

        # Get target directory from server config
        # Add Missions/Saves to server path (DCS standard directory structure)
        target_dir = Path(config.servers[server].path) / "Missions" / "Saves"

        # Step 4: Restore checkpoint(s) with progress display
        total_restored = 0

        for idx, checkpoint_path in enumerate(checkpoint_paths, 1):
            if not _quiet_mode and len(checkpoint_paths) > 1:
                console.print(f"\n[cyan]Restoring checkpoint {idx}/{len(checkpoint_paths)}[/cyan]")

            if not _quiet_mode:
                console.print(f"[cyan]Checkpoint:[/cyan] {checkpoint_path.name}")
                console.print(f"[cyan]Target server:[/cyan] {server}")
                console.print(f"[cyan]Target directory:[/cyan] {target_dir}")
                console.print(
                    f"[cyan]Include ranks file:[/cyan] {'Yes' if restore_ranks else 'No'}\n"
                )

                # Check for file conflicts BEFORE opening Progress context
                existing_files = check_restore_conflicts(
                    checkpoint_path=checkpoint_path,
                    target_dir=target_dir,
                    restore_ranks=restore_ranks,
                )

                # Ask for confirmation if files would be overwritten
                if existing_files:
                    confirmation = input(
                        f"Files will be overwritten ({len(existing_files)} files). Continue? (y/n): "
                    )
                    if confirmation.lower() != "y":
                        console.print("[yellow]Restoration cancelled by user[/yellow]")
                        raise typer.Exit(1)

                # Progress display with Rich (after confirmation)
                with Progress(
                    SpinnerColumn(),
                    TextColumn("[progress.description]{task.description}"),
                    console=console,
                    transient=True,  # Auto-clear spinner when done
                ) as progress:
                    task = progress.add_task("Restoring checkpoint...", total=None)

                    def update_progress(
                        message: str, current: int, total: int, _task: TaskID = task
                    ) -> None:
                        """Update progress display with current status."""
                        progress.update(_task, description=f"{message} ({current}/{total})")

                    # Restore with progress callback (skip overwrite check since we already confirmed)
                    restored_files = restore_checkpoint(
                        checkpoint_path=checkpoint_path,
                        target_dir=target_dir,
                        restore_ranks=restore_ranks,
                        progress_callback=update_progress,
                        skip_overwrite_check=True,
                    )
            else:
                # Quiet mode: no progress display, no interactive confirmation
                # In quiet mode, we assume user wants to overwrite (typical for automation)
                restored_files = restore_checkpoint(
                    checkpoint_path=checkpoint_path,
                    target_dir=target_dir,
                    restore_ranks=restore_ranks,
                    progress_callback=None,
                    skip_overwrite_check=True,  # No confirmation in quiet mode
                )

            total_restored += len(restored_files)

            # Display success for this checkpoint
            if not _quiet_mode:
                console.print(
                    f"[green]✓ Restored {len(restored_files)} file(s) from {checkpoint_path.name}[/green]"
                )
            else:
                # In quiet mode, just print the paths
                for file_path in restored_files:
                    console.print(str(file_path))

        # Step 5: Display final summary
        if not _quiet_mode and len(checkpoint_paths) > 1:
            console.print(
                f"\n[green]✓ Success![/green] Restored {len(checkpoint_paths)} checkpoint(s) "
                f"({total_restored} total files) to {server}"
            )

    except FileNotFoundError as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1) from e
    except ValueError as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1) from e
    except RuntimeError as e:
        console.print(f"[yellow]Warning:[/yellow] {e}")
        raise typer.Exit(1) from e
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1) from e


@app.command("list")
def list_command(
    server: Annotated[
        Optional[str],  # noqa: UP007 - Typer requires Optional
        typer.Option("--server", "-s", help="Filter checkpoints by server name"),
    ] = None,
    campaign: Annotated[
        Optional[str],  # noqa: UP007 - Typer requires Optional
        typer.Option("--campaign", "-c", help="Filter checkpoints by campaign name"),
    ] = None,
) -> None:
    """List available checkpoints with optional filters.

    Displays all checkpoints in the checkpoints directory, optionally filtered
    by server and/or campaign name. Shows checkpoint metadata including filename,
    campaign, server, timestamp, and file size in a formatted table.

    Args:
        server: Optional server name to filter checkpoints
        campaign: Optional campaign name to filter checkpoints

    Examples:
        # List all checkpoints
        foothold-checkpoint list

        # Filter by server
        foothold-checkpoint list --server prod-1

        # Filter by campaign
        foothold-checkpoint list --campaign afghanistan

        # Filter by both
        foothold-checkpoint list --server prod-1 --campaign afghanistan

        # Quiet mode (filenames only)
        foothold-checkpoint --quiet list
    """
    try:
        # Load configuration
        config_file = _config_path if _config_path else Path("config.yaml")
        config = load_config(config_file)

        # List checkpoints with filters
        checkpoints = list_checkpoints(
            config.checkpoints_dir, server_filter=server, campaign_filter=campaign
        )

        # Handle empty results
        if not checkpoints:
            if not _quiet_mode:
                if server or campaign:
                    filters = []
                    if server:
                        filters.append(f"server='{server}'")
                    if campaign:
                        filters.append(f"campaign='{campaign}'")
                    console.print(
                        f"[yellow]No checkpoints found matching {' and '.join(filters)}[/yellow]"
                    )
                else:
                    console.print("[yellow]No checkpoints found[/yellow]")
            return

        # Quiet mode: just print filenames with numbers
        if _quiet_mode:
            for idx, cp in enumerate(checkpoints, start=1):
                print(f"{idx}. {cp['filename']}")
            return

        # Normal mode: display Rich table
        from rich.table import Table

        table = Table(title="Checkpoints", show_header=True, header_style="bold cyan")
        table.add_column("#", style="dim", justify="right", width=4)
        table.add_column("Filename", style="white", no_wrap=True)
        table.add_column("Campaign", style="cyan")
        table.add_column("Server", style="green")
        table.add_column("Created", style="yellow")
        table.add_column("Size", style="magenta", justify="right")
        table.add_column("Name", style="blue")
        table.add_column("Comment", style="dim")

        # Add rows for each checkpoint
        for idx, cp in enumerate(checkpoints, start=1):
            # Format timestamp for human readability (remove microseconds)
            timestamp_str = cp["timestamp"]
            # "2024-02-14T10:30:00.123456" -> "2024-02-14 10:30:00"
            if "." in timestamp_str:
                timestamp_str = timestamp_str.split(".")[0]
            timestamp_display = timestamp_str.replace("T", " ")

            # Get optional name and comment
            name_display = cp.get("name") or ""
            comment_display = cp.get("comment") or ""

            table.add_row(
                str(idx),
                cp["filename"],
                cp["campaign"],
                cp["server"],
                timestamp_display,
                cp["size_human"],
                name_display,
                comment_display,
            )

        console.print(table)
        console.print(f"\n[cyan]Total:[/cyan] {len(checkpoints)} checkpoint(s)")

    except FileNotFoundError as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1) from e
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1) from e


@app.command("delete")
def delete_command(
    checkpoint_file: Annotated[
        Optional[str],  # noqa: UP007 - Typer requires Optional
        typer.Argument(
            help="Checkpoint to delete: filename, number, or selection (e.g., '1', '1,3', '1-3'). Omit for interactive mode."
        ),
    ] = None,
    force: Annotated[
        bool,
        typer.Option("--force", "-f", help="Delete without confirmation"),
    ] = False,
) -> None:
    """Delete a checkpoint file from storage.

    Validates that the file is a valid checkpoint before deletion. By default,
    prompts for confirmation showing checkpoint metadata. Use --force to skip
    confirmation. In interactive mode (no checkpoint file specified), displays
    available checkpoints and prompts for selection.

    The checkpoint can be specified as:
    - A filename: 'afghanistan_checkpoint.zip'
    - A number from the list: '1' (deletes the first checkpoint)
    - Multiple selections: '1,3,5' or '1-3' (deletes multiple checkpoints)
    - Omitted for interactive selection

    Args:
        checkpoint_file: Optional checkpoint to delete (filename, number, or selection)
        force: If True, delete immediately without confirmation

    Examples:
        # Delete by number
        foothold-checkpoint delete 1

        # Delete multiple checkpoints
        foothold-checkpoint delete 1,3,5 --force

        # Delete with confirmation by filename
        foothold-checkpoint delete afghanistan_checkpoint.zip

        # Force delete without confirmation
        foothold-checkpoint delete checkpoint.zip --force

        # Interactive mode
        foothold-checkpoint delete

        # Quiet mode (automatic force, no prompts)
        foothold-checkpoint --quiet delete 1
    """
    import json
    import zipfile

    try:
        # Load configuration
        config_file = _config_path if _config_path else Path("config.yaml")
        config = load_config(config_file)

        # Step 1: Get checkpoint file (from argument or interactive selection)
        if checkpoint_file:
            # Check if checkpoint_file is a numeric selection (e.g., "1", "1,3", "1-3")
            if is_numeric_selection(checkpoint_file):
                # Resolve numeric selection by listing checkpoints
                checkpoints = list_checkpoints(config.checkpoints_dir)

                if not checkpoints:
                    console.print("[yellow]No checkpoints found[/yellow]")
                    raise typer.Exit(1)

                try:
                    selected_indices = parse_selection(checkpoint_file, len(checkpoints))
                except ValueError as e:
                    console.print(f"[red]Error:[/red] Invalid checkpoint selection: {e}")
                    raise typer.Exit(1) from e

                # Build list of checkpoint paths from indices
                checkpoint_paths = [
                    Path(config.checkpoints_dir) / checkpoints[idx - 1]["filename"]
                    for idx in selected_indices
                ]

                # Show what was selected (helpful feedback)
                if not _quiet_mode:
                    console.print("[cyan]Selected checkpoint(s) for deletion:[/cyan]")
                    for idx in selected_indices:
                        console.print(f"  {idx}. {checkpoints[idx - 1]['filename']}")
            else:
                # Treat as filename (existing behavior)
                checkpoint_paths = [Path(config.checkpoints_dir) / checkpoint_file]
        else:
            # Interactive mode: list checkpoints and prompt for selection
            checkpoints = list_checkpoints(config.checkpoints_dir)

            if not checkpoints:
                console.print("[yellow]No checkpoints found[/yellow]")
                raise typer.Exit(1)

            # Display numbered list
            if not _quiet_mode:
                console.print("\n[cyan]Available checkpoints:[/cyan]")
                for idx, cp in enumerate(checkpoints, 1):
                    timestamp = cp["timestamp"].replace("T", " ")

                    # Build display string with optional name/comment
                    display_parts = [
                        f"  {idx}. [white]{cp['filename']}[/white] -",
                        f"[cyan]{cp['campaign']}[/cyan] on",
                        f"[green]{cp['server']}[/green]",
                        f"[yellow]({timestamp})[/yellow]",
                    ]

                    # Add name if present
                    if cp.get("name"):
                        display_parts.insert(-1, f"[blue]'{cp['name']}'[/blue]")

                    # Add comment if present
                    if cp.get("comment"):
                        display_parts.append(f"[dim]- {cp['comment']}[/dim]")

                    console.print(" ".join(display_parts))

            # Prompt for selection (supports multiple: "1,3,5" or "1-3")
            console.print(
                "\n[dim]Tip: You can select multiple checkpoints (e.g., '1,3,5' or '1-3')[/dim]"
            )
            selection_str = Prompt.ask("\nSelect checkpoint number(s)", default="1")

            try:
                selected_indices = parse_selection(selection_str, len(checkpoints))
            except ValueError as e:
                console.print(f"[red]Error:[/red] {e}")
                raise typer.Exit(1) from e

            # Build list of checkpoint paths
            checkpoint_paths = [
                Path(config.checkpoints_dir) / checkpoints[idx - 1]["filename"]
                for idx in selected_indices
            ]

        # Step 2: Delete checkpoints
        deleted_count = 0
        cancelled_count = 0

        for checkpoint_path in checkpoint_paths:
            # Read metadata for display (before deletion)
            try:
                with zipfile.ZipFile(checkpoint_path, "r") as zf:
                    metadata_content = zf.read("metadata.json")
                    metadata = json.loads(metadata_content)
            except (FileNotFoundError, zipfile.BadZipFile, KeyError):
                # If we can't read metadata, proceed anyway (delete_checkpoint will validate)
                metadata = None

            # Step 3: Delete checkpoint with optional confirmation
            # Quiet mode acts like force mode (no prompts)
            use_force = force or _quiet_mode

            if use_force:
                # Force mode: no confirmation needed
                result = delete_checkpoint(checkpoint_path, force=True, confirm_callback=None)
                if result:
                    deleted_count += 1
            else:
                # Interactive mode: display metadata and prompt for confirmation
                if len(checkpoint_paths) > 1:
                    console.print(
                        f"\n[cyan]Checkpoint {deleted_count + cancelled_count + 1}/{len(checkpoint_paths)}:[/cyan]"
                    )

                if metadata:
                    console.print("\n[yellow]About to delete checkpoint:[/yellow]")
                    console.print(f"  Filename: [white]{checkpoint_path.name}[/white]")
                    console.print(
                        f"  Campaign: [cyan]{metadata.get('campaign_name', 'Unknown')}[/cyan]"
                    )
                    console.print(
                        f"  Server: [green]{metadata.get('server_name', 'Unknown')}[/green]"
                    )
                    console.print(
                        f"  Created: [yellow]{metadata.get('created_at', 'Unknown')}[/yellow]"
                    )

                    # Display name if present
                    if metadata.get("name"):
                        console.print(f"  Name: [blue]{metadata['name']}[/blue]")

                    # Display comment if present
                    if metadata.get("comment"):
                        console.print(f"  Comment: [white]{metadata['comment']}[/white]")

                # Create confirmation callback
                def confirm(meta: dict) -> bool:  # noqa: ARG001 - callback signature required
                    """Prompt user for deletion confirmation."""
                    response = Prompt.ask(
                        "\n[yellow]Delete this checkpoint?[/yellow]",
                        choices=["y", "n"],
                        default="n",
                    )
                    return response.lower() == "y"

                result = delete_checkpoint(checkpoint_path, force=False, confirm_callback=confirm)

                if result is None:
                    # User cancelled
                    cancelled_count += 1
                else:
                    deleted_count += 1

        # Step 4: Display final result
        if not _quiet_mode:
            if deleted_count > 0:
                console.print(f"\n[green]✓ Success![/green] Deleted {deleted_count} checkpoint(s)")
            if cancelled_count > 0:
                console.print(f"[yellow]{cancelled_count} deletion(s) cancelled[/yellow]")
        else:
            # In quiet mode, print deleted filenames
            if deleted_count > 0:
                for cp_path in checkpoint_paths:
                    if not cp_path.exists():  # File was deleted
                        print(cp_path.name)

    except FileNotFoundError as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1) from e
    except ValueError as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1) from e
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1) from e


@app.command("import")
def import_command(
    directory: Annotated[
        Optional[str],  # noqa: UP007 - Typer requires Optional
        typer.Argument(help="Source directory containing campaign files to import"),
    ] = None,
    server: Annotated[
        Optional[str],  # noqa: UP007 - Typer requires Optional
        typer.Option("--server", "-s", help="Target server name for metadata"),
    ] = None,
    campaign: Annotated[
        Optional[str],  # noqa: UP007 - Typer requires Optional
        typer.Option("--campaign", "-c", help="Campaign name to import"),
    ] = None,
    name: Annotated[
        Optional[str],  # noqa: UP007 - Typer requires Optional
        typer.Option("--name", "-n", help="Optional user-friendly name for checkpoint"),
    ] = None,
    comment: Annotated[
        Optional[str],  # noqa: UP007 - Typer requires Optional
        typer.Option("--comment", help="Optional comment describing the checkpoint"),
    ] = None,
) -> None:
    """Import campaign files from a directory and create a checkpoint.

    Scans the source directory for Foothold campaign files, creates a checkpoint
    ZIP archive with proper metadata. Can auto-detect campaigns or prompt for
    selection when multiple campaigns are found.

    Args:
        directory: Source directory path containing campaign files
        server: Server name for checkpoint metadata
        campaign: Campaign name to import (auto-detected if omitted)
        name: Optional user-friendly name
        comment: Optional comment

    Examples:
        # Import with all metadata
        foothold-checkpoint import /path/to/backup --server prod-1 --campaign afghanistan

        # Auto-detect campaign and prompt for server
        foothold-checkpoint import /path/to/backup

        # With optional metadata
        foothold-checkpoint import /backup --server prod-1 --campaign afghan --name "Manual Backup"

        # Quiet mode (no prompts, auto-confirms)
        foothold-checkpoint --quiet import /backup --server prod-1 --campaign afghan
    """
    try:
        # Load configuration
        config_file = _config_path if _config_path else Path("config.yaml")
        config = load_config(config_file)

        # Step 1: Get source directory (from argument or could be prompted)
        if not directory:
            console.print("[red]Error:[/red] Source directory is required")
            raise typer.Exit(1)

        source_dir = Path(directory)
        if not source_dir.exists():
            console.print(f"[red]Error:[/red] Source directory not found: {source_dir}")
            raise typer.Exit(1)

        if not source_dir.is_dir():
            console.print(f"[red]Error:[/red] Not a directory: {source_dir}")
            raise typer.Exit(1)

        # Step 2: Detect campaigns in source directory
        all_files = list(source_dir.iterdir())
        filenames = [f.name for f in all_files if f.is_file()]
        campaigns_found = group_campaign_files(filenames)

        if not campaigns_found:
            console.print(f"[red]Error:[/red] No campaign files found in {source_dir}")
            raise typer.Exit(1)

        # Step 3: Get campaign name (from flag, auto-detect, or prompt)
        if campaign:
            # User specified campaign name
            campaign_name = campaign
            # Validate it exists
            if campaign_name not in campaigns_found:
                # Try case-insensitive match
                campaign_lower = campaign_name.lower()
                matching = [c for c in campaigns_found if c.lower() == campaign_lower]
                if matching:
                    campaign_name = matching[0]
                else:
                    available = ", ".join(campaigns_found.keys())
                    console.print(
                        f"[red]Error:[/red] Campaign '{campaign}' not found. "
                        f"Available: {available}"
                    )
                    raise typer.Exit(1)
        elif len(campaigns_found) == 1:
            # Auto-detect single campaign
            campaign_name = list(campaigns_found.keys())[0]
            if not _quiet_mode:
                console.print(f"[cyan]Auto-detected campaign:[/cyan] {campaign_name}")
        else:
            # Multiple campaigns: prompt for selection
            if not _quiet_mode:
                console.print("\n[cyan]Multiple campaigns found:[/cyan]")
                for idx, camp in enumerate(campaigns_found.keys(), 1):
                    console.print(f"  {idx}. [white]{camp}[/white]")

            choices = [str(i) for i in range(1, len(campaigns_found) + 1)]
            selection = Prompt.ask("\nSelect campaign number", choices=choices, default="1")
            selected_idx = int(selection) - 1
            campaign_name = list(campaigns_found.keys())[selected_idx]

        # Step 4: Get server name (from flag or prompt)
        if not server:
            # Prompt for server
            available_servers = list(config.servers.keys())
            if not available_servers:
                console.print("[red]Error:[/red] No servers configured")
                raise typer.Exit(1)

            if not _quiet_mode:
                console.print("\n[cyan]Available servers:[/cyan]")
                for idx, s in enumerate(available_servers, 1):
                    console.print(f"  {s} ({idx})")

            # Accept both number and server name (validate manually)
            while True:
                selection = Prompt.ask("\nSelect target server", default="1")
                if selection.isdigit():
                    idx = int(selection)
                    if 1 <= idx <= len(available_servers):
                        server_name = available_servers[idx - 1]
                        break
                elif selection in available_servers:
                    server_name = selection
                    break
                else:
                    console.print(f"[red]Invalid selection:[/red] '{selection}'")
                    console.print(
                        f"Please enter a number (1-{len(available_servers)}) or a server name"
                    )
        else:
            server_name = server
            # Validate server exists
            if server_name not in config.servers:
                available = ", ".join(config.servers.keys())
                console.print(
                    f"[red]Error:[/red] Server '{server_name}' not found. "
                    f"Available servers: {available}"
                )
                raise typer.Exit(1)

        # Step 5: Display summary and confirm (unless quiet mode)
        if not _quiet_mode:
            console.print("\n[yellow]Import Summary:[/yellow]")
            console.print(f"  Source: [white]{source_dir}[/white]")
            console.print(f"  Campaign: [cyan]{campaign_name}[/cyan]")
            console.print(f"  Server: [green]{server_name}[/green]")
            if name:
                console.print(f"  Name: [blue]{name}[/blue]")
            if comment:
                console.print(f"  Comment: [white]{comment}[/white]")

            confirm = Prompt.ask(
                "\n[yellow]Proceed with import?[/yellow]", choices=["y", "n"], default="y"
            )
            if confirm.lower() != "y":
                console.print("[yellow]Import cancelled[/yellow]")
                return

        # Step 6: Perform import
        result = import_checkpoint(
            source_dir=source_dir,
            campaign_name=campaign_name,
            server_name=server_name,
            output_dir=config.checkpoints_dir,
            name=name,
            comment=comment,
            return_warnings=True,
        )

        # Handle result (could be path or tuple with warnings)
        if isinstance(result, tuple):
            checkpoint_path, warnings = result
        else:
            checkpoint_path = result
            warnings = []

        # Step 7: Display results
        if _quiet_mode:
            # Quiet mode: just print checkpoint path
            print(checkpoint_path.name)
        else:
            console.print(
                f"\n[green]✓ Success![/green] Imported checkpoint: "
                f"[cyan]{checkpoint_path.name}[/cyan]"
            )

            # Display warnings if any
            if warnings:
                console.print(f"\n[yellow]Warnings ({len(warnings)}):[/yellow]")
                for warning in warnings:
                    console.print(f"  [yellow]⚠[/yellow] {warning}")

    except FileNotFoundError as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1) from e
    except ValueError as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1) from e
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1) from e


def main() -> None:
    """Entry point for the CLI application.

    This function is called when the foothold-checkpoint command is executed.
    It runs the Typer app which handles all command routing and execution.
    """
    app()


if __name__ == "__main__":
    main()

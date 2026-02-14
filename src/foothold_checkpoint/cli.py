"""Command-line interface for foothold-checkpoint tool."""

import signal
import sys
from pathlib import Path
from types import FrameType
from typing import Annotated, Optional  # noqa: UP035 - Required for Typer compatibility

import typer
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.prompt import Prompt

from foothold_checkpoint.core.campaign import detect_campaigns, group_campaign_files
from foothold_checkpoint.core.checkpoint import create_checkpoint
from foothold_checkpoint.core.config import load_config
from foothold_checkpoint.core.storage import (
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
                for srv in available_servers:
                    console.print(f"  - {srv}")

            server = Prompt.ask("\nSelect server", choices=available_servers)

        # Validate server exists
        if server not in config.servers:
            available = ", ".join(config.servers.keys())
            console.print(f"[red]Error:[/red] Server '{server}' not found in configuration")
            console.print(f"Available servers: {available}")
            raise typer.Exit(1)

        server_config = config.servers[server]
        mission_dir = Path(server_config.mission_directory)

        # Validate mission directory exists
        if not mission_dir.exists():
            console.print(f"[red]Error:[/red] Mission directory does not exist: {mission_dir}")
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
            # Save specific campaign
            if campaign not in campaigns:
                available = ", ".join(campaigns.keys())
                console.print(f"[red]Error:[/red] Campaign '{campaign}' not found in mission directory")
                console.print(f"Available campaigns: {available}")
                raise typer.Exit(1)
            campaigns_to_save = [campaign]
        else:
            # Prompt for campaign selection
            if not _quiet_mode:
                console.print("\n[cyan]Detected campaigns:[/cyan]")
                for camp in campaigns:
                    file_count = len(campaigns[camp])
                    console.print(f"  - {camp} ({file_count} file{'s' if file_count > 1 else ''})")

            campaign_choices = list(campaigns.keys()) + ["all"]
            selected = Prompt.ask("\nSelect campaign (or 'all')", choices=campaign_choices)

            campaigns_to_save = list(campaigns.keys()) if selected == "all" else [selected]

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
            checkpoint_name = Prompt.ask("Checkpoint name (optional, press Enter to skip)", default="")
            if checkpoint_name == "":
                checkpoint_name = None

        if checkpoint_comment is None and not _quiet_mode and not save_all and in_interactive_mode:
            checkpoint_comment = Prompt.ask("Checkpoint comment (optional, press Enter to skip)", default="")
            if checkpoint_comment == "":
                checkpoint_comment = None

        # Step 5: Create checkpoints
        checkpoints_dir = Path(config.checkpoints_directory)
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
                ) as progress:
                    task = progress.add_task(f"Creating checkpoint for {camp_name}...", total=None)

                    def update_progress(message: str, current: int, total: int) -> None:
                        progress.update(task, description=f"{message} ({current}/{total})")  # noqa: B023

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
            console.print(f"\n[green]✓ Success![/green] Created {len(created_checkpoints)} checkpoint(s):")
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
            help="Path to checkpoint ZIP file to restore (or omit to select interactively)"
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

    If no checkpoint file is provided, lists available checkpoints for selection.
    If --server is not provided, prompts for server selection.

    The restore process verifies file integrity, excludes Foothold_Ranks.lua by
    default, and prompts for confirmation if files will be overwritten.

    Examples:

        # Restore specific checkpoint to a server
        $ foothold-checkpoint restore afghanistan_2024-02-14.zip --server test-server

        # Restore with ranks file included
        $ foothold-checkpoint restore checkpoint.zip --server prod-1 --restore-ranks

        # Interactive mode (select checkpoint and server)
        $ foothold-checkpoint restore
    """
    try:
        # Step 1: Load configuration
        config_file = _config_path if _config_path else Path("config.yaml")
        config = load_config(config_file)

        # Step 2: Get checkpoint file
        checkpoint_path: Path
        if checkpoint_file:
            checkpoint_path = Path(checkpoint_file)
            # Validate checkpoint file exists
            if not checkpoint_path.exists():
                console.print(f"[red]Error:[/red] Checkpoint file not found: {checkpoint_path}")
                raise typer.Exit(1)
        else:
            # Interactive mode: list and prompt for checkpoint selection
            if not _quiet_mode:
                console.print("[cyan]Available checkpoints:[/cyan]")

            # List all checkpoints
            checkpoints = list_checkpoints(config.checkpoints_directory)

            if not checkpoints:
                console.print("[red]Error:[/red] No checkpoints found in checkpoint directory")
                raise typer.Exit(1)

            # Display checkpoints with numbering
            if not _quiet_mode:
                for idx, cp in enumerate(checkpoints, start=1):
                    console.print(
                        f"  {idx}. {cp['filename']} "
                        f"[dim](Campaign: {cp['campaign']}, Server: {cp['server']}, "
                        f"Created: {cp['timestamp']})[/dim]"
                    )

            # Prompt for selection
            selection = Prompt.ask(
                "Select checkpoint number",
                choices=[str(i) for i in range(1, len(checkpoints) + 1)]
            )

            selected_index = int(selection) - 1
            # Construct full path from checkpoint directory and filename
            checkpoint_path = config.checkpoints_directory / checkpoints[selected_index]["filename"]

        # Step 3: Get target server
        if server is None:
            # Prompt for server selection
            available_servers = list(config.servers.keys())
            if not available_servers:
                console.print("[red]Error:[/red] No servers configured")
                raise typer.Exit(1)

            if not _quiet_mode:
                console.print(f"[cyan]Available servers:[/cyan] {', '.join(available_servers)}")

            server = Prompt.ask(
                "Select target server",
                choices=available_servers
            )

        # Validate server exists in config
        if server not in config.servers:
            console.print(
                f"[red]Error:[/red] Server '{server}' not found in configuration.\n"
                f"Available servers: {', '.join(config.servers.keys())}"
            )
            raise typer.Exit(1)

        # Get target directory from server config
        target_dir = config.servers[server].mission_directory

        # Step 4: Restore checkpoint with progress display
        if not _quiet_mode:
            console.print(f"\n[cyan]Restoring checkpoint to server:[/cyan] {server}")
            console.print(f"[cyan]Target directory:[/cyan] {target_dir}")
            console.print(f"[cyan]Include ranks file:[/cyan] {'Yes' if restore_ranks else 'No'}\n")

            # Progress display with Rich
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console
            ) as progress:
                task = progress.add_task("Restoring checkpoint...", total=None)

                def update_progress(message: str, current: int, total: int) -> None:  # noqa: B023 - task variable is safely captured
                    """Update progress display with current status."""
                    progress.update(task, description=f"{message} ({current}/{total})")

                # Restore with progress callback
                restored_files = restore_checkpoint(
                    checkpoint_path=checkpoint_path,
                    target_dir=target_dir,
                    restore_ranks=restore_ranks,
                    progress_callback=update_progress
                )
        else:
            # Quiet mode: no progress display
            restored_files = restore_checkpoint(
                checkpoint_path=checkpoint_path,
                target_dir=target_dir,
                restore_ranks=restore_ranks,
                progress_callback=None
            )

        # Step 5: Display success message
        if not _quiet_mode:
            console.print(
                f"\n[green]✓ Success![/green] Restored {len(restored_files)} file(s) to {server}"
            )
        else:
            # In quiet mode, just print the paths
            for file_path in restored_files:
                console.print(str(file_path))

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
        str | None,
        typer.Option("--server", "-s", help="Filter checkpoints by server name"),
    ] = None,
    campaign: Annotated[
        str | None,
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
            config.checkpoints_directory,
            server_filter=server,
            campaign_filter=campaign
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
                    console.print(f"[yellow]No checkpoints found matching {' and '.join(filters)}[/yellow]")
                else:
                    console.print("[yellow]No checkpoints found[/yellow]")
            return

        # Quiet mode: just print filenames
        if _quiet_mode:
            for cp in checkpoints:
                print(cp["filename"])
            return

        # Normal mode: display Rich table
        from rich.table import Table

        table = Table(title="Checkpoints", show_header=True, header_style="bold cyan")
        table.add_column("Filename", style="white", no_wrap=True)
        table.add_column("Campaign", style="cyan")
        table.add_column("Server", style="green")
        table.add_column("Created", style="yellow")
        table.add_column("Size", style="magenta", justify="right")
        table.add_column("Name", style="blue")

        # Add rows for each checkpoint
        for cp in checkpoints:
            # Format timestamp for human readability
            timestamp_str = cp["timestamp"]
            # Convert ISO timestamp to more readable format
            # "2024-02-14T10:30:00" -> "2024-02-14 10:30:00"
            timestamp_display = timestamp_str.replace("T", " ")

            # Get optional name
            name_display = cp.get("name") or ""

            table.add_row(
                cp["filename"],
                cp["campaign"],
                cp["server"],
                timestamp_display,
                cp["size_human"],
                name_display
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
        str | None,
        typer.Argument(help="Checkpoint file to delete (optional if interactive)"),
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

    Args:
        checkpoint_file: Optional checkpoint filename to delete
        force: If True, delete immediately without confirmation

    Examples:
        # Delete with confirmation
        foothold-checkpoint delete afghanistan_2024-02-14.zip

        # Force delete without confirmation
        foothold-checkpoint delete checkpoint.zip --force

        # Interactive mode
        foothold-checkpoint delete

        # Quiet mode (automatic force, no prompts)
        foothold-checkpoint --quiet delete checkpoint.zip
    """
    import json
    import zipfile

    try:
        # Load configuration
        config_file = _config_path if _config_path else Path("config.yaml")
        config = load_config(config_file)

        # Step 1: Get checkpoint file (from argument or interactive selection)
        if checkpoint_file:
            checkpoint_path = config.checkpoints_directory / checkpoint_file
        else:
            # Interactive mode: list checkpoints and prompt for selection
            checkpoints = list_checkpoints(config.checkpoints_directory)

            if not checkpoints:
                console.print("[yellow]No checkpoints found[/yellow]")
                raise typer.Exit(1)

            # Display numbered list
            if not _quiet_mode:
                console.print("\n[cyan]Available checkpoints:[/cyan]")
                for idx, cp in enumerate(checkpoints, 1):
                    timestamp = cp["timestamp"].replace("T", " ")
                    console.print(
                        f"  {idx}. [white]{cp['filename']}[/white] - "
                        f"[cyan]{cp['campaign']}[/cyan] on "
                        f"[green]{cp['server']}[/green] "
                        f"[yellow]({timestamp})[/yellow]"
                    )

            # Prompt for selection
            choices = [str(i) for i in range(1, len(checkpoints) + 1)]
            selection = Prompt.ask(
                "\nSelect checkpoint number",
                choices=choices,
                default="1"
            )
            selected_idx = int(selection) - 1
            checkpoint_path = config.checkpoints_directory / checkpoints[selected_idx]["filename"]

        # Step 2: Read metadata for display (before deletion)
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
            result = delete_checkpoint(
                checkpoint_path,
                force=True,
                confirm_callback=None
            )
        else:
            # Interactive mode: display metadata and prompt for confirmation
            if metadata:
                console.print("\n[yellow]About to delete checkpoint:[/yellow]")
                console.print(f"  Campaign: [cyan]{metadata.get('campaign_name', 'Unknown')}[/cyan]")
                console.print(f"  Server: [green]{metadata.get('server_name', 'Unknown')}[/green]")
                console.print(f"  Created: [yellow]{metadata.get('created_at', 'Unknown')}[/yellow]")

            # Create confirmation callback
            def confirm(meta: dict) -> bool:  # noqa: ARG001 - callback signature required
                """Prompt user for deletion confirmation."""
                response = Prompt.ask(
                    "\n[yellow]Delete this checkpoint?[/yellow]",
                    choices=["y", "n"],
                    default="n"
                )
                return response.lower() == "y"

            result = delete_checkpoint(
                checkpoint_path,
                force=False,
                confirm_callback=confirm
            )

        # Step 4: Display result
        if result is None:
            # User cancelled
            if not _quiet_mode:
                console.print("[yellow]Deletion cancelled[/yellow]")
        else:
            # Successfully deleted
            if _quiet_mode:
                # In quiet mode, just print the deleted filename
                print(checkpoint_path.name)
            else:
                console.print(
                    f"[green]✓ Success![/green] Deleted checkpoint "
                    f"[cyan]{result['campaign_name']}[/cyan] from "
                    f"[green]{result['server_name']}[/green]"
                )

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
        str | None,
        typer.Argument(help="Source directory containing campaign files to import"),
    ] = None,
    server: Annotated[
        str | None,
        typer.Option("--server", "-s", help="Target server name for metadata"),
    ] = None,
    campaign: Annotated[
        str | None,
        typer.Option("--campaign", "-c", help="Campaign name to import"),
    ] = None,
    name: Annotated[
        str | None,
        typer.Option("--name", "-n", help="Optional user-friendly name for checkpoint"),
    ] = None,
    comment: Annotated[
        str | None,
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
            selection = Prompt.ask(
                "\nSelect campaign number",
                choices=choices,
                default="1"
            )
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
                for s in available_servers:
                    console.print(f"  - {s}")

            server_name = Prompt.ask(
                "\nSelect target server",
                choices=available_servers,
                default=available_servers[0]
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
                "\n[yellow]Proceed with import?[/yellow]",
                choices=["y", "n"],
                default="y"
            )
            if confirm.lower() != "y":
                console.print("[yellow]Import cancelled[/yellow]")
                return

        # Step 6: Perform import
        result = import_checkpoint(
            source_dir=source_dir,
            campaign_name=campaign_name,
            server_name=server_name,
            output_dir=config.checkpoints_directory,
            name=name,
            comment=comment,
            return_warnings=True
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

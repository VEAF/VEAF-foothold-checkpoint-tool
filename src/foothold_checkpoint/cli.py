"""Command-line interface for foothold-checkpoint tool."""

import signal
import sys
from pathlib import Path
from types import FrameType
from typing import Annotated, Optional  # noqa: UP035 - Required for Typer compatibility

import typer
from rich.console import Console

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
    config: Annotated[
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

    # Handle quiet flag
    if quiet:
        global _quiet_mode
        _quiet_mode = True


def main() -> None:
    """Entry point for the CLI application.

    This function is called when the foothold-checkpoint command is executed.
    It runs the Typer app which handles all command routing and execution.
    """
    app()


if __name__ == "__main__":
    main()

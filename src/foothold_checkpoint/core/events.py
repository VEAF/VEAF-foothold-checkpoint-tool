"""Event hooks system for checkpoint operations.

This module provides EventHooks dataclass for optional callbacks that enable
external systems (like Discord) to be notified of checkpoint operation events.

The hook system is completely optional - when hooks=None, operations proceed
normally without any callbacks. This enables the core library to work in both
CLI mode (no hooks) and plugin mode (Discord notifications).

Example:
    # CLI mode - no hooks
    checkpoint = await save_checkpoint(campaign, server_path, config, hooks=None)

    # Plugin mode - with Discord hooks
    hooks = EventHooks(
        on_save_start=lambda c: send_message(f"Saving {c}..."),
        on_save_complete=lambda p: send_message(f"Saved to {p}")
    )
    checkpoint = await save_checkpoint(campaign, server_path, config, hooks=hooks)
"""

import logging
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class EventHooks:
    """Optional async callbacks for checkpoint operation events.

    All hooks are optional. When a hook is None, it is simply skipped.
    Hooks are async functions that should not raise exceptions - if they do,
    the exception is logged and the operation continues.

    Attributes:
        on_save_start: Called when checkpoint save begins
        on_save_progress: Called during save with (current, total) progress
        on_save_complete: Called when save completes successfully with checkpoint path
        on_restore_start: Called when checkpoint restore begins
        on_restore_progress: Called during restore with (current_file, total_files)
        on_restore_complete: Called when restore completes with list of restored files
        on_delete_start: Called when checkpoint delete begins
        on_delete_complete: Called when delete completes with checkpoint name
        on_backup_complete: Called when auto-backup completes with backup path
        on_error: Called when any operation fails with exception
    """

    # Save operation hooks
    on_save_start: Callable[[str], Awaitable[None]] | None = None
    on_save_progress: Callable[[int, int], Awaitable[None]] | None = None
    on_save_complete: Callable[[Any], Awaitable[None]] | None = None  # Path

    # Restore operation hooks
    on_restore_start: Callable[[str, str], Awaitable[None]] | None = (
        None  # checkpoint_name, campaign
    )
    on_restore_progress: Callable[[int, int], Awaitable[None]] | None = None
    on_restore_complete: Callable[[list[str]], Awaitable[None]] | None = None  # restored_files

    # Delete operation hooks
    on_delete_start: Callable[[str], Awaitable[None]] | None = None  # checkpoint_name
    on_delete_complete: Callable[[str], Awaitable[None]] | None = None  # checkpoint_name

    # Auto-backup hook
    on_backup_complete: Callable[[Any], Awaitable[None]] | None = None  # backup_path (Path)

    # Error hook (called for any operation failure)
    on_error: Callable[[Exception], Awaitable[None]] | None = None


async def safe_invoke_hook(
    hook: Callable[..., Awaitable[None]] | None,
    *args: Any,
    hook_name: str = "unknown",
) -> None:
    """Safely invoke an async hook callback, catching and logging any exceptions.

    This wrapper ensures that hook failures never cause checkpoint operations to fail.
    If a hook raises an exception, it is logged and the operation continues normally.

    Args:
        hook: The async hook function to invoke (or None to skip)
        *args: Arguments to pass to the hook function
        hook_name: Name of the hook for logging purposes

    Example:
        await safe_invoke_hook(hooks.on_save_start, campaign, hook_name="on_save_start")
    """
    if hook is None:
        return

    try:
        await hook(*args)
    except Exception as e:
        # Log the error but don't re-raise - hooks should never fail operations
        logger.error(
            f"Hook '{hook_name}' raised exception (operation continues): {e}",
            exc_info=True,
        )

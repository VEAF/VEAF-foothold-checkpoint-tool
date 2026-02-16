"""Event listener for DCS events (minimal implementation).

This module provides the EventListener class for potential future integration
with DCS mission events. For v2.0.0, this is a minimal stub since checkpoint
operations are triggered via Discord commands, not DCS events.
"""


class FootholdEventListener:
    """Event listener for DCS mission events.

    Future versions may implement:
    - Automatic checkpoints on mission end
    - Checkpoint on server shutdown
    - Integration with mission scripting
    """

    def __init__(self) -> None:
        """Initialize the event listener."""
        pass

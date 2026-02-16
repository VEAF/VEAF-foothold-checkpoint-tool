"""Event listener for DCS events.

This module provides the EventListener for potential future integration
with DCS mission events. For v2.0.0, this is a minimal implementation since
checkpoint operations are primarily triggered via Discord commands.

Future versions may implement:
- Automatic checkpoints on mission end
- Checkpoint on server shutdown
- Integration with mission scripting
"""

from typing import TYPE_CHECKING

from core import EventListener

if TYPE_CHECKING:
    pass


class FootholdEventListener(EventListener["FootholdCheckpoint"]):
    """Event listener for DCS mission events.

    Inherits from DCSServerBot's EventListener base class, providing:
    - Access to plugin configuration via self.get_config(server)
    - Database connection pools (self.pool, self.apool)
    - Bot instance (self.bot)
    - Logger (self.log)
    - Event decorators (@event, @chat_command)

    Example future usage:
        @event(name="onMissionEnd")
        async def onMissionEnd(self, server: Server, data: dict) -> None:
            # Auto-save checkpoint when mission ends
            pass
    """

    # No custom initialization needed - EventListener.__init__ handles everything
    # All the infrastructure (self.plugin, self.bot, self.log, etc.) is provided by base class

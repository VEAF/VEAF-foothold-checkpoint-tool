"""DCSServerBot plugin package for foothold-checkpoint tool.

This package provides integration between the foothold-checkpoint CLI tool
and DCSServerBot, allowing automatic checkpoint management from the bot's
command interface.

Architecture Overview:
- DCSServerBot uses a plugin-based architecture where each plugin extends
  the bot with new commands and functionality
- Plugins register commands through the bot's command system
- This plugin wraps the foothold-checkpoint CLI tool to provide checkpoint
  management commands to server administrators

Integration Points:
- Commands are registered in the bot's command tree
- Configuration is loaded from the bot's config system
- Logging uses the bot's logging infrastructure
- Error handling follows bot conventions

For more information on DCSServerBot plugin architecture, see:
https://github.com/Special-K-s-Flightsim-Bots/DCSServerBot
"""

__version__ = "0.1.0"
__all__ = ["commands"]

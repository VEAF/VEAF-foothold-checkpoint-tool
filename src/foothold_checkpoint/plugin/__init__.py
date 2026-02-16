"""DCSServerBot plugin for Foothold Checkpoint management.

This package provides Discord-based checkpoint operations via slash commands,
integrating the Foothold Checkpoint Tool with DCSServerBot framework.
"""

from .version import __version__

__all__ = ["__version__"]


# DCSServerBot plugin entry point
# This function is called by DCSSB when loading the plugin
async def setup(bot):
    """Setup function called by DCSServerBot to load the plugin.

    Args:
        bot: DCSServerBot instance

    This imports the plugin class and registers it with the bot.
    The plugin uses DCSServerBot's Plugin base class for full integration.
    """
    from .plugin.commands import FootholdCheckpoint
    from .plugin.listener import FootholdEventListener

    # IMPORTANT: Pass explicit name to avoid DCSSB deriving wrong name from module path
    # Without this, DCSSB extracts "plugin" instead of "foothold-checkpoint"
    plugin = FootholdCheckpoint(bot, FootholdEventListener, name="foothold-checkpoint")

    # Add commands to the group
    plugin.checkpoint_group.add_command(plugin.save_command)
    plugin.checkpoint_group.add_command(plugin.restore_command)
    plugin.checkpoint_group.add_command(plugin.list_command)
    plugin.checkpoint_group.add_command(plugin.delete_command)

    # Add the command group to the bot's tree
    bot.tree.add_command(plugin.checkpoint_group)

    await bot.add_cog(plugin)

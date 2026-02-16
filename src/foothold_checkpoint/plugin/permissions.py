"""Permission management for Discord role-based access control."""

import discord


async def check_permission(
    interaction: discord.Interaction,
    config: dict[str, dict[str, list[str]]],
    operation: str
) -> bool:
    """Check if user has permission for the specified operation.
    
    Args:
        interaction: Discord interaction object with user and guild info
        config: Plugin configuration with permissions section
        operation: Operation name ('save', 'restore', 'list', 'delete')
        
    Returns:
        True if user has permission, False otherwise
        
    Example:
        >>> if not await check_permission(interaction, config, 'restore'):
        ...     await interaction.response.send_message(
        ...         "❌ You don't have permission to restore checkpoints.",
        ...         ephemeral=True
        ...     )
        ...     return
    """
    # Check for administrator override
    if interaction.user.guild_permissions.administrator:
        return True
    
    # Get permitted roles for operation
    permissions = config.get('permissions', {})
    allowed_roles = permissions.get(operation, [])
    
    # Check if user has any of the permitted roles
    user_roles = [role.name for role in interaction.user.roles]
    return any(role in allowed_roles for role in user_roles)


def format_permission_denied(operation: str, allowed_roles: list[str]) -> str:
    """Format permission denied error message.
    
    Args:
        operation: Operation name that was denied
        allowed_roles: List of roles that are permitted for this operation
        
    Returns:
        Formatted error message with required roles
        
    Example:
        >>> msg = format_permission_denied('restore', ['DCS Admin', 'Mission Designer'])
        >>> print(msg)
        ❌ You don't have permission to restore. Required roles: DCS Admin, Mission Designer
    """
    roles_str = ", ".join(allowed_roles) if allowed_roles else "None configured"
    return f"❌ You don't have permission to {operation}. Required roles: {roles_str}"

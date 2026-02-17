"""Discord UI components for interactive checkpoint management."""

from typing import Any

import discord
from discord import ui


class CheckpointMetadataModal(ui.Modal, title="Checkpoint Metadata"):
    """Modal for entering optional checkpoint name and comment."""

    def __init__(self):
        """Initialize the metadata modal."""
        super().__init__()
        self.checkpoint_name: str | None = None
        self.checkpoint_comment: str | None = None

    name_input = ui.TextInput(
        label="Name (optional)",
        placeholder="e.g., Pre-mission backup, After attack, etc.",
        required=False,
        max_length=100,
        style=discord.TextStyle.short,
    )

    comment_input = ui.TextInput(
        label="Comment (optional)",
        placeholder="Add any notes or description for this checkpoint...",
        required=False,
        max_length=500,
        style=discord.TextStyle.paragraph,
    )

    async def on_submit(self, interaction: discord.Interaction) -> None:
        """Handle modal submission.

        Args:
            interaction: Discord interaction from modal submission
        """
        # Store values (convert empty strings to None)
        self.checkpoint_name = self.name_input.value.strip() or None
        self.checkpoint_comment = self.comment_input.value.strip() or None

        # Acknowledge the submission (we'll update the message from the parent view)
        await interaction.response.defer()


class CampaignSelectView(ui.View):
    """Interactive view for selecting campaigns to save.

    Provides a dropdown menu with all available campaigns plus an "All campaigns" option,
    with Save and Cancel buttons to confirm or abort the selection.
    """

    def __init__(self, campaigns: dict[str, Any], timeout: float = 180.0):
        """Initialize the campaign selection view.

        Args:
            campaigns: Dictionary of campaign configs {campaign_name: CampaignConfig}
            timeout: View timeout in seconds (default: 3 minutes)
        """
        super().__init__(timeout=timeout)
        self.selected_campaigns: list[str] | None = None
        self.campaigns = campaigns
        self.metadata_modal: CheckpointMetadataModal | None = None

        # Create the dropdown
        options = [
            discord.SelectOption(
                label="📦 All Campaigns",
                value="__all__",
                description="Save checkpoints for all configured campaigns",
                emoji="📦",
            )
        ]

        # Add individual campaign options
        for campaign_name in sorted(campaigns.keys()):
            campaign = campaigns[campaign_name]
            display_name = campaign.display_name or campaign_name
            options.append(
                discord.SelectOption(
                    label=display_name,
                    value=campaign_name,
                    description=f"Save checkpoint for {display_name}",
                    emoji="📁",
                )
            )

        # Create select menu
        select = ui.Select(
            placeholder="Select campaign(s) to save...",
            min_values=1,
            max_values=min(len(options), 25),  # Discord limit is 25
            options=options,
        )
        select.callback = self.select_callback
        self.add_item(select)

        # Add Save button
        save_button = ui.Button(label="Save", style=discord.ButtonStyle.success, emoji="💾")
        save_button.callback = self.save_callback
        self.add_item(save_button)

        # Add Cancel button
        cancel_button = ui.Button(label="Cancel", style=discord.ButtonStyle.secondary, emoji="❌")
        cancel_button.callback = self.cancel_callback
        self.add_item(cancel_button)

    async def select_callback(self, interaction: discord.Interaction) -> None:
        """Handle campaign selection (updates selection without closing view).

        Args:
            interaction: Discord interaction from the select menu
        """
        # Get selected values
        selected = interaction.data["values"]  # type: ignore

        # Check if "All campaigns" was selected
        if "__all__" in selected:
            self.selected_campaigns = list(self.campaigns.keys())
            await interaction.response.edit_message(
                content=f"📁 **Selected: All {len(self.campaigns)} campaigns**\n\nClick **💾 Save** to create checkpoints or select different campaigns.",
                view=self,
            )
        else:
            self.selected_campaigns = selected
            campaign_names = ", ".join([self.campaigns[c].display_name or c for c in selected])
            await interaction.response.edit_message(
                content=f"📁 **Selected: {campaign_names}**\n\nClick **💾 Save** to create checkpoints or select different campaigns.",
                view=self,
            )

    async def save_callback(self, interaction: discord.Interaction) -> None:
        """Handle Save button click (shows metadata modal then proceeds).

        Args:
            interaction: Discord interaction from the button
        """
        if self.selected_campaigns is None:
            await interaction.response.send_message(
                "⚠️ Please select at least one campaign first.", ephemeral=True
            )
            return

        # Show modal for name and comment
        self.metadata_modal = CheckpointMetadataModal()
        await interaction.response.send_modal(self.metadata_modal)

        # Wait for modal submission
        await self.metadata_modal.wait()

        # The view will stop after modal submission is handled by the command
        self.stop()

    async def cancel_callback(self, interaction: discord.Interaction) -> None:
        """Handle Cancel button click (aborts checkpoint creation).

        Args:
            interaction: Discord interaction from the button
        """
        self.selected_campaigns = None
        await interaction.response.edit_message(
            content="❌ **Checkpoint creation cancelled.**", view=None
        )
        self.stop()

    async def on_timeout(self) -> None:
        """Handle view timeout."""
        self.selected_campaigns = None
        self.stop()


class CheckpointBrowserView(ui.View):
    """Interactive checkpoint browser with live details preview.

    Displays a dropdown to select checkpoints and updates the embed
    in real-time to show details of the selected checkpoint.
    """

    def __init__(
        self, checkpoints: list[dict[str, Any]], format_details_func, timeout: float = 300.0
    ):
        """Initialize the checkpoint browser view.

        Args:
            checkpoints: List of checkpoint dicts with metadata
            format_details_func: Function to format checkpoint details as embed
            timeout: View timeout in seconds (default: 5 minutes)
        """
        super().__init__(timeout=timeout)
        self.checkpoints = checkpoints
        self.format_details_func = format_details_func
        self.current_index = 0  # Default to first checkpoint

        # Create the dropdown (limited to 25 options by Discord)
        options = []
        separator_added = False

        for idx, cp in enumerate(checkpoints[:25]):  # Discord limit
            # Add separator before first auto-backup checkpoint
            if cp.get("is_auto_backup") and not separator_added:
                options.append(
                    discord.SelectOption(
                        label="─────────── AUTO-BACKUPS ───────────",
                        value="__separator__",
                        description="Automatic backups created before restore operations",
                        emoji="🔽",
                    )
                )
                separator_added = True

            filename = cp["filename"]
            campaign = cp.get("campaign", "unknown")

            # Build label with filename
            label = filename
            if len(label) > 100:  # Discord label limit
                label = f"{label[:97]}..."

            # Build description with campaign, date, size, and name/comment if present
            timestamp_str = cp.get("timestamp", "")
            if timestamp_str:
                # "2024-02-14T10:30:00" -> "02-14 10:30"
                date_part = timestamp_str[5:10] if len(timestamp_str) > 10 else ""
                time_part = timestamp_str[11:16] if len(timestamp_str) > 16 else ""
                display_time = f"{date_part} {time_part}"
            else:
                display_time = ""

            # Include name and/or comment if present
            extras = []
            if cp.get("name"):
                extras.append(f"[{cp['name']}]")
            if cp.get("comment"):
                comment = cp["comment"]
                if len(comment) > 30:
                    comment = f"{comment[:27]}..."
                extras.append(comment)

            extra_info = " - ".join(extras) if extras else ""

            # Build description: "campaign • date time • size • extras"
            description_parts = [campaign, display_time, cp.get("size_human", "")]
            if extra_info:
                description_parts.append(extra_info)

            description = " • ".join(filter(None, description_parts))
            if len(description) > 100:  # Discord description limit
                description = f"{description[:97]}..."

            options.append(
                discord.SelectOption(
                    label=label,
                    value=str(idx),  # Use index as value
                    description=description,
                )
            )

        if not options:
            # No checkpoints - add a dummy disabled option
            options.append(
                discord.SelectOption(
                    label="No checkpoints available",
                    value="__none__",
                    description="No checkpoints found",
                )
            )

        # Create select menu
        select = ui.Select(
            placeholder="Select a checkpoint to view details...",
            min_values=1,
            max_values=1,
            options=options,
        )
        select.callback = self.select_callback
        self.add_item(select)

    async def select_callback(self, interaction: discord.Interaction) -> None:
        """Handle checkpoint selection and update embed.

        Args:
            interaction: Discord interaction from the select menu
        """
        # Get selected index
        selected_value = interaction.data["values"][0]  # type: ignore

        if selected_value == "__none__":
            await interaction.response.edit_message(
                content="❌ No checkpoints available.", embed=None, view=None
            )
            self.stop()
            return

        if selected_value == "__separator__":
            # User clicked the separator - ignore and keep the view as is
            await interaction.response.defer()
            return

        # Update current index
        self.current_index = int(selected_value)

        # Get selected checkpoint
        selected_checkpoint = self.checkpoints[self.current_index]

        # Generate new embed for selected checkpoint
        embed = self.format_details_func(selected_checkpoint)

        # Update the message with new embed
        await interaction.response.edit_message(
            content=f"📦 **Checkpoint {self.current_index + 1}/{len(self.checkpoints)}** - Select from dropdown to view details:",
            embed=embed,
            view=self,
        )

    async def on_timeout(self) -> None:
        """Handle view timeout."""
        self.stop()


class CheckpointDeleteBrowserView(ui.View):
    """Interactive checkpoint browser for deletion with live details preview.

    Displays a dropdown to select checkpoints and updates the embed
    in real-time to show details of the selected checkpoint. Includes
    a Delete button to trigger deletion confirmation.
    """

    def __init__(
        self, checkpoints: list[dict[str, Any]], format_details_func, timeout: float = 300.0
    ):
        """Initialize the checkpoint browser view.

        Args:
            checkpoints: List of checkpoint dicts with metadata
            format_details_func: Function to format checkpoint details as embed
            timeout: View timeout in seconds (default: 5 minutes)
        """
        super().__init__(timeout=timeout)
        self.checkpoints = checkpoints
        self.format_details_func = format_details_func
        self.current_index = 0  # Default to first checkpoint
        self.delete_requested = False  # Flag to indicate delete button clicked

        # Create the dropdown (limited to 25 options by Discord)
        options = []
        separator_added = False

        for idx, cp in enumerate(checkpoints[:25]):  # Discord limit
            # Add separator before first auto-backup checkpoint
            if cp.get("is_auto_backup") and not separator_added:
                options.append(
                    discord.SelectOption(
                        label="─────────── AUTO-BACKUPS ───────────",
                        value="__separator__",
                        description="Automatic backups created before restore operations",
                        emoji="🔽",
                    )
                )
                separator_added = True

            filename = cp["filename"]
            campaign = cp.get("campaign", "unknown")

            # Build label with filename
            label = filename
            if len(label) > 100:  # Discord label limit
                label = f"{label[:97]}..."

            # Build description with campaign, date, size, and name/comment if present
            timestamp_str = cp.get("timestamp", "")
            if timestamp_str:
                # "2024-02-14T10:30:00" -> "02-14 10:30"
                date_part = timestamp_str[5:10] if len(timestamp_str) > 10 else ""
                time_part = timestamp_str[11:16] if len(timestamp_str) > 16 else ""
                display_time = f"{date_part} {time_part}"
            else:
                display_time = ""

            # Include name and/or comment if present
            extras = []
            if cp.get("name"):
                extras.append(f"[{cp['name']}]")
            if cp.get("comment"):
                comment = cp["comment"]
                if len(comment) > 30:
                    comment = f"{comment[:27]}..."
                extras.append(comment)

            extra_info = " - ".join(extras) if extras else ""

            # Build description: "campaign • date time • size • extras"
            description_parts = [campaign, display_time, cp.get("size_human", "")]
            if extra_info:
                description_parts.append(extra_info)

            description = " • ".join(filter(None, description_parts))
            if len(description) > 100:  # Discord description limit
                description = f"{description[:97]}..."

            options.append(
                discord.SelectOption(
                    label=label,
                    value=str(idx),  # Use index as value
                    description=description,
                )
            )

        if not options:
            # No checkpoints - add a dummy disabled option
            options.append(
                discord.SelectOption(
                    label="No checkpoints available",
                    value="__none__",
                    description="No checkpoints found",
                )
            )

        # Create select menu
        select = ui.Select(
            placeholder="Select a checkpoint to view details...",
            min_values=1,
            max_values=1,
            options=options,
        )
        select.callback = self.select_callback
        self.add_item(select)

        # Add Delete button
        delete_button = ui.Button(label="Delete", style=discord.ButtonStyle.danger, emoji="🗑️")
        delete_button.callback = self.delete_callback
        self.add_item(delete_button)

    async def select_callback(self, interaction: discord.Interaction) -> None:
        """Handle checkpoint selection and update embed.

        Args:
            interaction: Discord interaction from the select menu
        """
        # Get selected index
        selected_value = interaction.data["values"][0]  # type: ignore

        if selected_value == "__none__":
            await interaction.response.edit_message(
                content="❌ No checkpoints available.", embed=None, view=None
            )
            self.stop()
            return

        if selected_value == "__separator__":
            # User clicked the separator - ignore and keep the view as is
            await interaction.response.defer()
            return

        # Update current index
        self.current_index = int(selected_value)

        # Get selected checkpoint
        selected_checkpoint = self.checkpoints[self.current_index]

        # Generate new embed for selected checkpoint
        embed = self.format_details_func(selected_checkpoint)

        # Update the message with new embed
        await interaction.response.edit_message(
            content=f"🗑️ **Checkpoint {self.current_index + 1}/{len(self.checkpoints)}** - Select from dropdown to view details, then click Delete:",
            embed=embed,
            view=self,
        )

    async def delete_callback(self, interaction: discord.Interaction) -> None:
        """Handle Delete button click.

        Args:
            interaction: Discord interaction from the button
        """
        # Set flag and stop view
        self.delete_requested = True

        # Acknowledge the interaction without changing the message
        # The delete_command will handle showing the confirmation dialog
        await interaction.response.defer()

        self.stop()

    async def on_timeout(self) -> None:
        """Handle view timeout."""
        self.stop()


class CheckpointSelectView(ui.View):
    """Interactive view for selecting a checkpoint from a list.

    Provides a dropdown menu with all available checkpoints.
    """

    def __init__(self, checkpoints: list[dict[str, Any]], timeout: float = 180.0):
        """Initialize the checkpoint selection view.

        Args:
            checkpoints: List of checkpoint dicts with name, campaign, timestamp
            timeout: View timeout in seconds (default: 3 minutes)
        """
        super().__init__(timeout=timeout)
        self.selected_checkpoint: dict[str, Any] | None = None
        self.checkpoints = checkpoints

        # Create the dropdown (limited to 25 options by Discord)
        options = []
        separator_added = False

        for cp in checkpoints[:25]:  # Discord limit
            # Add separator before first auto-backup checkpoint
            if cp.get("is_auto_backup") and not separator_added:
                options.append(
                    discord.SelectOption(
                        label="─────────── AUTO-BACKUPS ───────────",
                        value="__separator__",
                        description="Automatic backups created before restore operations",
                        emoji="🔽",
                    )
                )
                separator_added = True

            filename = cp["filename"]
            campaign = cp.get("campaign", "unknown")
            # Format timestamp for display
            timestamp_str = cp.get("timestamp", "")
            if timestamp_str:
                # "2024-02-14T10:30:00" -> "02-14 10:30"
                date_part = timestamp_str[5:10] if len(timestamp_str) > 10 else ""
                time_part = timestamp_str[11:16] if len(timestamp_str) > 16 else ""
                display_time = f"{date_part} {time_part}"
            else:
                display_time = ""

            label = filename
            if len(label) > 100:  # Discord label limit
                label = f"{label[:97]}..."

            # Include name and/or comment if present (helps identify auto-backups)
            extras = []
            if cp.get("name"):
                extras.append(f"[{cp['name']}]")
            if cp.get("comment"):
                comment = cp["comment"]
                if len(comment) > 30:
                    comment = f"{comment[:27]}..."
                extras.append(comment)

            extra_info = " - ".join(extras) if extras else ""

            # Build description: "campaign • date time • size • extras"
            description_parts = [campaign, display_time, cp.get("size_human", "")]
            if extra_info:
                description_parts.append(extra_info)

            description = " • ".join(filter(None, description_parts))
            if len(description) > 100:  # Discord description limit
                description = f"{description[:97]}..."

            options.append(
                discord.SelectOption(
                    label=label,
                    value=filename,
                    description=description,  # Use filename as value
                )
            )

        if not options:
            # No checkpoints - add a dummy disabled option
            options.append(
                discord.SelectOption(
                    label="No checkpoints available",
                    value="__none__",
                    description="No checkpoints found",
                )
            )

        # Create select menu
        select = ui.Select(
            placeholder="Select a checkpoint...", min_values=1, max_values=1, options=options
        )
        select.callback = self.select_callback
        self.add_item(select)

    async def select_callback(self, interaction: discord.Interaction) -> None:
        """Handle checkpoint selection.

        Args:
            interaction: Discord interaction from the select menu
        """
        # Get selected value (filename)
        selected_filename = interaction.data["values"][0]  # type: ignore

        if selected_filename == "__none__":
            await interaction.response.edit_message(
                content="❌ No checkpoints available.", view=None
            )
            self.stop()
            return

        if selected_filename == "__separator__":
            # User clicked the separator - ignore and keep the view as is
            await interaction.response.defer()
            return

        # Find the checkpoint dict
        self.selected_checkpoint = next(
            (cp for cp in self.checkpoints if cp["filename"] == selected_filename), None
        )

        # Acknowledge the interaction silently
        await interaction.response.defer()

        self.stop()

    async def on_timeout(self) -> None:
        """Handle view timeout."""
        self.selected_checkpoint = None
        self.stop()


class CheckpointDeleteConfirm(ui.View):
    """Confirmation dialog for checkpoint deletion.

    Provides Confirm/Cancel buttons to prevent accidental deletions,
    with full checkpoint details displayed.
    """

    def __init__(
        self, checkpoint: dict[str, Any], restore_browser_func=None, timeout: float = 60.0
    ):
        """Initialize the confirmation view.

        Args:
            checkpoint: Checkpoint dictionary with full metadata
            restore_browser_func: Optional callback to restore the browser view on cancel
            timeout: View timeout in seconds (default: 60 seconds)
        """
        super().__init__(timeout=timeout)
        self.checkpoint = checkpoint
        self.checkpoint_name = checkpoint["filename"]
        self.confirmed: bool | None = None
        self.restore_browser_func = restore_browser_func

    @ui.button(label="Confirm Delete", style=discord.ButtonStyle.danger, emoji="🗑️")
    async def confirm_button(self, interaction: discord.Interaction, _button: ui.Button) -> None:
        """Handle confirmation button click."""
        self.confirmed = True
        await interaction.response.edit_message(
            content=f"🗑️ Deleting checkpoint: `{self.checkpoint_name}`...", embed=None, view=None
        )
        self.stop()

    @ui.button(label="Cancel", style=discord.ButtonStyle.secondary, emoji="❌")
    async def cancel_button(self, interaction: discord.Interaction, _button: ui.Button) -> None:
        """Handle cancel button click."""
        self.confirmed = False

        # If we have a restore function, call it to show the browser again
        if self.restore_browser_func:
            await self.restore_browser_func(interaction)
        else:
            await interaction.response.edit_message(
                content="❌ Deletion cancelled.", embed=None, view=None
            )
        self.stop()

    async def on_timeout(self) -> None:
        """Handle view timeout."""
        self.confirmed = False
        self.stop()


class CheckpointRestoreConfirm(ui.View):
    """Confirmation dialog for checkpoint restoration.

    Provides Confirm/Cancel buttons to prevent accidental restorations,
    with full checkpoint details displayed.
    """

    def __init__(
        self, checkpoint: dict[str, Any], server: str, auto_backup: bool, timeout: float = 60.0
    ):
        """Initialize the confirmation view.

        Args:
            checkpoint: Checkpoint dictionary with full metadata
            server: Target server name
            auto_backup: Whether auto-backup will be created
            timeout: View timeout in seconds (default: 60 seconds)
        """
        super().__init__(timeout=timeout)
        self.checkpoint = checkpoint
        self.checkpoint_name = checkpoint["filename"]
        self.server = server
        self.auto_backup = auto_backup
        self.confirmed: bool | None = None

    @ui.button(label="Confirm Restore", style=discord.ButtonStyle.primary, emoji="♻️")
    async def confirm_button(self, interaction: discord.Interaction, _button: ui.Button) -> None:
        """Handle confirmation button click."""
        self.confirmed = True
        backup_msg = " (creating auto-backup)" if self.auto_backup else " (⚠️ no backup)"
        await interaction.response.edit_message(
            content=f"♻️ Restoring checkpoint: `{self.checkpoint_name}` to server `{self.server}`{backup_msg}...",
            view=None,
        )
        self.stop()

    @ui.button(label="Cancel", style=discord.ButtonStyle.secondary, emoji="❌")
    async def cancel_button(self, interaction: discord.Interaction, _button: ui.Button) -> None:
        """Handle cancel button click."""
        self.confirmed = False
        await interaction.response.edit_message(content="❌ Restoration cancelled.", view=None)
        self.stop()

    async def on_timeout(self) -> None:
        """Handle view timeout."""
        self.confirmed = False
        self.stop()

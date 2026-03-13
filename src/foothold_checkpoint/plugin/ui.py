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


class PaginatedCheckpointSelectView(ui.View):
    """Paginated interactive view for selecting a checkpoint.

    Provides pagination, type filtering, and campaign filtering
    to handle large numbers of checkpoints within Discord's 25-option limit.
    """

    CHECKPOINTS_PER_PAGE = 20  # Safe margin below Discord's 25-option limit

    def __init__(self, checkpoints: list[dict[str, Any]], timeout: float = 180.0):
        """Initialize the paginated checkpoint selection view.

        Args:
            checkpoints: List of checkpoint dicts with name, campaign, timestamp
            timeout: View timeout in seconds (default: 3 minutes)
        """
        super().__init__(timeout=timeout)
        self.selected_checkpoint: dict[str, Any] | None = None
        self.all_checkpoints = checkpoints
        self.type_filter: str = "all"  # "all", "manual", "auto"
        self.campaign_filter: str | None = None  # None = all campaigns
        self.current_page = 0

        # Build initial UI
        self._build_ui()

    def _get_filtered_checkpoints(self) -> list[dict[str, Any]]:
        """Get checkpoints filtered by type and campaign.

        Returns:
            Filtered checkpoint list
        """
        filtered = self.all_checkpoints

        # Apply type filter
        if self.type_filter == "manual":
            filtered = [cp for cp in filtered if not cp.get("is_auto_backup", False)]
        elif self.type_filter == "auto":
            filtered = [cp for cp in filtered if cp.get("is_auto_backup", False)]

        # Apply campaign filter
        if self.campaign_filter:
            filtered = [cp for cp in filtered if cp.get("campaign") == self.campaign_filter]

        return filtered

    def _get_page_checkpoints(self) -> list[dict[str, Any]]:
        """Get checkpoints for current page.

        Returns:
            Checkpoints for current page
        """
        filtered = self._get_filtered_checkpoints()
        start_idx = self.current_page * self.CHECKPOINTS_PER_PAGE
        end_idx = start_idx + self.CHECKPOINTS_PER_PAGE
        return filtered[start_idx:end_idx]

    def _get_total_pages(self) -> int:
        """Get total number of pages.

        Returns:
            Total pages (minimum 1)
        """
        filtered = self._get_filtered_checkpoints()
        if not filtered:
            return 1
        return (len(filtered) + self.CHECKPOINTS_PER_PAGE - 1) // self.CHECKPOINTS_PER_PAGE

    def _build_select_options(
        self, page_checkpoints: list[dict[str, Any]]
    ) -> list[discord.SelectOption]:
        """Build checkpoint select options for current page.

        Args:
            page_checkpoints: Checkpoints to display

        Returns:
            List of SelectOption objects
        """
        if not page_checkpoints:
            return [
                discord.SelectOption(
                    label="No checkpoints match filters",
                    value="__none__",
                    description="Adjust filters to see more checkpoints",
                )
            ]

        options = []
        for cp in page_checkpoints:
            filename = cp["filename"]
            campaign = cp.get("campaign", "unknown")

            # Format timestamp for display
            timestamp_str = cp.get("timestamp", "")
            if timestamp_str:
                date_part = timestamp_str[5:10] if len(timestamp_str) > 10 else ""
                time_part = timestamp_str[11:16] if len(timestamp_str) > 16 else ""
                display_time = f"{date_part} {time_part}"
            else:
                display_time = ""

            label = filename
            if len(label) > 100:
                label = f"{label[:97]}..."

            # Build description
            description_parts = [campaign, display_time, cp.get("size_human", "")]
            if cp.get("name"):
                description_parts.append(f"[{cp['name']}]")

            description = " • ".join(filter(None, description_parts))
            if len(description) > 100:
                description = f"{description[:97]}..."

            emoji = "🔄" if cp.get("is_auto_backup") else "💾"

            options.append(
                discord.SelectOption(
                    label=label,
                    value=filename,
                    description=description,
                    emoji=emoji,
                )
            )

        return options

    def _get_available_campaigns(self) -> list[str]:
        """Get sorted list of unique campaigns.

        Returns:
            List of campaign names
        """
        campaigns = {cp.get("campaign", "unknown") for cp in self.all_checkpoints}
        return sorted(campaigns)

    def _get_header_text(self) -> str:
        """Generate header text with filter status.

        Returns:
            Formatted header string
        """
        total = len(self._get_filtered_checkpoints())
        total_pages = self._get_total_pages()

        # Type filter label
        type_label = {"all": "All", "manual": "Manual", "auto": "Auto-backups"}[self.type_filter]

        # Campaign filter label
        if self.campaign_filter:
            campaign_label = f" • Campaign: {self.campaign_filter}"
        else:
            campaign_label = " • All Campaigns"

        return (
            f"🔄 **Select Checkpoint to Restore** (Page {self.current_page + 1}/{total_pages})\n"
            f"Type: {type_label}{campaign_label} • Total: {total}"
        )

    def _build_ui(self) -> None:
        """Build the complete UI with filters, pagination, and checkpoint selection."""
        self.clear_items()

        page_checkpoints = self._get_page_checkpoints()
        total_pages = self._get_total_pages()

        # ROW 0: Type filter buttons
        manual_btn = ui.Button(
            label="Manual",
            style=discord.ButtonStyle.primary
            if self.type_filter == "manual"
            else discord.ButtonStyle.secondary,
            emoji="💾",
            row=0,
        )
        manual_btn.callback = self._type_filter_callback
        self.add_item(manual_btn)

        auto_btn = ui.Button(
            label="Auto-backups",
            style=discord.ButtonStyle.primary
            if self.type_filter == "auto"
            else discord.ButtonStyle.secondary,
            emoji="🔄",
            row=0,
        )
        auto_btn.callback = self._type_filter_callback
        self.add_item(auto_btn)

        all_btn = ui.Button(
            label="All",
            style=discord.ButtonStyle.primary
            if self.type_filter == "all"
            else discord.ButtonStyle.secondary,
            emoji="📋",
            row=0,
        )
        all_btn.callback = self._type_filter_callback
        self.add_item(all_btn)

        # ROW 1: Campaign filter (only if multiple campaigns exist)
        campaigns = self._get_available_campaigns()
        if len(campaigns) > 1:
            campaign_options = [
                discord.SelectOption(
                    label="All Campaigns",
                    value="__all__",
                    emoji="🌐",
                    default=self.campaign_filter is None,
                )
            ]
            for campaign in campaigns:
                campaign_options.append(
                    discord.SelectOption(
                        label=campaign,
                        value=campaign,
                        default=self.campaign_filter == campaign,
                    )
                )

            campaign_select = ui.Select(
                placeholder="Filter by campaign...",
                options=campaign_options,
                row=1,
            )
            campaign_select.callback = self._campaign_filter_callback
            self.add_item(campaign_select)

        # ROW 2: Checkpoint selection
        checkpoint_options = self._build_select_options(page_checkpoints)
        checkpoint_select = ui.Select(
            placeholder="Select checkpoint to restore...",
            options=checkpoint_options,
            row=2,
        )
        checkpoint_select.callback = self._checkpoint_select_callback
        self.add_item(checkpoint_select)

        # ROW 3: Pagination controls (only if multiple pages)
        if total_pages > 1:
            prev_btn = ui.Button(
                label="Previous",
                style=discord.ButtonStyle.secondary,
                emoji="◀",
                disabled=self.current_page == 0,
                row=3,
            )
            prev_btn.callback = self._prev_page_callback
            self.add_item(prev_btn)

            page_btn = ui.Button(
                label=f"Page {self.current_page + 1}/{total_pages}",
                style=discord.ButtonStyle.secondary,
                disabled=True,
                row=3,
            )
            self.add_item(page_btn)

            next_btn = ui.Button(
                label="Next",
                style=discord.ButtonStyle.secondary,
                emoji="▶",
                disabled=self.current_page >= total_pages - 1,
                row=3,
            )
            next_btn.callback = self._next_page_callback
            self.add_item(next_btn)

    async def _type_filter_callback(self, interaction: discord.Interaction) -> None:
        """Handle type filter button clicks.

        Args:
            interaction: Discord interaction
        """
        import discord.ui

        label = ""

        # Find button label from components
        for child in self.children:
            if isinstance(child, discord.ui.Button) and child.label:
                if child.label == "Manual":
                    label = "Manual"
                    break
                elif child.label == "Auto-backups":
                    label = "Auto-backups"
                    break
                elif child.label == "All":
                    label = "All"
                    break

        # Try extracting from interaction data
        if not label and "component" in interaction.data:  # type: ignore
            component_data = interaction.data["component"]  # type: ignore
            label = component_data.get("label", "")

        # Map label to filter
        if label == "Manual":
            self.type_filter = "manual"
        elif label == "Auto-backups":
            self.type_filter = "auto"
        else:
            self.type_filter = "all"

        self.current_page = 0  # Reset to first page
        self._build_ui()

        await interaction.response.edit_message(content=self._get_header_text(), view=self)

    async def _campaign_filter_callback(self, interaction: discord.Interaction) -> None:
        """Handle campaign filter selection.

        Args:
            interaction: Discord interaction
        """
        selected = interaction.data["values"][0]  # type: ignore
        self.campaign_filter = None if selected == "__all__" else selected
        self.current_page = 0  # Reset to first page
        self._build_ui()

        await interaction.response.edit_message(content=self._get_header_text(), view=self)

    async def _checkpoint_select_callback(self, interaction: discord.Interaction) -> None:
        """Handle checkpoint selection.

        Args:
            interaction: Discord interaction
        """
        selected_filename = interaction.data["values"][0]  # type: ignore

        if selected_filename == "__none__":
            await interaction.response.send_message(
                "❌ No checkpoints available with current filters.", ephemeral=True
            )
            return

        # Find checkpoint
        self.selected_checkpoint = next(
            (cp for cp in self.all_checkpoints if cp["filename"] == selected_filename), None
        )

        await interaction.response.defer()
        self.stop()

    async def _prev_page_callback(self, interaction: discord.Interaction) -> None:
        """Handle previous page button.

        Args:
            interaction: Discord interaction
        """
        if self.current_page > 0:
            self.current_page -= 1
            self._build_ui()

        await interaction.response.edit_message(content=self._get_header_text(), view=self)

    async def _next_page_callback(self, interaction: discord.Interaction) -> None:
        """Handle next page button.

        Args:
            interaction: Discord interaction
        """
        total_pages = self._get_total_pages()
        if self.current_page < total_pages - 1:
            self.current_page += 1
            self._build_ui()

        await interaction.response.edit_message(content=self._get_header_text(), view=self)

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


class PaginatedCheckpointBrowserView(ui.View):
    """Paginated checkpoint browser with campaign and type filters.

    Features:
    - Filter by type (Manual/Auto-backup/All)
    - Filter by campaign (dropdown with all detected campaigns)
    - Pagination (20 checkpoints per page)
    - Live details preview
    """

    CHECKPOINTS_PER_PAGE = 20

    def __init__(
        self, checkpoints: list[dict[str, Any]], format_details_func, timeout: float = 300.0
    ):
        """Initialize the paginated checkpoint browser.

        Args:
            checkpoints: List of checkpoint dicts with metadata
            format_details_func: Function to format checkpoint details as embed
            timeout: View timeout in seconds (default: 5 minutes)
        """
        super().__init__(timeout=timeout)
        self.all_checkpoints = checkpoints
        self.format_details_func = format_details_func

        # Separate manual and auto-backups
        self.manual = [cp for cp in checkpoints if not cp.get("is_auto_backup")]
        self.auto_backups = [cp for cp in checkpoints if cp.get("is_auto_backup")]

        # Extract unique campaigns (sorted alphabetically)
        campaigns_set = {cp.get("campaign", "unknown") for cp in checkpoints}
        self.campaigns = sorted(campaigns_set)

        # State
        self.type_filter = "manual"  # "manual", "auto", "all"
        self.campaign_filter = "all"  # "all" or specific campaign name
        self.current_page = 0
        self.current_index = 0

        self._build_ui()

    def _get_filtered_checkpoints(self) -> list[dict[str, Any]]:
        """Get checkpoints based on current filters."""
        # First filter by type
        if self.type_filter == "manual":
            filtered = self.manual
        elif self.type_filter == "auto":
            filtered = self.auto_backups
        else:  # "all"
            filtered = self.all_checkpoints

        # Then filter by campaign
        if self.campaign_filter != "all":
            filtered = [cp for cp in filtered if cp.get("campaign") == self.campaign_filter]

        return filtered

    def _get_page_checkpoints(self) -> list[dict[str, Any]]:
        """Get checkpoints for current page."""
        filtered = self._get_filtered_checkpoints()
        start = self.current_page * self.CHECKPOINTS_PER_PAGE
        end = start + self.CHECKPOINTS_PER_PAGE
        return filtered[start:end]

    def _build_select_options(
        self, page_checkpoints: list[dict[str, Any]]
    ) -> list[discord.SelectOption]:
        """Build select options for current page checkpoints."""
        if not page_checkpoints:
            return [
                discord.SelectOption(
                    label="No checkpoints found",
                    value="__none__",
                    description="Try changing filters",
                )
            ]

        options = []
        for idx, cp in enumerate(page_checkpoints):
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

            # Use global index as value (page_start + idx)
            global_idx = self.current_page * self.CHECKPOINTS_PER_PAGE + idx
            options.append(
                discord.SelectOption(label=label, value=str(global_idx), description=description)
            )

        return options

    def _build_ui(self) -> None:
        """Build UI components based on current state."""
        self.clear_items()

        # Row 0: Type filter buttons
        manual_btn = ui.Button(
            label=f"Manual ({len(self.manual)})",
            style=(
                discord.ButtonStyle.primary
                if self.type_filter == "manual"
                else discord.ButtonStyle.secondary
            ),
            emoji="🔹",
            row=0,
        )
        manual_btn.callback = lambda i: self._type_filter_callback(i, "manual")

        auto_btn = ui.Button(
            label=f"Auto-backups ({len(self.auto_backups)})",
            style=(
                discord.ButtonStyle.primary
                if self.type_filter == "auto"
                else discord.ButtonStyle.secondary
            ),
            emoji="🔄",
            row=0,
        )
        auto_btn.callback = lambda i: self._type_filter_callback(i, "auto")

        all_btn = ui.Button(
            label=f"All ({len(self.all_checkpoints)})",
            style=(
                discord.ButtonStyle.primary
                if self.type_filter == "all"
                else discord.ButtonStyle.secondary
            ),
            emoji="📦",
            row=0,
        )
        all_btn.callback = lambda i: self._type_filter_callback(i, "all")

        self.add_item(manual_btn)
        self.add_item(auto_btn)
        self.add_item(all_btn)

        # Row 1: Campaign filter select (only if multiple campaigns exist)
        if len(self.campaigns) > 1:
            campaign_options = [
                discord.SelectOption(
                    label="All Campaigns",
                    value="all",
                    description=f"{len(self.all_checkpoints)} total checkpoints",
                    emoji="🌍",
                )
            ]

            for campaign in self.campaigns:
                count = sum(1 for cp in self.all_checkpoints if cp.get("campaign") == campaign)
                campaign_options.append(
                    discord.SelectOption(
                        label=campaign,
                        value=campaign,
                        description=f"{count} checkpoint{'s' if count != 1 else ''}",
                    )
                )

            campaign_select = ui.Select(
                placeholder=f"Campaign: {self.campaign_filter if self.campaign_filter != 'all' else 'All'}",
                options=campaign_options,
                row=1,
            )
            campaign_select.callback = self._campaign_filter_callback
            self.add_item(campaign_select)

        # Row 2: Checkpoint select
        page_checkpoints = self._get_page_checkpoints()
        checkpoint_options = self._build_select_options(page_checkpoints)

        checkpoint_select = ui.Select(
            placeholder="Select a checkpoint to view details...",
            options=checkpoint_options,
            row=2,
        )
        checkpoint_select.callback = self._checkpoint_select_callback
        self.add_item(checkpoint_select)

        # Row 3: Pagination buttons (if needed)
        filtered = self._get_filtered_checkpoints()
        total_pages = max(
            1, (len(filtered) + self.CHECKPOINTS_PER_PAGE - 1) // self.CHECKPOINTS_PER_PAGE
        )

        if total_pages > 1:
            prev_btn = ui.Button(
                label="Previous",
                emoji="◀️",
                disabled=(self.current_page == 0),
                row=3,
            )
            prev_btn.callback = self._prev_page_callback

            page_info_btn = ui.Button(
                label=f"Page {self.current_page + 1}/{total_pages}",
                style=discord.ButtonStyle.secondary,
                disabled=True,
                row=3,
            )

            next_btn = ui.Button(
                label="Next",
                emoji="▶️",
                disabled=(self.current_page >= total_pages - 1),
                row=3,
            )
            next_btn.callback = self._next_page_callback

            self.add_item(prev_btn)
            self.add_item(page_info_btn)
            self.add_item(next_btn)

    async def _type_filter_callback(
        self, interaction: discord.Interaction, filter_type: str
    ) -> None:
        """Handle type filter button click."""
        self.type_filter = filter_type
        self.current_page = 0  # Reset to first page
        self._build_ui()
        await self._update_message(interaction)

    async def _campaign_filter_callback(self, interaction: discord.Interaction) -> None:
        """Handle campaign filter selection."""
        selected_campaign = interaction.data["values"][0]  # type: ignore
        self.campaign_filter = selected_campaign
        self.current_page = 0  # Reset to first page
        self._build_ui()
        await self._update_message(interaction)

    async def _checkpoint_select_callback(self, interaction: discord.Interaction) -> None:
        """Handle checkpoint selection."""
        selected_value = interaction.data["values"][0]  # type: ignore

        if selected_value == "__none__":
            await interaction.response.defer()
            return

        # Get global index
        global_idx = int(selected_value)
        filtered = self._get_filtered_checkpoints()

        if global_idx >= len(filtered):
            await interaction.response.defer()
            return

        # Update current index
        self.current_index = global_idx
        selected_checkpoint = filtered[global_idx]

        # Generate embed
        embed = self.format_details_func(selected_checkpoint)

        # Update message
        await interaction.response.edit_message(
            content=self._get_header_text(filtered),
            embed=embed,
            view=self,
        )

    async def _prev_page_callback(self, interaction: discord.Interaction) -> None:
        """Handle previous page button."""
        if self.current_page > 0:
            self.current_page -= 1
            self._build_ui()
            await self._update_message(interaction)

    async def _next_page_callback(self, interaction: discord.Interaction) -> None:
        """Handle next page button."""
        filtered = self._get_filtered_checkpoints()
        total_pages = (len(filtered) + self.CHECKPOINTS_PER_PAGE - 1) // self.CHECKPOINTS_PER_PAGE

        if self.current_page < total_pages - 1:
            self.current_page += 1
            self._build_ui()
            await self._update_message(interaction)

    def _get_header_text(self, filtered: list[dict[str, Any]]) -> str:
        """Generate header text showing filter status."""
        total = len(filtered)
        start = self.current_page * self.CHECKPOINTS_PER_PAGE + 1
        end = min((self.current_page + 1) * self.CHECKPOINTS_PER_PAGE, total)

        filter_parts = []
        if self.type_filter != "all":
            filter_parts.append(f"Type: {self.type_filter.title()}")
        if self.campaign_filter != "all":
            filter_parts.append(f"Campaign: {self.campaign_filter}")

        filter_text = f" ({', '.join(filter_parts)})" if filter_parts else ""

        if total == 0:
            return f"📦 No checkpoints found{filter_text}"
        elif total <= self.CHECKPOINTS_PER_PAGE:
            return f"📦 **{total} checkpoint{'s' if total != 1 else ''}**{filter_text}"
        else:
            return f"📦 **Showing {start}-{end} of {total} checkpoints**{filter_text}"

    async def _update_message(self, interaction: discord.Interaction) -> None:
        """Update message with current state."""
        filtered = self._get_filtered_checkpoints()
        page_checkpoints = self._get_page_checkpoints()

        if page_checkpoints:
            # Show first checkpoint of current page
            embed = self.format_details_func(page_checkpoints[0])
            await interaction.response.edit_message(
                content=self._get_header_text(filtered),
                embed=embed,
                view=self,
            )
        else:
            # No checkpoints found
            await interaction.response.edit_message(
                content=self._get_header_text(filtered),
                embed=None,
                view=self,
            )

    async def on_timeout(self) -> None:
        """Handle view timeout."""
        self.stop()


class PaginatedCheckpointDeleteBrowserView(PaginatedCheckpointBrowserView):
    """Paginated checkpoint browser for deletion with Delete button.

    Extends PaginatedCheckpointBrowserView to add a Delete button.
    """

    def __init__(
        self, checkpoints: list[dict[str, Any]], format_details_func, timeout: float = 300.0
    ):
        """Initialize the paginated delete browser.

        Args:
            checkpoints: List of checkpoint dicts with metadata
            format_details_func: Function to format checkpoint details as embed
            timeout: View timeout in seconds (default: 5 minutes)
        """
        super().__init__(checkpoints, format_details_func, timeout)
        self.delete_requested = False  # Flag to indicate delete button clicked

    def _build_ui(self) -> None:
        """Build UI components based on current state (including Delete button)."""
        # Call parent to build all standard components
        super()._build_ui()

        # Add Delete button at row 4 (after pagination buttons)
        delete_button = ui.Button(
            label="Delete",
            style=discord.ButtonStyle.danger,
            emoji="🗑️",
            row=4,
        )
        delete_button.callback = self._delete_callback
        self.add_item(delete_button)

    async def _delete_callback(self, interaction: discord.Interaction) -> None:
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

    def _get_header_text(self, filtered: list[dict[str, Any]]) -> str:
        """Generate header text showing filter status (with delete emoji)."""
        text = super()._get_header_text(filtered)
        # Replace 📦 with 🗑️ to indicate delete mode
        return text.replace("📦", "🗑️", 1)

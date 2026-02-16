"""Pydantic models for DCSServerBot plugin configuration."""

from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field, field_validator


class PermissionsConfig(BaseModel):
    """Permission configuration for Discord role-based access control."""

    save: list[str] = Field(
        default_factory=lambda: ["DCS Admin", "Mission Designer"],
        description="Roles allowed to save checkpoints"
    )
    restore: list[str] = Field(
        default_factory=lambda: ["DCS Admin"],
        description="Roles allowed to restore checkpoints"
    )
    list_checkpoints: list[str] = Field(
        default_factory=lambda: ["DCS Admin", "Mission Designer", "Mission Controller"],
        description="Roles allowed to list checkpoints",
        alias="list"
    )
    delete: list[str] = Field(
        default_factory=lambda: ["DCS Admin"],
        description="Roles allowed to delete checkpoints"
    )


class NotificationsConfig(BaseModel):
    """Notification configuration for Discord events."""

    channel: str = Field(
        default="mission-logs",
        description="Discord channel name for checkpoint notifications"
    )
    on_save: bool = Field(
        default=True,
        description="Send notification when checkpoint is saved"
    )
    on_restore: bool = Field(
        default=True,
        description="Send notification when checkpoint is restored"
    )
    on_delete: bool = Field(
        default=True,
        description="Send notification when checkpoint is deleted"
    )
    on_error: bool = Field(
        default=True,
        description="Send notification on operation errors"
    )


class PluginConfig(BaseModel):
    """Plugin configuration model for DCSServerBot integration."""

    campaigns_file: Path = Field(
        ...,
        description="Path to campaigns.yaml defining all campaign settings"
    )
    checkpoints_dir: Path = Field(
        ...,
        description="Directory where checkpoints are stored"
    )
    permissions: PermissionsConfig = Field(
        default_factory=PermissionsConfig,
        description="Role-based permission configuration"
    )
    notifications: NotificationsConfig = Field(
        default_factory=NotificationsConfig,
        description="Discord notification settings"
    )

    @field_validator("campaigns_file", "checkpoints_dir")
    @classmethod
    def resolve_path(cls, v: Path) -> Path:
        """Resolve paths to absolute."""
        return v.resolve()

    @field_validator("campaigns_file")
    @classmethod
    def validate_campaigns_file(cls, v: Path) -> Path:
        """Validate that campaigns_file exists."""
        if not v.exists():
            raise ValueError(f"Campaigns file not found: {v}")
        if not v.is_file():
            raise ValueError(f"Campaigns file path is not a file: {v}")
        return v

    def to_dict(self) -> dict[str, Any]:
        """Convert config to dictionary for use with permission/notification functions."""
        return {
            "campaigns_file": str(self.campaigns_file),
            "checkpoints_dir": str(self.checkpoints_dir),
            "permissions": {
                "save": self.permissions.save,
                "restore": self.permissions.restore,
                "list": self.permissions.list_checkpoints,
                "delete": self.permissions.delete,
            },
            "notifications": {
                "channel": self.notifications.channel,
                "on_save": self.notifications.on_save,
                "on_restore": self.notifications.on_restore,
                "on_delete": self.notifications.on_delete,
                "on_error": self.notifications.on_error,
            }
        }

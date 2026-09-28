"""
PRCustomComponent for Home Assistant.

SPDX-License-Identifier: Apache-2.0

Update Platform

For more details about this integration, please refer to
https://github.com/alandtse/pr_custom_component
"""

from typing import Any

from homeassistant.components.update import UpdateEntity, UpdateEntityFeature

from .const import DOMAIN
from .entity import PRCustomComponentApiClientEntity


async def async_setup_entry(hass, entry, async_add_devices):
    """Setup update platform."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_devices([PRCustomComponentApiClientUpdate(coordinator, entry)])


class PRCustomComponentApiClientUpdate(PRCustomComponentApiClientEntity, UpdateEntity):
    """PRCustomComponent update class."""

    def __init__(self, coordinator, entry):
        """Initialize the update entity."""
        super().__init__(coordinator, entry)

    _attr_supported_features = UpdateEntityFeature.INSTALL

    @property
    def installed_version(self):
        """Return the installed version."""
        return self.coordinator.api.installed_version

    @property
    def latest_version(self):
        """Return the latest version."""
        return self.coordinator.api.latest_version

    async def async_install(
        self, version: str | None, backup: bool, **kwargs: Any
    ) -> None:
        """Install an update."""
        return await self.coordinator.api.async_update_data(
            download=True, version=version, backup=backup, **kwargs
        )

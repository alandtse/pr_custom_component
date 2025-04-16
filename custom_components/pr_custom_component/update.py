"""
PRCustomComponent for Home Assistant.

SPDX-License-Identifier: Apache-2.0

Update Platform

For more details about this integration, please refer to
https://github.com/alandtse/pr_custom_component
"""
from homeassistant.components.update import (
    UpdateDeviceClass,
    UpdateEntity,
    UpdateEntityDescription,
    UpdateEntityFeature,
)
from homeassistant.helpers.device_registry import DeviceInfo

# from .const import BINARY_SENSOR_DEVICE_CLASS, DOMAIN
from .const import DOMAIN
from .entity import PRCustomComponentApiClientEntity


async def async_setup_entry(hass, entry, async_add_devices):
    """Setup binary_sensor platform."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_devices([PRCustomComponentApiClientUpdate(coordinator, entry)])


class PRCustomComponentApiClientUpdate(
    PRCustomComponentApiClientEntity, UpdateEntity
):
    """PRCustomComponent binary_sensor class."""

    def __init__(self, coordinator, entry):
        """Initialize the binary_sensor."""
        super().__init__(coordinator, entry)

    _attr_supported_features = (
        UpdateEntityFeature.INSTALL #| UpdateEntityFeature.PROGRESS
    )

    @property
    def installed_version(self):
        """Return the installed version."""
        return self.coordinator.api.installed_version

    @property
    def latest_version(self):
        """Return the latest version."""
        return self.coordinator.api.latest_version

    async def async_update(self):
        """Update the entity."""
        return await self.coordinator.api.async_update_data(download=self.coordinator.api.auto_update)
"""
PRCustomComponent for Home Assistant.

SPDX-License-Identifier: Apache-2.0

Binary Sensor Platform

For more details about this integration, please refer to
https://github.com/alandtse/pr_custom_component
"""
from homeassistant.components.binary_sensor import BinarySensorEntity

from .const import BINARY_SENSOR, BINARY_SENSOR_DEVICE_CLASS, DEFAULT_NAME, DOMAIN, ICON
from .entity import PRCustomComponentApiClientEntity


async def async_setup_entry(hass, entry, async_add_devices):
    """Setup binary_sensor platform."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_devices([PRCustomComponentApiClientBinarySensor(coordinator, entry)])


class PRCustomComponentApiClientBinarySensor(
    PRCustomComponentApiClientEntity, BinarySensorEntity
):
    """PRCustomComponent binary_sensor class."""

    @property
    def name(self):
        """Return the name of the binary_sensor."""
        return f"{super().name} update available"

    @property
    def device_class(self):
        """Return the class of this binary_sensor."""
        return BINARY_SENSOR_DEVICE_CLASS

    @property
    def is_on(self):
        """Return true if the binary_sensor is on."""
        return self.coordinator.api.update_available

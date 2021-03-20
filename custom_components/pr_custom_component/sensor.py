"""
PRCustomComponent for Home Assistant.

SPDX-License-Identifier: Apache-2.0

Sensor Platform

For more details about this integration, please refer to
https://github.com/alandtse/pr_custom_component
"""
from .const import DEFAULT_NAME, DOMAIN, ICON, SENSOR, SENSOR_DEVICE_CLASS
from .entity import PRCustomComponentApiClientEntity


async def async_setup_entry(hass, entry, async_add_devices):
    """Setup sensor platform."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_devices([PRCustomComponentApiClientSensor(coordinator, entry)])


class PRCustomComponentApiClientSensor(PRCustomComponentApiClientEntity):
    """PRCustomComponent Sensor class."""

    @property
    def name(self):
        """Return the name of the sensor."""
        return f"{super().name} last update"

    @property
    def state(self):
        """Return the state of the sensor."""
        return self.coordinator.api.updated_at

    @property
    def device_class(self):
        """Return the class of this sensor."""
        return SENSOR_DEVICE_CLASS

    @property
    def icon(self):
        """Return the icon of the sensor."""
        return ICON

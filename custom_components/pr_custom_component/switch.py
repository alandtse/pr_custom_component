"""
PRCustomComponent for Home Assistant.

SPDX-License-Identifier: Apache-2.0

Switch Platform

For more details about this integration, please refer to
https://github.com/alandtse/pr_custom_component
"""
from homeassistant.components.switch import SwitchEntity

from .const import DOMAIN, ICON
from .entity import PRCustomComponentApiClientEntity


async def async_setup_entry(hass, entry, async_add_devices):
    """Setup sensor platform."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_devices([PRCustomComponentApiClientBinarySwitch(coordinator, entry)])


class PRCustomComponentApiClientBinarySwitch(
    PRCustomComponentApiClientEntity, SwitchEntity
):
    """PRCustomComponent switch class."""

    async def async_turn_on(self, **kwargs):  # pylint: disable=unused-argument
        """Turn on the switch."""
        self.coordinator.api.auto_update = True

    async def async_turn_off(self, **kwargs):  # pylint: disable=unused-argument
        """Turn off the switch."""
        self.coordinator.api.auto_update = False

    @property
    def name(self):
        """Return the name of the switch."""
        return f"{super().name} auto update"

    @property
    def icon(self):
        """Return the icon of this switch."""
        return ICON

    @property
    def is_on(self):
        """Return true if the switch is on."""
        return self.coordinator.api.auto_update

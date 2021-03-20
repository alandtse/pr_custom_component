"""
PRCustomComponent for Home Assistant.

SPDX-License-Identifier: Apache-2.0

Base entity to inherit

For more details about this integration, please refer to
https://github.com/alandtse/pr_custom_component
"""
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, NAME, VERSION, DEFAULT_NAME


class PRCustomComponentApiClientEntity(CoordinatorEntity):
    def __init__(self, coordinator, config_entry):
        super().__init__(coordinator)
        self.config_entry = config_entry

    @property
    def unique_id(self):
        """Return a unique ID to use for this entity."""
        return self.config_entry.entry_id

    @property
    def name(self):
        """Return a name to use for this entity."""
        return f"{self.config_entry.data.get('name', DEFAULT_NAME).capitalize()} PR#{self.config_entry.data.get('pull_number', 'UNKNOWN')}"

    @property
    def device_info(self):
        """Return device_info."""
        return {
            "identifiers": {(DOMAIN, self.unique_id)},
            "name": f"{self.config_entry.data.get('name', DEFAULT_NAME).capitalize()} PR#{self.config_entry.data.get('pull_number', 'UNKNOWN')}",
            "model": VERSION,
            "manufacturer": NAME,
            "sw_version": f"{self.config_entry.data.get('update_time', DEFAULT_NAME)}",
        }

    @property
    def device_state_attributes(self):
        """Return the state attributes."""
        return {
            "id": self.coordinator.api.name,
            "integration": DOMAIN,
            "pr_url": f"{self.config_entry.data.get('pr_url', '')}",
        }

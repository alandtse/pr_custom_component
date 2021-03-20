"""
PRCustomComponent for Home Assistant.

SPDX-License-Identifier: Apache-2.0

For more details about this integration, please refer to
https://github.com/alandtse/pr_custom_component
"""
import asyncio
from datetime import timedelta
import logging
from typing import List, Text

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import Config, HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers.aiohttp_client import (
    async_get_clientsession,
)
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
import yarl

from .api import PRCustomComponentApiClient
from .const import CONF_PR_URL, DOMAIN, HACS_DOMAIN, PLATFORMS, STARTUP_MESSAGE

SCAN_INTERVAL = timedelta(days=1)

_LOGGER: logging.Logger = logging.getLogger(__package__)


async def async_setup(hass: HomeAssistant, config: Config):
    """Set up this integration using YAML is not supported."""
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Set up this integration using UI."""
    if hass.data.get(DOMAIN) is None:
        hass.data.setdefault(DOMAIN, {})
        _LOGGER.info(STARTUP_MESSAGE)

    pr_url = entry.data.get(CONF_PR_URL)

    session = async_get_clientsession(hass)
    client = PRCustomComponentApiClient(session, yarl.URL(pr_url), hass.config.path())
    client.set_token(get_hacs_token(hass))
    client.updated_at = entry.data["update_time"]
    coordinator = PRCustomComponentDataUpdateCoordinator(hass, client=client)
    await coordinator.async_refresh()

    if not coordinator.last_update_success:
        raise ConfigEntryNotReady

    hass.data[DOMAIN][entry.entry_id] = coordinator

    for platform in PLATFORMS:
        if entry.options.get(platform, True):
            coordinator.platforms.append(platform)
            hass.async_add_job(
                hass.config_entries.async_forward_entry_setup(entry, platform)
            )

    entry.add_update_listener(async_reload_entry)
    return True


class PRCustomComponentDataUpdateCoordinator(DataUpdateCoordinator):
    """Class to manage fetching data from the API."""

    def __init__(self, hass: HomeAssistant, client: PRCustomComponentApiClient) -> None:
        """Initialize."""
        self.api = client
        self.platforms: List[Text] = []
        self.hass = hass

        super().__init__(hass, _LOGGER, name=DOMAIN, update_interval=SCAN_INTERVAL)

    async def _async_update_data(self):
        """Update data via library."""
        self.api.set_token(get_hacs_token(self.hass))
        try:
            return await self.api.async_update_data(download=self.api.auto_update)
        except Exception as exception:
            raise UpdateFailed() from exception


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Handle removal of an entry."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    unloaded = all(
        await asyncio.gather(
            *[
                hass.config_entries.async_forward_entry_unload(entry, platform)
                for platform in PLATFORMS
                if platform in coordinator.platforms
            ]
        )
    )
    await coordinator.api.async_delete()
    if unloaded:
        hass.data[DOMAIN].pop(entry.entry_id)

    return unloaded


async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload config entry."""
    await async_unload_entry(hass, entry)
    await async_setup_entry(hass, entry)


def get_hacs_token(hass: HomeAssistant) -> Text:
    """Search for hacs token."""
    if not hass:
        _LOGGER.debug("No hass provided.")
        return ""
    hacs_token: Text = ""
    old_hacs_token: Text = hacs_token
    if hass.config_entries.async_entries(HACS_DOMAIN):
        for hacs_entry in hass.config_entries.async_entries(HACS_DOMAIN):
            hacs_token = hacs_entry.data.get("token", "")
            if hacs_token:
                break
    if hacs_token and hacs_token != old_hacs_token:
        _LOGGER.debug("Found new hacs token")
    return hacs_token

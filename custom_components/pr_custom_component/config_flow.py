"""
PRCustomComponent for Home Assistant.

SPDX-License-Identifier: Apache-2.0

Config Flow Platform

For more details about this integration, please refer to
https://github.com/alandtse/pr_custom_component
"""
from typing import Dict, Text

from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.helpers.aiohttp_client import async_get_clientsession
import voluptuous as vol
import yarl
import logging

from . import get_hacs_token
from .api import PRCustomComponentApiClient
from .const import CONF_PR_URL, DOMAIN, PLATFORMS
from .exceptions import RateLimitException

_LOGGER: logging.Logger = logging.getLogger(__package__)


class PRCustomComponentFlowHandler(  # type: ignore
    config_entries.ConfigFlow, domain=DOMAIN
):
    """Config flow for PRCustomComponent."""

    VERSION = 1
    CONNECTION_CLASS = config_entries.CONN_CLASS_CLOUD_POLL

    def __init__(self):
        """Initialize."""
        self._errors = {}

    async def async_step_user(self, user_input=None):
        """Handle a flow initialized by the user."""
        self._errors = {}

        # Uncomment the next 2 lines if only a single instance of the integration is allowed:
        # if self._async_current_entries():
        #     return self.async_abort(reason="single_instance_allowed")

        if user_input is not None:
            result = {}
            try:
                result = await self.install_integration(user_input[CONF_PR_URL])
            except RateLimitException:
                self._errors["base"] = "rate_limited"
                return await self._show_config_form(user_input)
            if result.get("name") and result.get("update_time"):
                user_input.update(result)
                return self.async_create_entry(
                    title=result.get("name"), data=user_input
                )
            else:
                self._errors["base"] = "bad_pr"

            return await self._show_config_form(user_input)

        return await self._show_config_form(user_input)

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        return PRCustomComponentOptionsFlowHandler(config_entry)

    async def _show_config_form(self, user_input):  # pylint: disable=unused-argument
        """Show the configuration form to edit location data."""
        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({vol.Required(CONF_PR_URL): str}),
            errors=self._errors,
        )

    async def install_integration(self, pr_url: Text) -> Dict:
        """Return true if integration is successfully installed."""
        try:
            session = async_get_clientsession(self.hass)
            client = PRCustomComponentApiClient(
                session, yarl.URL(pr_url), self.hass.config.path()
            )
            client.set_token(get_hacs_token(self.hass))
            await client.async_update_data(download=True)
            return {
                "name": client.name,
                "update_time": client.updated_at,
                "pull_number": client.pull_number,
            }
        except Exception:  # pylint: disable=broad-except
            raise
        return {}


class PRCustomComponentOptionsFlowHandler(config_entries.OptionsFlow):
    """PRCustomComponent config flow options handler."""

    def __init__(self, config_entry):
        """Initialize HACS options flow."""
        self.config_entry = config_entry
        self.options = dict(config_entry.options)

    async def async_step_init(self, user_input=None):  # pylint: disable=unused-argument
        """Manage the options."""
        return await self.async_step_user()

    async def async_step_user(self, user_input=None):
        """Handle a flow initialized by the user."""
        if user_input is not None:
            self.options.update(user_input)
            return await self._update_options()

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(x, default=self.options.get(x, True)): bool
                    for x in sorted(PLATFORMS)
                }
            ),
        )

    async def _update_options(self):
        """Update config entry options."""
        return self.async_create_entry(title=self.config_entry.title, data=self.options)

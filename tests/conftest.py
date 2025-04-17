"""Global fixtures for PRCustomComponent integration."""
# Fixtures allow you to replace functions with a Mock object. You can perform
# many options via the Mock to reflect a particular behavior from the original
# function that you want to see without going through the function's actual logic.
# Fixtures can either be passed into tests as parameters, or if autouse=True, they
# will automatically be used across all tests.
#
# Fixtures that are defined in conftest.py are available across all tests. You can also
# define fixtures within a particular test file to scope them locally.
#
# pytest_homeassistant_custom_component provides some fixtures that are provided by
# Home Assistant core. You can find those fixture definitions here:
# https://github.com/MatthewFlamm/pytest-homeassistant-custom-component/blob/master/pytest_homeassistant_custom_component/common.py
#
# See here for more info: https://docs.pytest.org/en/latest/fixture.html (note that
# pytest includes fixtures OOB which you can use as defined on this page)
from unittest.mock import patch
import pytest
import os
from pathlib import Path

from .const import MOCK_CONFIG_DATA
from pytest_homeassistant_custom_component.common import MockConfigEntry
from custom_components.pr_custom_component import async_setup_entry
from custom_components.pr_custom_component.const import DOMAIN
from custom_components.pr_custom_component.update import PRCustomComponentApiClientUpdate

pytest_plugins = "pytest_homeassistant_custom_component"


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations):
    """Enable custom integrations."""
    return


# This fixture is used to prevent HomeAssistant from attempting to create and dismiss persistent
# notifications. These calls would fail without this fixture since the persistent_notification
# integration is never loaded during a test.
@pytest.fixture(name="skip_notifications", autouse=True)
def skip_notifications_fixture():
    """Skip notification calls."""
    with patch("homeassistant.components.persistent_notification.async_create"), patch(
        "homeassistant.components.persistent_notification.async_dismiss"
    ):
        yield


# This fixture creates a mock config entry that can be used across all tests.
# It provides a consistent configuration for testing the integration.
@pytest.fixture(name="mock_config_entry")
async def mock_config_entry_fixture(hass):
    """Create a mock config entry."""

    return MockConfigEntry(domain=DOMAIN, data=MOCK_CONFIG_DATA, entry_id="test")


# This fixture sets up the update entity and its coordinator for testing.
# It handles the initialization of the integration and provides both the entity
# and coordinator objects that are needed for testing update functionality.
@pytest.fixture(name="setup_update_entity")
async def setup_update_entity_fixture(hass, mock_config_entry):
    """Set up the update entity and return it along with its coordinator."""
    # Add the config entry to Home Assistant
    mock_config_entry.add_to_hass(hass)
    
    # Set up the config entry
    assert await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    coordinator = hass.data[DOMAIN][mock_config_entry.entry_id]
    update_entity = PRCustomComponentApiClientUpdate(coordinator, mock_config_entry)
    
    return update_entity, coordinator


# This fixture, when used, will result in calls to async_update_data to return None. To have the call
# return a value, we would add the `return_value=<VALUE_TO_RETURN>` parameter to the patch call.
@pytest.fixture(name="bypass_get_data")
def bypass_get_data_fixture():
    """Skip calls to get data from API."""
    with patch(
        "custom_components.pr_custom_component.PRCustomComponentApiClient.async_update_data"
    ):
        yield


# In this fixture, we are forcing calls to async_update_data to raise an Exception. This is useful
# for exception handling.
@pytest.fixture(name="error_on_get_data")
def error_get_data_fixture():
    """Simulate error when retrieving data from API."""
    with patch(
        "custom_components.pr_custom_component.PRCustomComponentApiClient.async_update_data",
        side_effect=Exception,
    ):
        yield

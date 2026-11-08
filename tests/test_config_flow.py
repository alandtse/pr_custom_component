"""Test PRCustomComponent config flow."""
from unittest.mock import patch

from homeassistant import config_entries, data_entry_flow
import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.pr_custom_component.const import (
    DOMAIN,
    PLATFORMS,
    SENSOR,
    SWITCH,
    UPDATE,
)
from custom_components.pr_custom_component.exceptions import RateLimitException

from .const import MOCK_CONFIG, MOCK_CONFIG_DATA


# This fixture bypasses the actual setup of the integration
# since we only want to test the config flow. We test the
# actual functionality of the integration in other test modules.
@pytest.fixture(autouse=True)
def bypass_setup_fixture():
    """Prevent setup."""
    with patch(
        "custom_components.pr_custom_component.async_setup",
        return_value=True,
    ), patch(
        "custom_components.pr_custom_component.async_setup_entry",
        return_value=True,
    ):
        yield


# Here we simiulate a successful config flow from the backend.
# Note that we use the `bypass_get_data` fixture here because
# we want the config flow validation to succeed during the test.
async def test_successful_config_flow(hass):
    """Test a successful config flow."""
    # Initialize a config flow
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    # Check that the config flow shows the user form as the first step
    assert result["type"] == data_entry_flow.FlowResultType.FORM
    assert result["step_id"] == "user"

    # The API lookup is mocked so the PR validates and returns its metadata
    install_result = {
        "name": MOCK_CONFIG_DATA["name"],
        "update_time": MOCK_CONFIG_DATA["update_time"],
        "pull_number": MOCK_CONFIG_DATA["pull_number"],
    }
    with patch(
        "custom_components.pr_custom_component.config_flow."
        "PRCustomComponentFlowHandler.install_integration",
        return_value=install_result,
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], user_input=dict(MOCK_CONFIG)
        )

    # Check that the config flow is complete and a new entry is created with
    # the input data plus the PR metadata
    assert result["type"] == data_entry_flow.FlowResultType.CREATE_ENTRY
    assert result["title"] == MOCK_CONFIG_DATA["name"]
    assert result["data"] == MOCK_CONFIG_DATA
    assert result["result"]


# A PR that cannot be resolved (empty API result) must show the form again
# with the bad_pr error.
async def test_failed_config_flow(hass):
    """Test a failed config flow due to an unresolvable PR."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    assert result["type"] == data_entry_flow.FlowResultType.FORM
    assert result["step_id"] == "user"

    with patch(
        "custom_components.pr_custom_component.config_flow."
        "PRCustomComponentFlowHandler.install_integration",
        return_value={},
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], user_input=dict(MOCK_CONFIG)
        )

    assert result["type"] == data_entry_flow.FlowResultType.FORM
    assert result["errors"] == {"base": "bad_pr"}


async def test_rate_limited_config_flow(hass):
    """Test the config flow reports GitHub rate limiting."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    with patch(
        "custom_components.pr_custom_component.config_flow."
        "PRCustomComponentFlowHandler.install_integration",
        side_effect=RateLimitException,
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], user_input=dict(MOCK_CONFIG)
        )

    assert result["type"] == data_entry_flow.FlowResultType.FORM
    assert result["errors"] == {"base": "rate_limited"}


# Our config flow also has an options flow, so we must test it as well.
async def test_options_flow(hass):
    """Test an options flow."""
    # Create a new MockConfigEntry and add to HASS (we're bypassing config
    # flow entirely)
    entry = MockConfigEntry(domain=DOMAIN, data=MOCK_CONFIG_DATA, entry_id="test")
    entry.add_to_hass(hass)

    # Initialize an options flow
    result = await hass.config_entries.options.async_init(entry.entry_id)

    # Verify that the first options step is a user form
    assert result["type"] == data_entry_flow.FlowResultType.FORM
    assert result["step_id"] == "user"

    # Enter some fake data into the form
    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={platform: platform != SENSOR for platform in PLATFORMS},
    )

    # Verify that the flow finishes
    assert result["type"] == data_entry_flow.FlowResultType.CREATE_ENTRY
    assert result["title"] == entry.title

    # Verify that the options were updated
    assert entry.options == {UPDATE: True, SENSOR: False, SWITCH: True}

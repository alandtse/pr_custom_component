"""Test PRCustomComponent switch."""

from homeassistant.components.switch import (
    DOMAIN as SWITCH_DOMAIN,
    SERVICE_TURN_OFF,
    SERVICE_TURN_ON,
)
from homeassistant.const import ATTR_ENTITY_ID, STATE_OFF, STATE_ON

from custom_components.pr_custom_component.const import DOMAIN

SWITCH_ENTITY_ID = f"{SWITCH_DOMAIN}.tesla_pr_46558_auto_update"


async def test_switch_services(hass, bypass_get_data, mock_config_entry):
    """Test the auto update switch toggles the API client's auto_update flag."""
    mock_config_entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    coordinator = hass.data[DOMAIN][mock_config_entry.entry_id]

    await hass.services.async_call(
        SWITCH_DOMAIN,
        SERVICE_TURN_OFF,
        service_data={ATTR_ENTITY_ID: SWITCH_ENTITY_ID},
        blocking=True,
    )
    assert coordinator.api.auto_update is False
    assert hass.states.get(SWITCH_ENTITY_ID).state == STATE_OFF

    await hass.services.async_call(
        SWITCH_DOMAIN,
        SERVICE_TURN_ON,
        service_data={ATTR_ENTITY_ID: SWITCH_ENTITY_ID},
        blocking=True,
    )
    assert coordinator.api.auto_update is True
    assert hass.states.get(SWITCH_ENTITY_ID).state == STATE_ON

    assert await hass.config_entries.async_unload(mock_config_entry.entry_id)
    await hass.async_block_till_done()

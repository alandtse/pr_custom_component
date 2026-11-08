"""Test PRCustomComponent update."""
from homeassistant.const import ATTR_ENTITY_ID
from homeassistant.components.update import (
    DOMAIN as UPDATE_DOMAIN,
    SERVICE_INSTALL,
    UpdateEntityFeature
)
from unittest.mock import patch

from .const import MOCK_PR_RESPONSE, TEST_ENTITY_ID


def test_update_entity_initialization(hass, setup_update_entity):
    """Test update entity initialization and initial properties."""
    update_entity, coordinator = setup_update_entity

    # Test initial properties
    assert update_entity.supported_features == UpdateEntityFeature.INSTALL
    assert update_entity.installed_version == coordinator.api.installed_version
    assert update_entity.latest_version == coordinator.api.latest_version

    # Test that update entity is set up correctly
    assert hass.states.get(f"{UPDATE_DOMAIN}.{TEST_ENTITY_ID}") is not None


def test_version_property_changes(setup_update_entity):
    """Test version property changes."""
    update_entity, coordinator = setup_update_entity

    # Test property changes
    with patch.object(coordinator.api, '_installed_version', new="1.0.0"), \
         patch.object(coordinator.api, '_latest_version', new="1.1.0"):
        # Verify that the update entity properties reflect the API client changes
        assert update_entity.installed_version == "1.0.0"
        assert update_entity.latest_version == "1.1.0"


async def test_async_install_method(setup_update_entity):
    """Test async_install method."""
    update_entity, coordinator = setup_update_entity

    # Test async_update method
    with patch.object(coordinator.api, 'async_update_data') as mock_update:
        mock_update.return_value = MOCK_PR_RESPONSE
        result = await update_entity.async_install(
            version=None,
            backup=False,
        )
        assert result == MOCK_PR_RESPONSE
        assert mock_update.called
        assert mock_update.call_args[1]["download"] is True

async def test_async_install_service(hass, setup_update_entity):
    """Test async_install service."""
    update_entity, coordinator = setup_update_entity

    with patch.object(coordinator.api, '_installed_version', "2.0.0"), \
        patch.object(coordinator.api, '_latest_version', "2.1.0"), \
        patch.object(coordinator.api, 'async_update_data') as mock_update:

        # Test async_install method
        await hass.services.async_call(
            UPDATE_DOMAIN,
            SERVICE_INSTALL,
            {ATTR_ENTITY_ID: f"update.{TEST_ENTITY_ID}"},
            blocking=True,
        )

        assert mock_update.called
        assert mock_update.call_args[1]["download"] is True

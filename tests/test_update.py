"""Test PRCustomComponent update."""
import pytest

from homeassistant.const import ATTR_ENTITY_ID
from homeassistant.components.update import SERVICE_INSTALL, UpdateEntityFeature
from unittest.mock import patch

from .const import MOCK_PR_RESPONSE

pytestmark = pytest.mark.asyncio


def test_update_entity_initialization(setup_update_entity):
    """Test update entity initialization and initial properties."""
    update_entity, coordinator = setup_update_entity

    # Test initial properties
    assert update_entity.supported_features == UpdateEntityFeature.INSTALL
    assert update_entity.installed_version == coordinator.api.installed_version
    assert update_entity.latest_version == coordinator.api.latest_version


def test_version_property_changes(setup_update_entity):
    """Test version property changes."""
    update_entity, coordinator = setup_update_entity

    # Test property changes
    with patch.object(coordinator.api, '_installed_version', new="1.0.0"), \
         patch.object(coordinator.api, '_latest_version', new="1.1.0"):
        # Verify that the update entity properties reflect the API client changes
        assert update_entity.installed_version == "1.0.0"
        assert update_entity.latest_version == "1.1.0"


async def test_async_update_method(setup_update_entity):
    """Test async_update method."""
    update_entity, coordinator = setup_update_entity

    # Test async_update method
    with patch.object(coordinator.api, 'async_update_data') as mock_update:
        mock_update.return_value = MOCK_PR_RESPONSE
        result = await update_entity.async_update()
        assert result == MOCK_PR_RESPONSE
        assert mock_update.called
        assert mock_update.call_args[1]["download"] is True

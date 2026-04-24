"""Support for Geist PDU sensors."""
from __future__ import annotations

from homeassistant.components.sensor import SensorEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import GeistPDUDataUpdateCoordinator
from . import GeistPDUConfigEntry

async def async_setup_entry(
    hass: HomeAssistant,
    entry: GeistPDUConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Geist PDU sensors based on a config entry."""
    coordinator = entry.runtime_data
    # async_add_entities([GeistPDUSensor(coordinator)])

class GeistPDUEntity(CoordinatorEntity[GeistPDUDataUpdateCoordinator]):
    """Base class for Geist PDU entities."""
    
    _attr_has_entity_name = True

    def __init__(self, coordinator: GeistPDUDataUpdateCoordinator) -> None:
        """Initialize the entity."""
        super().__init__(coordinator)
        self._attr_device_info = {
            "identifiers": {(DOMAIN, coordinator.entry.entry_id)},
            "name": "Geist PDU",
            "manufacturer": "Geist",
        }

class GeistPDUSensor(GeistPDUEntity, SensorEntity):
    """Representation of a Geist PDU sensor."""
    # Implementation details would go here

"""Base entity for Geist PDU."""
from __future__ import annotations

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import GeistPDUDataUpdateCoordinator


class GeistPDUEntity(CoordinatorEntity[GeistPDUDataUpdateCoordinator]):
    """Base class for Geist PDU entities."""

    _attr_has_entity_name = True

    def __init__(self, coordinator: GeistPDUDataUpdateCoordinator) -> None:
        """Initialize the entity."""
        super().__init__(coordinator)
        device_info = coordinator.device_info
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, coordinator.device_id)},
            name=device_info.get("label", "Geist PDU"),
            manufacturer="Geist",
            model=device_info.get("model", "Upgradable rPDU"),
            sw_version=device_info.get("version"),
            serial_number=device_info.get("serialNumber"),
        )

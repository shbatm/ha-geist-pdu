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
        # The PDU device itself is registered during setup.
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, coordinator.device_id)},
        )


class GeistPDUOutletEntity(GeistPDUEntity):
    """Base class for Geist PDU outlet entities."""

    def __init__(
        self, coordinator: GeistPDUDataUpdateCoordinator, outlet_id: str
    ) -> None:
        """Initialize the outlet entity."""
        super().__init__(coordinator)
        self._outlet_id = outlet_id
        device_id = coordinator.device_id

        outlet_data = (
            coordinator.data.get("dev", {})
            .get(device_id, {})
            .get("outlet", {})
            .get(outlet_id, {})
        )
        label = outlet_data.get("label", f"Outlet {int(outlet_id) + 1}")

        # Sub-device for the outlet
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, f"{device_id}_outlet_{outlet_id}")},
            name=label,
            manufacturer="Geist",
            model="PDU Outlet",
            via_device_id=coordinator.pdu_device_entry_id,
        )

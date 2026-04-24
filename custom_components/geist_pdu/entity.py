"""Base entity for Geist PDU."""
from __future__ import annotations

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import CONF_URL, DOMAIN
from .coordinator import GeistPDUDataUpdateCoordinator


class GeistPDUEntity(CoordinatorEntity[GeistPDUDataUpdateCoordinator]):
    """Base class for Geist PDU entities."""

    _attr_has_entity_name = True

    def __init__(self, coordinator: GeistPDUDataUpdateCoordinator) -> None:
        """Initialize the entity."""
        super().__init__(coordinator)
        device_id = coordinator.device_id
        sys_info = coordinator.device_info
        dev_data = coordinator.data.get("dev", {}).get(device_id, {})

        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, device_id)},
            name=dev_data.get("label", sys_info.get("label", "Geist PDU")),
            manufacturer="Geist",
            model=sys_info.get("model", "Upgradable rPDU"),
            sw_version=sys_info.get("version"),
            serial_number=sys_info.get("serialNumber"),
            configuration_url=coordinator.entry.data[CONF_URL],
        )

class GeistPDUOutletEntity(GeistPDUEntity):
    """Base class for Geist PDU outlet entities."""

    def __init__(self, coordinator: GeistPDUDataUpdateCoordinator, outlet_id: str) -> None:
        """Initialize the outlet entity."""
        super().__init__(coordinator)
        self._outlet_id = outlet_id
        device_id = coordinator.device_id

        outlet_data = coordinator.data.get("dev", {}).get(device_id, {}).get("outlet", {}).get(outlet_id, {})
        label = outlet_data.get("label", f"Outlet {int(outlet_id) + 1}")

        # Sub-device for the outlet
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, f"{device_id}_outlet_{outlet_id}")},
            name=label,
            manufacturer="Geist",
            model="PDU Outlet",
            via_device=(DOMAIN, device_id),
        )

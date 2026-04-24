"""Support for Geist PDU buttons."""
from __future__ import annotations

from typing import TYPE_CHECKING

from homeassistant.components.button import ButtonEntity

from .entity import GeistPDUEntity

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant
    from homeassistant.helpers.entity_platform import AddEntitiesCallback

    from . import GeistPDUConfigEntry
    from .coordinator import GeistPDUDataUpdateCoordinator

async def async_setup_entry(
    hass: HomeAssistant,
    entry: GeistPDUConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Geist PDU buttons based on a config entry."""
    coordinator = entry.runtime_data
    device_id = coordinator.device_id
    if not device_id:
        return

    data = coordinator.data[device_id]
    outlets = data.get("outlet", {})

    entities = []
    for o_idx in outlets:
        entities.append(GeistPDUOutletButton(coordinator, o_idx, "reboot"))
        entities.append(GeistPDUOutletButton(coordinator, o_idx, "cancel"))

    async_add_entities(entities)

class GeistPDUOutletButton(GeistPDUEntity, ButtonEntity):
    """Representation of a Geist PDU outlet control button."""

    def __init__(self, coordinator: GeistPDUDataUpdateCoordinator, outlet_id: str, action: str) -> None:
        """Initialize the button."""
        super().__init__(coordinator)
        self._outlet_id = outlet_id
        self._action = action
        self._attr_unique_id = f"{coordinator.device_id}_outlet_{outlet_id}_{action}_button"

        # Get label from initial data if possible
        device_id = coordinator.device_id
        outlet_data = coordinator.data.get(device_id, {}).get("outlet", {}).get(outlet_id, {})
        label = outlet_data.get("label", f"Outlet {int(outlet_id) + 1}")

        if action == "reboot":
            self._attr_name = f"{label} Reboot"
            self._attr_icon = "mdi:restart"
        else:
            self._attr_name = f"{label} Cancel"
            self._attr_icon = "mdi:cancel"

    async def async_press(self) -> None:
        """Handle the button press."""
        await self.coordinator.async_send_command(self._outlet_id, self._action)

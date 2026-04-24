"""Support for Geist PDU buttons."""
from __future__ import annotations

from typing import TYPE_CHECKING

from homeassistant.components.button import ButtonEntity
from homeassistant.const import EntityCategory

from .entity import GeistPDUOutletEntity

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

    dev_data = coordinator.data.get("dev", {}).get(device_id, {})
    outlets = dev_data.get("outlet", {})

    entities = []
    for o_idx in outlets:
        entities.append(GeistPDUOutletButton(coordinator, o_idx, "reboot"))
        entities.append(GeistPDUOutletButton(coordinator, o_idx, "cancel"))

    async_add_entities(entities)

class GeistPDUOutletButton(GeistPDUOutletEntity, ButtonEntity):
    """Representation of a Geist PDU outlet control button."""

    _attr_entity_registry_enabled_default = False
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(self, coordinator: GeistPDUDataUpdateCoordinator, outlet_id: str, action: str) -> None:
        """Initialize the button."""
        super().__init__(coordinator, outlet_id)
        self._action = action
        self._attr_unique_id = f"{coordinator.device_id}_outlet_{outlet_id}_{action}_button"

        if action == "reboot":
            self._attr_name = "Reboot"
            self._attr_icon = "mdi:restart"
        else:
            self._attr_name = "Cancel"
            self._attr_icon = "mdi:cancel"

    async def async_press(self) -> None:
        """Handle the button press."""
        await self.coordinator.async_send_command(self._outlet_id, self._action)

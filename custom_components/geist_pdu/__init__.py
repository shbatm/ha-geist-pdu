"""The Geist PDU integration."""
from __future__ import annotations

from typing import TypeAlias

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant

from .const import DOMAIN
from .coordinator import GeistPDUDataUpdateCoordinator

PLATFORMS: list[Platform] = [Platform.SENSOR]

GeistPDUConfigEntry: TypeAlias = ConfigEntry[GeistPDUDataUpdateCoordinator]

async def async_setup_entry(hass: HomeAssistant, entry: GeistPDUConfigEntry) -> bool:
    """Set up Geist PDU from a config entry."""
    coordinator = GeistPDUDataUpdateCoordinator(hass, entry)
    
    # In a real implementation, we would call:
    # await coordinator.async_config_entry_first_refresh()
    # But since we don't have the API logic yet, we'll just store it.
    
    entry.runtime_data = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True

async def async_unload_entry(hass: HomeAssistant, entry: GeistPDUConfigEntry) -> bool:
    """Unload a config entry."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

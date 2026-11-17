"""The Geist PDU integration."""

from __future__ import annotations

from typing import TYPE_CHECKING, TypeAlias

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform

from .coordinator import GeistPDUDataUpdateCoordinator

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant

PLATFORMS: list[Platform] = [Platform.SENSOR, Platform.SWITCH, Platform.BUTTON]

GeistPDUConfigEntry: TypeAlias = ConfigEntry[GeistPDUDataUpdateCoordinator]


async def async_setup_entry(hass: HomeAssistant, entry: GeistPDUConfigEntry) -> None:
    """Set up Geist PDU from a config entry."""
    coordinator = GeistPDUDataUpdateCoordinator(hass, entry)

    # Perform first refresh
    await coordinator.async_config_entry_first_refresh()
    coordinator.async_register_pdu_device()

    entry.runtime_data = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)


async def async_unload_entry(hass: HomeAssistant, entry: GeistPDUConfigEntry) -> None:
    """Unload a config entry."""
    await hass.config_entries.async_unload_platforms_or_raise(entry, PLATFORMS)

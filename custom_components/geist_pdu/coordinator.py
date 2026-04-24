"""Data update coordinator for Geist PDU."""
from __future__ import annotations

from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import DOMAIN, LOGGER, SCAN_INTERVAL

class GeistPDUDataUpdateCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Geist PDU data update coordinator."""

    def __init__(self, hass: HomeAssistant, entry) -> None:
        """Initialize Geist PDU data update coordinator."""
        super().__init__(
            hass,
            LOGGER,
            name=DOMAIN,
            update_interval=SCAN_INTERVAL,
        )
        self.entry = entry

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch data from Geist PDU."""
        try:
            # Placeholder for actual data fetching logic
            return {}
        except Exception as err:
            raise UpdateFailed(f"Error communicating with Geist PDU: {err}") from err

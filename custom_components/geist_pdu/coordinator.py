"""Data update coordinator for Geist PDU."""
from __future__ import annotations

from http import HTTPStatus
from typing import TYPE_CHECKING, Any

import async_timeout
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME, CONF_VERIFY_SSL
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import CONF_HOST, DOMAIN, LOGGER, SCAN_INTERVAL

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant

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
        self.device_id: str | None = None
        self.device_info: dict[str, Any] = {}

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch data from Geist PDU."""
        session = async_get_clientsession(
            self.hass, verify_ssl=self.entry.data.get(CONF_VERIFY_SSL, False)
        )
        host = self.entry.data[CONF_HOST]

        # Use credentials from config entry
        username = self.entry.data[CONF_USERNAME]
        password = self.entry.data[CONF_PASSWORD]

        try:
            async with async_timeout.timeout(10):
                # 1. Fetch system info for device metadata (model, SN)
                sys_resp = await session.post(
                    f"https://{host}/api/sys",
                    json={"username": username, "password": password, "cmd": "get"}
                )
                if sys_resp.status == HTTPStatus.OK:
                    sys_json = await sys_resp.json()
                    if sys_json.get("status") != "fail":
                        self.device_info = sys_json.get("data", {})

                # 2. Fetch full device dump
                dev_resp = await session.post(
                    f"https://{host}/api/dev",
                    json={"username": username, "password": password, "cmd": "get"}
                )
                if dev_resp.status != HTTPStatus.OK:
                    raise UpdateFailed(f"HTTP error: {dev_resp.status}")

                res_json = await dev_resp.json()
                if res_json.get("status") == "fail":
                    raise UpdateFailed(f"API failure: {res_json.get('message')}")

                data = res_json.get("data", {})
                if not data:
                    raise UpdateFailed("No data returned")

                # The data is keyed by device ID (e.g. A1F8340B851900C3)
                if not self.device_id:
                    self.device_id = next(iter(data.keys()))

                return data
        except Exception as err:
            if isinstance(err, UpdateFailed):
                raise
            raise UpdateFailed(f"Communication error: {err}") from err

"""Data update coordinator for Geist PDU."""
from __future__ import annotations

import asyncio
from http import HTTPStatus
from typing import TYPE_CHECKING, Any

import aiohttp
import async_timeout
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME, CONF_VERIFY_SSL
from homeassistant.exceptions import HomeAssistantError
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
        username = self.entry.data[CONF_USERNAME]
        password = self.entry.data[CONF_PASSWORD]

        payload = {"username": username, "password": password, "cmd": "get"}

        try:
            async with async_timeout.timeout(10):
                # Run requests in parallel to save time
                sys_task = session.post(f"https://{host}/api/sys", json=payload)
                dev_task = session.post(f"https://{host}/api/dev", json=payload)

                responses = await asyncio.gather(sys_task, dev_task, return_exceptions=True)

                # Handle sys response
                if not isinstance(responses[0], Exception) and responses[0].status == HTTPStatus.OK:
                    sys_json = await responses[0].json()
                    if sys_json.get("status") != "fail":
                        self.device_info = sys_json.get("data", {})

                # Handle dev response
                dev_resp = responses[1]
                if isinstance(dev_resp, Exception):
                    raise dev_resp

                if dev_resp.status != HTTPStatus.OK:
                    raise UpdateFailed(f"HTTP error: {dev_resp.status}")

                res_json = await dev_resp.json()
                if res_json.get("status") == "fail":
                    raise UpdateFailed(f"API failure: {res_json.get('message')}")

                data = res_json.get("data", {})
                if not data:
                    raise UpdateFailed("No data returned")

                # The data is keyed by device ID
                if not self.device_id:
                    self.device_id = next(iter(data.keys()))

                return data
        except (asyncio.TimeoutError, async_timeout.TimeoutError) as err:
            raise UpdateFailed("Timeout communicating with Geist PDU") from err
        except Exception as err:
            if isinstance(err, UpdateFailed):
                raise
            raise UpdateFailed(f"Communication error: {err}") from err

    async def async_send_command(self, outlet_id: str, action: str) -> None:
        """Send a control command to the PDU."""
        if not self.device_id:
            raise HomeAssistantError("Device ID not populated")

        host = self.entry.data[CONF_HOST]
        username = self.entry.data[CONF_USERNAME]
        password = self.entry.data[CONF_PASSWORD]

        url = f"https://{host}/api/dev/{self.device_id}/outlet/{outlet_id}"
        payload = {
            "username": username,
            "password": password,
            "cmd": "control",
            "data": {"action": action, "delay": False},
        }

        session = async_get_clientsession(
            self.hass, verify_ssl=self.entry.data.get(CONF_VERIFY_SSL, False)
        )

        try:
            async with async_timeout.timeout(10):
                response = await session.post(url, json=payload)
                if response.status != HTTPStatus.OK:
                    raise HomeAssistantError(f"HTTP error sending {action} to outlet {outlet_id}: {response.status}")

                res_json = await response.json()
                if res_json.get("status") == "fail":
                    raise HomeAssistantError(f"API failure sending {action} to outlet {outlet_id}: {res_json.get('message')}")

                await self.async_request_refresh()

        except (aiohttp.ClientError, asyncio.TimeoutError, async_timeout.TimeoutError) as err:
            raise HomeAssistantError(f"Communication error sending {action} to outlet {outlet_id}: {err}") from err

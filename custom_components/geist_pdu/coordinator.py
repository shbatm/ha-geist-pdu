"""Data update coordinator for Geist PDU."""
from __future__ import annotations

import asyncio
from http import HTTPStatus
from typing import TYPE_CHECKING, Any

import aiohttp
import async_timeout
from homeassistant.const import CONF_PASSWORD, CONF_URL, CONF_USERNAME, CONF_VERIFY_SSL
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import DOMAIN, LOGGER, SCAN_INTERVAL

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
        self.alarm_data: dict[str, Any] = {}

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch data from Geist PDU."""
        session = async_get_clientsession(
            self.hass, verify_ssl=self.entry.data.get(CONF_VERIFY_SSL, False)
        )
        # Use host if url not yet available (migration/fallback)
        base_url = self.entry.data.get(CONF_URL, f"https://{self.entry.data.get('host')}")
        username = self.entry.data[CONF_USERNAME]
        password = self.entry.data[CONF_PASSWORD]

        payload = {"username": username, "password": password, "cmd": "get"}

        try:
            async with async_timeout.timeout(15):
                tasks = []
                # Only fetch sys if not already fetched
                if not self.device_info:
                    tasks.append(session.post(f"{base_url}/api/sys", json=payload))
                else:
                    tasks.append(asyncio.sleep(0)) # placeholder

                tasks.append(session.post(f"{base_url}/api/dev", json=payload))
                tasks.append(session.post(f"{base_url}/api/state", json=payload))

                responses = await asyncio.gather(*tasks, return_exceptions=True)

                # Handle sys response
                if not self.device_info and not isinstance(responses[0], Exception) and responses[0].status == HTTPStatus.OK:
                    sys_json = await responses[0].json()
                    if sys_json.get("status") != "fail":
                        self.device_info = sys_json.get("data", {})

                # Handle dev response
                dev_resp = responses[1]
                if isinstance(dev_resp, Exception):
                    raise dev_resp

                if dev_resp.status != HTTPStatus.OK:
                    raise UpdateFailed(f"HTTP error fetching dev: {dev_resp.status}")

                dev_json = await dev_resp.json()
                if dev_json.get("status") == "fail":
                    raise UpdateFailed(f"API failure fetching dev: {dev_json.get('message')}")

                dev_data = dev_json.get("data", {})
                if not dev_data:
                    raise UpdateFailed("No device data returned")

                if not self.device_id:
                    self.device_id = next(iter(dev_data.keys()))

                # Handle state response
                state_resp = responses[2]
                state_data = {}
                if not isinstance(state_resp, Exception) and state_resp.status == HTTPStatus.OK:
                    state_json = await state_resp.json()
                    if state_json.get("status") != "fail":
                        state_data = state_json.get("data", {})

                # If alarms/warnings active, fetch triggers
                warn_count = state_data.get("warnCount", 0)
                alarm_count = state_data.get("alarmCount", 0)

                if warn_count > 0 or alarm_count > 0:
                    trigger_resp = await session.post(f"{base_url}/api/alarm/trigger", json=payload)
                    if trigger_resp.status == HTTPStatus.OK:
                        trigger_json = await trigger_resp.json()
                        self.alarm_data = trigger_json.get("data", {})
                else:
                    self.alarm_data = {}

                return {
                    "dev": dev_data,
                    "state": state_data,
                    "alarms": self.alarm_data,
                }
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

        base_url = self.entry.data.get(CONF_URL, f"https://{self.entry.data.get('host')}")
        username = self.entry.data[CONF_USERNAME]
        password = self.entry.data[CONF_PASSWORD]

        url = f"{base_url}/api/dev/{self.device_id}/outlet/{outlet_id}"
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

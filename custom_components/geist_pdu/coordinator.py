"""Data update coordinator for Geist PDU."""
from __future__ import annotations

import asyncio
from http import HTTPStatus
from typing import TYPE_CHECKING, Any

import aiohttp
from homeassistant.const import CONF_PASSWORD, CONF_URL, CONF_USERNAME, CONF_VERIFY_SSL
from homeassistant.core import callback
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import DOMAIN, LOGGER, SCAN_INTERVAL

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant

    from . import GeistPDUConfigEntry


class GeistPDUDataUpdateCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Geist PDU data update coordinator."""

    config_entry: GeistPDUConfigEntry

    def __init__(self, hass: HomeAssistant, entry: GeistPDUConfigEntry) -> None:
        """Initialize Geist PDU data update coordinator."""
        super().__init__(
            hass,
            LOGGER,
            config_entry=entry,
            name=DOMAIN,
            update_interval=SCAN_INTERVAL,
        )
        self.device_id: str | None = None
        self.device_info: dict[str, Any] = {}
        self.alarm_data: dict[str, Any] = {}
        self.pdu_device_entry_id: str | None = None

    @callback
    def async_register_pdu_device(self) -> None:
        """Register the PDU device, so outlet devices can link to it by id."""
        if not self.device_id:
            raise HomeAssistantError("Device ID not populated")
        dev_data = self.data.get("dev", {}).get(self.device_id, {})
        device = dr.async_get(self.hass).async_get_or_create(
            config_entry_id=self.config_entry.entry_id,
            identifiers={(DOMAIN, self.device_id)},
            name=dev_data.get("label", self.device_info.get("label", "Geist PDU")),
            manufacturer="Geist",
            model=self.device_info.get("model", "Upgradable rPDU"),
            sw_version=self.device_info.get("version"),
            serial_number=self.device_info.get("serialNumber"),
            configuration_url=self.config_entry.data[CONF_URL],
        )
        self.pdu_device_entry_id = device.id

    def _session(self) -> aiohttp.ClientSession:
        """Return the shared client session for this PDU."""
        return async_get_clientsession(
            self.hass, verify_ssl=self.config_entry.data.get(CONF_VERIFY_SSL, False)
        )

    def _payload(self, cmd: str) -> dict[str, Any]:
        """Return a request body carrying the credentials."""
        return {
            "username": self.config_entry.data[CONF_USERNAME],
            "password": self.config_entry.data[CONF_PASSWORD],
            "cmd": cmd,
        }

    async def _async_post(
        self, path: str, payload: dict[str, Any]
    ) -> tuple[int, Any]:
        """POST to the PDU API; return the status and, when OK, the JSON body."""
        url = f"{self.config_entry.data[CONF_URL]}{path}"
        async with self._session().post(url, json=payload) as response:
            if response.status != HTTPStatus.OK:
                return response.status, None
            return response.status, await response.json()

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch data from Geist PDU."""
        payload = self._payload("get")

        try:
            async with asyncio.timeout(15):
                # /api/sys is static, so it is only fetched until it succeeds.
                sys_result, dev_result, state_result = await asyncio.gather(
                    self._async_post("/api/sys", payload)
                    if not self.device_info
                    else asyncio.sleep(0),
                    self._async_post("/api/dev", payload),
                    self._async_post("/api/state", payload),
                    return_exceptions=True,
                )

                if (
                    not self.device_info
                    and isinstance(sys_result, tuple)
                    and (sys_json := sys_result[1]) is not None
                    and sys_json.get("status") != "fail"
                ):
                    self.device_info = sys_json.get("data", {})

                if isinstance(dev_result, BaseException):
                    raise dev_result
                dev_status, dev_json = dev_result
                if dev_json is None:
                    raise UpdateFailed(f"HTTP error fetching dev: {dev_status}")
                if dev_json.get("status") == "fail":
                    raise UpdateFailed(f"API failure fetching dev: {dev_json.get('message')}")

                dev_data = dev_json.get("data", {})
                if not dev_data:
                    raise UpdateFailed("No device data returned")

                if not self.device_id:
                    self.device_id = next(iter(dev_data.keys()))

                state_data = {}
                if (
                    isinstance(state_result, tuple)
                    and (state_json := state_result[1]) is not None
                    and state_json.get("status") != "fail"
                ):
                    state_data = state_json.get("data", {})

                # If alarms/warnings are active, fetch the triggers
                if state_data.get("warnCount", 0) > 0 or state_data.get("alarmCount", 0) > 0:
                    _, trigger_json = await self._async_post("/api/alarm/trigger", payload)
                    if trigger_json is not None:
                        self.alarm_data = trigger_json.get("data", {})
                else:
                    self.alarm_data = {}

                return {
                    "dev": dev_data,
                    "state": state_data,
                    "alarms": self.alarm_data,
                }
        except TimeoutError as err:
            raise UpdateFailed("Timeout communicating with Geist PDU") from err
        except UpdateFailed:
            raise
        except Exception as err:
            raise UpdateFailed(f"Communication error: {err}") from err

    async def async_send_command(self, outlet_id: str, action: str) -> None:
        """Send a control command to the PDU."""
        if not self.device_id:
            raise HomeAssistantError("Device ID not populated")

        payload = self._payload("control")
        payload["data"] = {"action": action, "delay": False}

        try:
            async with asyncio.timeout(10):
                status, res_json = await self._async_post(
                    f"/api/dev/{self.device_id}/outlet/{outlet_id}", payload
                )
        except (aiohttp.ClientError, TimeoutError) as err:
            raise HomeAssistantError(f"Communication error sending {action} to outlet {outlet_id}: {err}") from err

        if res_json is None:
            raise HomeAssistantError(f"HTTP error sending {action} to outlet {outlet_id}: {status}")
        if res_json.get("status") == "fail":
            raise HomeAssistantError(f"API failure sending {action} to outlet {outlet_id}: {res_json.get('message')}")

        await self.async_request_refresh()

"""Support for Geist PDU switches."""
from __future__ import annotations

from http import HTTPStatus
from typing import TYPE_CHECKING, Any

import aiohttp
import async_timeout
from homeassistant.components.switch import SwitchEntity
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME, CONF_VERIFY_SSL
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import CONF_HOST, LOGGER
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
    """Set up Geist PDU switches based on a config entry."""
    coordinator = entry.runtime_data
    device_id = coordinator.device_id
    if not device_id:
        return

    data = coordinator.data[device_id]
    outlets = data.get("outlet", {})

    async_add_entities([
        GeistPDUOutletSwitch(coordinator, o_idx)
        for o_idx in outlets
    ])

class GeistPDUOutletSwitch(GeistPDUEntity, SwitchEntity):
    """Representation of a Geist PDU outlet switch."""

    def __init__(self, coordinator: GeistPDUDataUpdateCoordinator, outlet_id: str) -> None:
        """Initialize the switch."""
        super().__init__(coordinator)
        self._outlet_id = outlet_id
        self._attr_unique_id = f"{coordinator.device_id}_outlet_{outlet_id}_switch"

        # Get label from initial data if possible
        device_id = coordinator.device_id
        outlet_data = coordinator.data.get(device_id, {}).get("outlet", {}).get(outlet_id, {})
        label = outlet_data.get("label", f"Outlet {int(outlet_id) + 1}")
        self._attr_name = label

    @property
    def is_on(self) -> bool | None:
        """Return True if entity is on."""
        device_id = self.coordinator.device_id
        if not device_id:
            return None

        outlet_data = self.coordinator.data.get(device_id, {}).get("outlet", {}).get(self._outlet_id, {})
        state = outlet_data.get("state")
        return state in ("on", "off2on")

    async def _send_command(self, action: str) -> None:
        """Send a control command to the PDU."""
        host = self.coordinator.entry.data[CONF_HOST]
        username = self.coordinator.entry.data[CONF_USERNAME]
        password = self.coordinator.entry.data[CONF_PASSWORD]
        device_id = self.coordinator.device_id

        url = f"https://{host}/api/dev/{device_id}/outlet/{self._outlet_id}"
        payload = {
            "username": username,
            "password": password,
            "cmd": "control",
            "data": {"action": action, "delay": False},
        }

        session = async_get_clientsession(
            self.hass, verify_ssl=self.coordinator.entry.data.get(CONF_VERIFY_SSL, False)
        )

        try:
            async with async_timeout.timeout(10):
                response = await session.post(url, json=payload)
                if response.status != HTTPStatus.OK:
                    LOGGER.error("Error sending command %s to outlet %s: %s", action, self._outlet_id, response.status)
                    return

                res_json = await response.json()
                if res_json.get("status") == "fail":
                    LOGGER.error("API failed sending command %s to outlet %s: %s", action, self._outlet_id, res_json.get("message"))
                    return

                await self.coordinator.async_request_refresh()

        except (aiohttp.ClientError, async_timeout.TimeoutError) as err:
            LOGGER.error("Exception sending command %s to outlet %s: %s", action, self._outlet_id, err)

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the outlet on."""
        await self._send_command("on")

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the outlet off."""
        await self._send_command("off")

"""Support for Geist PDU buttons."""
from __future__ import annotations

from http import HTTPStatus
from typing import TYPE_CHECKING

import aiohttp
import async_timeout
from homeassistant.components.button import ButtonEntity
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
        host = self.coordinator.entry.data[CONF_HOST]
        username = self.coordinator.entry.data[CONF_USERNAME]
        password = self.coordinator.entry.data[CONF_PASSWORD]
        device_id = self.coordinator.device_id

        url = f"https://{host}/api/dev/{device_id}/outlet/{self._outlet_id}"
        payload = {
            "username": username,
            "password": password,
            "cmd": "control",
            "data": {"action": self._action, "delay": False},
        }

        session = async_get_clientsession(
            self.hass, verify_ssl=self.coordinator.entry.data.get(CONF_VERIFY_SSL, False)
        )

        try:
            async with async_timeout.timeout(10):
                response = await session.post(url, json=payload)
                if response.status != HTTPStatus.OK:
                    LOGGER.error("Error sending command %s to outlet %s: %s", self._action, self._outlet_id, response.status)
                    return

                res_json = await response.json()
                if res_json.get("status") == "fail":
                    LOGGER.error("API failed sending command %s to outlet %s: %s", self._action, self._outlet_id, res_json.get("message"))
                    return

                await self.coordinator.async_request_refresh()

        except (aiohttp.ClientError, async_timeout.TimeoutError) as err:
            LOGGER.error("Exception sending command %s to outlet %s: %s", self._action, self._outlet_id, err)

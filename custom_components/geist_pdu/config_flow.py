"""Config flow for Geist PDU integration."""
from __future__ import annotations

from http import HTTPStatus
from typing import TYPE_CHECKING, Any

import aiohttp
import async_timeout
from homeassistant import config_entries
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME, CONF_VERIFY_SSL
from homeassistant.helpers.aiohttp_client import async_get_clientsession
import voluptuous as vol

from .const import CONF_HOST, DOMAIN, LOGGER

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant
    from homeassistant.data_entry_flow import FlowResult

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_HOST): str,
        vol.Required(CONF_USERNAME): str,
        vol.Required(CONF_PASSWORD): str,
        vol.Optional(CONF_VERIFY_SSL, default=False): bool,
    }
)

async def _validate_input(hass: HomeAssistant, data: dict[str, Any]) -> dict[str, Any]:
    """Validate the user input allows us to connect."""
    session = async_get_clientsession(hass, verify_ssl=data.get(CONF_VERIFY_SSL, False))
    url = f"https://{data[CONF_HOST]}/api/dev"

    payload = {
        "username": data[CONF_USERNAME],
        "password": data[CONF_PASSWORD],
        "cmd": "get",
    }

    try:
        async with async_timeout.timeout(10):
            response = await session.post(url, json=payload)
            if response.status == HTTPStatus.UNAUTHORIZED:
                raise InvalidAuth
            if response.status != HTTPStatus.OK:
                raise CannotConnect

            res_json = await response.json()
            if res_json.get("status") == "fail":
                raise InvalidAuth

            device_data = res_json.get("data", {})
            if not device_data:
                raise CannotConnect

            device_id = next(iter(device_data.keys()))
            device_info = device_data[device_id]

            return {
                "title": device_info.get("name", data[CONF_HOST]),
                "unique_id": device_id,
            }

    except (aiohttp.ClientError, async_timeout.TimeoutError) as err:
        LOGGER.error("Error connecting to Geist PDU: %s", err)
        raise CannotConnect from err

class GeistPDUConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Geist PDU."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}
        if user_input is not None:
            try:
                info = await _validate_input(self.hass, user_input)
            except CannotConnect:
                errors["base"] = "cannot_connect"
            except InvalidAuth:
                errors["base"] = "invalid_auth"
            except Exception:  # noqa: BLE001
                LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"
            else:
                await self.async_set_unique_id(info["unique_id"])
                self._abort_if_unique_id_configured()
                return self.async_create_entry(title=info["title"], data=user_input)

        return self.async_show_form(
            step_id="user",
            data_schema=STEP_USER_DATA_SCHEMA,
            errors=errors,
        )

class CannotConnect(config_entries.HomeAssistantError):
    """Error to indicate we cannot connect."""

class InvalidAuth(config_entries.HomeAssistantError):
    """Error to indicate there is invalid auth."""

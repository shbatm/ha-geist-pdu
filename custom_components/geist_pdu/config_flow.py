"""Config flow for Geist PDU integration."""
from __future__ import annotations

import asyncio
from http import HTTPStatus
from typing import TYPE_CHECKING, Any

import aiohttp
from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.const import CONF_PASSWORD, CONF_URL, CONF_USERNAME, CONF_VERIFY_SSL
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.aiohttp_client import async_get_clientsession
import probatio

from .const import DOMAIN, LOGGER

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant

STEP_USER_DATA_SCHEMA = probatio.Schema(
    {
        probatio.Required(CONF_URL): str,
        probatio.Required(CONF_USERNAME): str,
        probatio.Required(probatio.Secret(CONF_PASSWORD)): str,
        probatio.Optional(CONF_VERIFY_SSL, default=False): bool,
    }
)

async def _validate_input(hass: HomeAssistant, data: dict[str, Any]) -> dict[str, Any]:
    """Validate the user input allows us to connect."""
    session = async_get_clientsession(hass, verify_ssl=data.get(CONF_VERIFY_SSL, False))
    url = data[CONF_URL].rstrip("/")
    if not url.startswith(("http://", "https://")):
        # Default to https if not specified for backward compatibility/safety
        url = f"https://{url}"

    endpoint = f"{url}/api/dev"

    payload = {
        "username": data[CONF_USERNAME],
        "password": data[CONF_PASSWORD],
        "cmd": "get",
    }

    try:
        async with (
            asyncio.timeout(10),
            session.post(endpoint, json=payload) as response,
        ):
            if response.status == HTTPStatus.UNAUTHORIZED:
                raise InvalidAuth
            if response.status != HTTPStatus.OK:
                raise CannotConnect
            res_json = await response.json()
    except (aiohttp.ClientError, TimeoutError) as err:
        LOGGER.error("Error connecting to Geist PDU: %s", err)
        raise CannotConnect from err

    if res_json.get("status") == "fail":
        raise InvalidAuth

    device_data = res_json.get("data", {})
    if not device_data:
        raise CannotConnect

    device_id = next(iter(device_data.keys()))
    device_info = device_data[device_id]

    return {
        "title": device_info.get("label", device_info.get("name", url)),
        "unique_id": device_id,
        "url": url,
    }

class GeistPDUConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Geist PDU."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
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
                LOGGER.exception("Unexpected exception during config flow validation")
                errors["base"] = "unknown"
            else:
                user_input[CONF_URL] = info["url"]
                await self.async_set_unique_id(info["unique_id"])
                self._abort_if_unique_id_configured()
                return self.async_create_entry(title=info["title"], data=user_input)

        return self.async_show_form(
            step_id="user",
            data_schema=STEP_USER_DATA_SCHEMA,
            errors=errors,
        )

class CannotConnect(HomeAssistantError):
    """Error to indicate we cannot connect."""

class InvalidAuth(HomeAssistantError):
    """Error to indicate there is invalid auth."""

"""Config flow: enter the controller's IP or myorca-XXXX.local name."""
from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.const import CONF_HOST
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import OrcaClient, OrcaConnectionError, OrcaError
from .const import DOMAIN


class OrcaConfigFlow(ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        errors: dict[str, str] = {}
        if user_input is not None:
            host = user_input[CONF_HOST].strip()
            client = OrcaClient(async_get_clientsession(self.hass), host)
            try:
                status = await client.get_status()
            except OrcaConnectionError:
                errors["base"] = "cannot_connect"
            except OrcaError:
                errors["base"] = "not_orca"
            else:
                await self.async_set_unique_id(status.device_id)
                self._abort_if_unique_id_configured(updates={CONF_HOST: host})
                return self.async_create_entry(
                    title=f"{status.model} {status.device_id}",
                    data={CONF_HOST: host},
                )

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {vol.Required(CONF_HOST, default=(user_input or {}).get(CONF_HOST, "")): str}
            ),
            errors=errors,
        )

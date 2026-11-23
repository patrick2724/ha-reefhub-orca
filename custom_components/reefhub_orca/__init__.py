"""reefhub ORCA (first generation) – local control via the controller's fallback page."""
from __future__ import annotations

import voluptuous as vol

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import OrcaClient
from .const import (
    ATTR_CHANNEL,
    ATTR_POINT_A,
    ATTR_POINT_B,
    ATTR_SPEED,
    DOMAIN,
    PLATFORMS,
    SERVICE_SET_CHANNEL,
)
from .coordinator import OrcaCoordinator

SET_CHANNEL_SCHEMA = vol.Schema(
    {
        vol.Required("device_id"): cv.string,
        vol.Optional(ATTR_CHANNEL, default=1): vol.All(vol.Coerce(int), vol.Range(1, 4)),
        vol.Optional(ATTR_POINT_A): vol.All(vol.Coerce(int), vol.Range(-90, 90)),
        vol.Optional(ATTR_POINT_B): vol.All(vol.Coerce(int), vol.Range(-90, 90)),
        vol.Optional(ATTR_SPEED): vol.All(vol.Coerce(int), vol.Range(10, 250)),
    }
)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    client = OrcaClient(async_get_clientsession(hass), entry.data[CONF_HOST])
    coordinator = OrcaCoordinator(hass, entry, client)
    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    if not hass.services.has_service(DOMAIN, SERVICE_SET_CHANNEL):

        async def _set_channel(call: ServiceCall) -> None:
            device = dr.async_get(hass).async_get(call.data["device_id"])
            target = None
            if device:
                for entry_id in device.config_entries:
                    target = hass.data.get(DOMAIN, {}).get(entry_id) or target
            if target is None:
                raise HomeAssistantError("ORCA: Gerät nicht gefunden")
            await target.async_save_channel(
                call.data[ATTR_CHANNEL],
                call.data.get(ATTR_POINT_A),
                call.data.get(ATTR_POINT_B),
                call.data.get(ATTR_SPEED),
            )

        hass.services.async_register(
            DOMAIN, SERVICE_SET_CHANNEL, _set_channel, schema=SET_CHANNEL_SCHEMA
        )
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    unloaded = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unloaded:
        hass.data[DOMAIN].pop(entry.entry_id)
        if not hass.data[DOMAIN]:
            hass.services.async_remove(DOMAIN, SERVICE_SET_CHANNEL)
    return unloaded

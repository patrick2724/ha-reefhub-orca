"""Rotation on/off per channel."""
from __future__ import annotations

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .entity import OrcaChannelEntity


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    coordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        OrcaRotationSwitch(coordinator, ch) for ch in coordinator.data.channels
    )


class OrcaRotationSwitch(OrcaChannelEntity, SwitchEntity):
    """On = the unit sweeps between point A and B."""

    _attr_translation_key = "rotation"
    _attr_icon = "mdi:rotate-3d-variant"

    def __init__(self, coordinator, channel: int) -> None:
        super().__init__(coordinator, channel, "rotation")

    @property
    def is_on(self) -> bool:
        return self.channel_data.running

    async def async_turn_on(self, **kwargs) -> None:
        await self.coordinator.async_command(self.coordinator.client.start(self.channel))

    async def async_turn_off(self, **kwargs) -> None:
        await self.coordinator.async_command(self.coordinator.client.stop(self.channel))

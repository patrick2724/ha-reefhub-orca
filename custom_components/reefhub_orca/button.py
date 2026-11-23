"""Selftest per channel and controller restart."""
from __future__ import annotations

from homeassistant.components.button import ButtonDeviceClass, ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .entity import OrcaChannelEntity, OrcaEntity


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    coordinator = hass.data[DOMAIN][entry.entry_id]
    entities: list[ButtonEntity] = [
        OrcaSelftestButton(coordinator, ch) for ch in coordinator.data.channels
    ]
    entities.append(OrcaRestartButton(coordinator))
    async_add_entities(entities)


class OrcaSelftestButton(OrcaChannelEntity, ButtonEntity):
    """Calibrate: the unit drives to both end stops."""

    _attr_translation_key = "selftest"
    _attr_icon = "mdi:target"
    _attr_entity_category = EntityCategory.CONFIG

    def __init__(self, coordinator, channel: int) -> None:
        super().__init__(coordinator, channel, "selftest")

    async def async_press(self) -> None:
        await self.coordinator.async_command(self.coordinator.client.selftest(self.channel))


class OrcaRestartButton(OrcaEntity, ButtonEntity):
    """Reboot the controller (units must be selftested afterwards)."""

    _attr_translation_key = "restart"
    _attr_device_class = ButtonDeviceClass.RESTART
    _attr_entity_category = EntityCategory.CONFIG

    def __init__(self, coordinator) -> None:
        super().__init__(coordinator, "restart")

    async def async_press(self) -> None:
        await self.coordinator.async_command(self.coordinator.client.restart())

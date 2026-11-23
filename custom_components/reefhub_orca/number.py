"""Point A, point B and speed per channel."""
from __future__ import annotations

from homeassistant.components.number import NumberEntity, NumberMode
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import DEGREE, EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .entity import OrcaChannelEntity

FIELDS = ("point_a", "point_b", "speed")


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    coordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        OrcaNumber(coordinator, ch, field)
        for ch in coordinator.data.channels
        for field in FIELDS
    )


class OrcaNumber(OrcaChannelEntity, NumberEntity):
    """One setting of a channel; changing it saves on the controller."""

    _attr_mode = NumberMode.BOX
    _attr_entity_category = EntityCategory.CONFIG

    def __init__(self, coordinator, channel: int, field: str) -> None:
        super().__init__(coordinator, channel, field)
        self.field = field
        self._attr_translation_key = field
        if field == "speed":
            self._attr_icon = "mdi:speedometer"
            self._attr_native_step = 1
        else:
            self._attr_icon = "mdi:angle-acute"
            self._attr_native_unit_of_measurement = DEGREE
            self._attr_native_step = 1

    @property
    def native_min_value(self) -> float:
        ch = self.channel_data
        return ch.speed_min if self.field == "speed" else ch.angle_min

    @property
    def native_max_value(self) -> float:
        ch = self.channel_data
        return ch.speed_max if self.field == "speed" else ch.angle_max

    @property
    def native_value(self) -> float | None:
        return getattr(self.channel_data, self.field)

    async def async_set_native_value(self, value: float) -> None:
        await self.coordinator.async_save_channel(self.channel, **{self.field: int(value)})

"""Status texts of controller and channels."""
from __future__ import annotations

from homeassistant.components.sensor import SensorEntity
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
    entities: list[SensorEntity] = [OrcaCloudSensor(coordinator)]
    for ch in coordinator.data.channels:
        entities.append(OrcaChannelText(coordinator, ch, "orca_status", "mdi:information-outline"))
        entities.append(OrcaChannelText(coordinator, ch, "selftest_status", "mdi:check-decagram"))
    async_add_entities(entities)


class OrcaCloudSensor(OrcaEntity, SensorEntity):
    _attr_translation_key = "cloud_status"
    _attr_icon = "mdi:cloud-outline"
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(self, coordinator) -> None:
        super().__init__(coordinator, "cloud_status")

    @property
    def native_value(self) -> str | None:
        return self.coordinator.data.cloud_status


class OrcaChannelText(OrcaChannelEntity, SensorEntity):
    """Raw status text as shown on the controller page."""

    def __init__(self, coordinator, channel: int, field: str, icon: str) -> None:
        super().__init__(coordinator, channel, field)
        self.field = field
        self._attr_translation_key = field
        self._attr_icon = icon
        if field == "selftest_status":
            self._attr_entity_category = EntityCategory.DIAGNOSTIC

    @property
    def native_value(self) -> str | None:
        return getattr(self.channel_data, self.field)

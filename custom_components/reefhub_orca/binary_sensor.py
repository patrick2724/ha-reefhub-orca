"""Calibration OK per channel and cloud connectivity."""
from __future__ import annotations

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
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
    entities: list[BinarySensorEntity] = [OrcaCloudConnected(coordinator)]
    entities.extend(OrcaCalibrated(coordinator, ch) for ch in coordinator.data.channels)
    async_add_entities(entities)


class OrcaCloudConnected(OrcaEntity, BinarySensorEntity):
    _attr_translation_key = "cloud_connected"
    _attr_device_class = BinarySensorDeviceClass.CONNECTIVITY
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(self, coordinator) -> None:
        super().__init__(coordinator, "cloud_connected")

    @property
    def is_on(self) -> bool:
        return self.coordinator.data.cloud_connected


class OrcaCalibrated(OrcaChannelEntity, BinarySensorEntity):
    """Off = unit needs a selftest before it can rotate (e.g. after power loss)."""

    _attr_translation_key = "calibrated"
    _attr_icon = "mdi:check-circle-outline"

    def __init__(self, coordinator, channel: int) -> None:
        super().__init__(coordinator, channel, "calibrated")

    @property
    def is_on(self) -> bool:
        return self.channel_data.selftest_ok

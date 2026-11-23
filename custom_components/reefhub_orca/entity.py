"""Base entities for reefhub ORCA."""
from __future__ import annotations

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, MANUFACTURER
from .coordinator import OrcaCoordinator


class OrcaEntity(CoordinatorEntity[OrcaCoordinator]):
    """Entity attached to the controller device."""

    _attr_has_entity_name = True

    def __init__(self, coordinator: OrcaCoordinator, key: str) -> None:
        super().__init__(coordinator)
        status = coordinator.data
        self._device_id = coordinator.config_entry.unique_id or status.device_id
        self._attr_unique_id = f"{self._device_id}_{key}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, self._device_id)},
            manufacturer=MANUFACTURER,
            model=status.model,
            name=coordinator.config_entry.title,
            sw_version=status.firmware,
            serial_number=status.device_id,
            configuration_url=coordinator.client.base_url,
        )


class OrcaChannelEntity(OrcaEntity):
    """Entity that belongs to one channel (= one rotation unit)."""

    def __init__(self, coordinator: OrcaCoordinator, channel: int, key: str) -> None:
        super().__init__(coordinator, f"ch{channel}_{key}")
        self.channel = channel
        self._attr_translation_placeholders = {"channel": str(channel)}

    @property
    def channel_data(self):
        return self.coordinator.data.channels.get(self.channel)

    @property
    def available(self) -> bool:
        return super().available and self.channel_data is not None

"""Data coordinator for reefhub ORCA."""
from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import OrcaClient, OrcaError, OrcaStatus
from .const import DOMAIN, SCAN_INTERVAL

_LOGGER = logging.getLogger(__name__)


class OrcaCoordinator(DataUpdateCoordinator[OrcaStatus]):
    """Polls the controller's status page."""

    config_entry: ConfigEntry

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry, client: OrcaClient) -> None:
        super().__init__(
            hass,
            _LOGGER,
            config_entry=entry,
            name=f"{DOMAIN} {entry.title}",
            update_interval=SCAN_INTERVAL,
        )
        self.client = client

    async def _async_update_data(self) -> OrcaStatus:
        try:
            return await self.client.get_status()
        except OrcaError as err:
            raise UpdateFailed(str(err)) from err

    async def async_command(self, coro) -> None:
        """Run a command, then refresh the state right away."""
        try:
            await coro
        except OrcaError as err:
            raise HomeAssistantError(f"ORCA: {err}") from err
        await self.async_refresh()

    async def async_save_channel(
        self,
        channel: int,
        point_a: int | None = None,
        point_b: int | None = None,
        speed: int | None = None,
    ) -> None:
        """Change one or more values; missing values keep their current setting."""
        current = self.data.channels.get(channel) if self.data else None
        if current is None:
            raise HomeAssistantError(f"ORCA: Kanal {channel} gibt es nicht")
        new_a = current.point_a if point_a is None else int(point_a)
        new_b = current.point_b if point_b is None else int(point_b)
        new_speed = current.speed if speed is None else int(speed)
        if None in (new_a, new_b, new_speed):
            raise HomeAssistantError("ORCA: aktuelle Werte unbekannt")
        for value, low, high, name in (
            (new_a, current.angle_min, current.angle_max, "Punkt A"),
            (new_b, current.angle_min, current.angle_max, "Punkt B"),
            (new_speed, current.speed_min, current.speed_max, "Geschwindigkeit"),
        ):
            if not low <= value <= high:
                raise HomeAssistantError(f"ORCA: {name} muss zwischen {low} und {high} liegen")
        await self.async_command(
            self.client.save_channel(channel, new_a, new_b, new_speed)
        )

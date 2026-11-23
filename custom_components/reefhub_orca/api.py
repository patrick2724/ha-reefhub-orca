"""Client for the local fallback API of first-generation reefhub ORCA controllers.

The controller has no JSON interface. State is read from the HTML status page
at ``/`` and commands are plain GET/POST requests that answer with a redirect.
"""
from __future__ import annotations

import asyncio
import html as html_lib
import re
from dataclasses import dataclass, field

import aiohttp

DEFAULT_TIMEOUT = 10


class OrcaError(Exception):
    """Base error."""


class OrcaConnectionError(OrcaError):
    """Controller not reachable."""


class OrcaParseError(OrcaError):
    """Status page could not be understood."""


@dataclass
class OrcaChannel:
    """State of one channel / rotation unit."""

    number: int
    selftest_status: str | None = None
    orca_status: str | None = None
    point_a: int | None = None
    point_b: int | None = None
    speed: int | None = None
    angle_min: int = -90
    angle_max: int = 90
    speed_min: int = 10
    speed_max: int = 200

    @property
    def running(self) -> bool:
        return (self.orca_status or "").lower().startswith("running")

    @property
    def selftest_ok(self) -> bool:
        return (self.selftest_status or "").lower().startswith("success")


@dataclass
class OrcaStatus:
    """Parsed status page."""

    firmware: str | None = None
    device_id: str | None = None
    model: str = "ORCA Controller"
    cloud_status: str | None = None
    channels: dict[int, OrcaChannel] = field(default_factory=dict)

    @property
    def cloud_connected(self) -> bool:
        return (self.cloud_status or "").lower().startswith("connected")


_TAG_RE = re.compile(r"<[^>]+>")


def _text(fragment: str) -> str:
    return html_lib.unescape(_TAG_RE.sub("", fragment)).strip()


def _label_value(block: str, label: str) -> str | None:
    """Return the text of the first <span> after ``label:``."""
    match = re.search(
        rf"{re.escape(label)}\s*:\s*<span[^>]*>(.*?)</span>", block, re.S | re.I
    )
    return _text(match.group(1)).rstrip(".") if match else None


def _input_value(block: str, name: str) -> int | None:
    match = re.search(
        rf'<input[^>]*name="{re.escape(name)}"[^>]*>', block, re.S | re.I
    )
    if not match:
        return None
    value = re.search(r'value="([^"]*)"', match.group(0))
    if not value:
        return None
    try:
        return int(float(value.group(1).strip()))
    except ValueError:
        return None


def parse_status(page: str) -> OrcaStatus:
    """Parse the controller's HTML status page."""
    status = OrcaStatus()

    version = re.search(r"Version:\s*([\w.\-]+)\s*\(ID:\s*([^)]+)\)", page)
    if not version:
        raise OrcaParseError("No version/ID found – is this an ORCA controller?")
    status.firmware = version.group(1).strip()
    status.device_id = version.group(2).strip()
    status.cloud_status = _label_value(page, "Cloud-Status")
    if re.search(r"ORCAlight", page, re.I):
        status.model = "ORCAlight Controller"

    # Split the page at every "Channel N" badge; each part holds one channel.
    starts = [
        (m.start(), int(m.group(1)))
        for m in re.finditer(r">\s*Channel\s+(\d+)\s*<", page)
    ]
    for index, (pos, number) in enumerate(starts):
        end = starts[index + 1][0] if index + 1 < len(starts) else len(page)
        block = page[pos:end]
        channel = OrcaChannel(number=number)
        channel.selftest_status = _label_value(block, "Selftest-Status")
        channel.orca_status = _label_value(block, "ORCA-Status")
        channel.point_a = _input_value(block, f"channel{number}_min")
        channel.point_b = _input_value(block, f"channel{number}_max")
        channel.speed = _input_value(block, f"channel{number}_speed")
        speed_range = re.search(
            r"Speed\s*\(min:\s*(\d+)\s*max:\s*(\d+)\)", block, re.I
        )
        if speed_range:
            channel.speed_min = int(speed_range.group(1))
            channel.speed_max = int(speed_range.group(2))
        status.channels[number] = channel

    if not status.channels:
        raise OrcaParseError("No channels found on the status page")
    return status


class OrcaClient:
    """Talks to one controller."""

    def __init__(self, session: aiohttp.ClientSession, host: str) -> None:
        host = host.strip().rstrip("/")
        if not host.startswith(("http://", "https://")):
            host = f"http://{host}"
        self.base_url = host
        self._session = session
        self._lock = asyncio.Lock()

    async def _request(
        self, method: str, path: str, data: dict | None = None
    ) -> str:
        url = f"{self.base_url}{path}"
        async with self._lock:
            try:
                async with self._session.request(
                    method,
                    url,
                    data=data,
                    allow_redirects=False,
                    timeout=aiohttp.ClientTimeout(total=DEFAULT_TIMEOUT),
                ) as resp:
                    if resp.status >= 400:
                        raise OrcaError(f"{method} {path} -> HTTP {resp.status}")
                    return await resp.text(errors="replace")
            except (aiohttp.ClientError, asyncio.TimeoutError) as err:
                raise OrcaConnectionError(f"{method} {path}: {err}") from err

    async def get_status(self) -> OrcaStatus:
        return parse_status(await self._request("GET", "/"))

    async def start(self, channel: int) -> None:
        await self._request("GET", f"/start?channel={channel}")

    async def stop(self, channel: int) -> None:
        await self._request("GET", f"/stop?channel={channel}")

    async def selftest(self, channel: int) -> None:
        await self._request("GET", f"/selftest?channel={channel}")

    async def restart(self) -> None:
        await self._request("GET", "/restart")

    async def save_channel(
        self, channel: int, point_a: int, point_b: int, speed: int
    ) -> None:
        """Save all three values; the controller persists them immediately."""
        await self._request(
            "POST",
            f"/save/channel{channel}",
            data={
                f"channel{channel}_min": str(int(point_a)),
                f"channel{channel}_max": str(int(point_b)),
                f"channel{channel}_speed": str(int(speed)),
            },
        )

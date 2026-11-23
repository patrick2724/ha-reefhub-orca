"""Tests: parser on the real page, client against a fake device, full HA setup."""
from __future__ import annotations

from unittest.mock import patch

import aiohttp
import pytest
from aiohttp.test_utils import TestServer

from homeassistant.const import CONF_HOST
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.reefhub_orca.api import OrcaClient, parse_status
from custom_components.reefhub_orca.const import DOMAIN

from .fake_orca import TEMPLATE, FakeOrca


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations):
    yield


def test_parse_real_page():
    s = parse_status(TEMPLATE)
    assert s.firmware == "1.2.9"
    assert s.device_id == "abcd1234ef"
    assert s.model == "ORCAlight Controller"
    assert s.cloud_connected
    ch = s.channels[1]
    assert list(s.channels) == [1]
    assert (ch.point_a, ch.point_b, ch.speed) == (-90, 90, 100)
    assert (ch.speed_min, ch.speed_max) == (10, 250)
    assert ch.selftest_ok and not ch.running


@pytest.mark.enable_socket
async def test_client_against_fake_http_device():
    fake = FakeOrca()
    async with TestServer(fake.app()) as server, aiohttp.ClientSession() as session:
        client = OrcaClient(session, f"{server.host}:{server.port}")
        await client.start(1)
        assert (await client.get_status()).channels[1].running
        await client.save_channel(1, -30, 45, 150)
        ch = (await client.get_status()).channels[1]
        assert (ch.point_a, ch.point_b, ch.speed) == (-30, 45, 150)
        await client.stop(1)
        assert not (await client.get_status()).channels[1].running


@pytest.fixture
def fake():
    device = FakeOrca()

    async def _request(self, method, path, data=None):
        return device.handle(method, f"http://x{path}", data)

    with patch("custom_components.reefhub_orca.api.OrcaClient._request", _request):
        yield device


async def test_config_flow(hass: HomeAssistant, fake: FakeOrca):
    result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": "user"})
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_HOST: "192.168.1.50"}
    )
    assert result["type"] == "create_entry"
    assert result["title"] == "ORCAlight Controller abcd1234ef"
    assert result["result"].unique_id == "abcd1234ef"


async def test_entities_and_control(hass: HomeAssistant, fake: FakeOrca):
    entry = MockConfigEntry(
        domain=DOMAIN, unique_id="abcd1234ef", title="ORCAlight Controller abcd1234ef",
        data={CONF_HOST: "192.168.1.50"},
    )
    hass.config.language = "de"
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    states = {s.entity_id: s.state for s in hass.states.async_all() if "orcalight" in s.entity_id}
    print("\nENTITIES:")
    for eid in sorted(states):
        print(f"  {eid} = {states[eid]}")

    sw = "switch.orcalight_controller_abcd1234ef_kanal_1_drehung"
    assert states[sw] == "off"
    await hass.services.async_call("switch", "turn_on", {"entity_id": sw}, blocking=True)
    await hass.async_block_till_done()
    assert hass.states.get(sw).state == "on"
    assert fake.running

    speed = "number.orcalight_controller_abcd1234ef_kanal_1_geschwindigkeit"
    await hass.services.async_call("number", "set_value", {"entity_id": speed, "value": 180}, blocking=True)
    await hass.async_block_till_done()
    assert fake.speed == 180 and fake.point_a == -90 and fake.point_b == 90
    assert hass.states.get(speed).state == "180"

    device = dr.async_get(hass).async_get_device(identifiers={(DOMAIN, "abcd1234ef")})
    assert device.sw_version == "1.2.9"
    await hass.services.async_call(
        DOMAIN, "set_channel",
        {"device_id": device.id, "point_a": -45, "point_b": 30},
        blocking=True,
    )
    await hass.async_block_till_done()
    assert (fake.point_a, fake.point_b, fake.speed) == (-45, 30, 180)

    with pytest.raises(Exception):
        await hass.services.async_call("number", "set_value", {"entity_id": speed, "value": 300}, blocking=True)
    assert fake.speed == 180

    await hass.services.async_call("button", "press",
        {"entity_id": "button.orcalight_controller_abcd1234ef_kanal_1_selbsttest"}, blocking=True)
    await hass.async_block_till_done()
    assert "GET /selftest?channel=1" in fake.log
    print("DEVICE LOG:", fake.log)

    assert await hass.config_entries.async_unload(entry.entry_id)

"""A stateful fake ORCAlight that serves the real captured status page."""
from __future__ import annotations

import re
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from aiohttp import web

TEMPLATE = (Path(__file__).parent / "orca_status_fixture.html").read_text()


class FakeOrca:
    def __init__(self) -> None:
        self.running = False
        self.selftest = "Success! Ready to go."
        self.point_a, self.point_b, self.speed = -90, 90, 100
        self.log: list[str] = []

    def page(self) -> str:
        html = TEMPLATE
        html = re.sub(
            r"(ORCA-Status: <span[^>]*>)[^<]*",
            lambda m: m.group(1) + ("Running smoothly." if self.running else "Stopped."),
            html,
        )
        html = re.sub(r"(Selftest-Status: <span[^>]*>)[^<]*", lambda m: m.group(1) + self.selftest, html)
        for name, val in (("min", self.point_a), ("max", self.point_b), ("speed", self.speed)):
            html = re.sub(
                rf'(name="channel1_{name}" id="channel1_{name}" value=")[^"]*',
                lambda m, v=val: m.group(1) + str(v),
                html,
            )
        return html

    def handle(self, method: str, url: str, data: dict | None) -> str:
        parsed = urlparse(url)
        path, query = parsed.path, parse_qs(parsed.query)
        self.log.append(f"{method} {path}{'?' + parsed.query if parsed.query else ''}")
        if path == "/":
            return self.page()
        if path in ("/start", "/stop", "/selftest"):
            if query.get("channel") != ["1"]:
                return ""
            if path == "/start":
                self.running = True
            elif path == "/stop":
                self.running = False
            else:
                self.running = False
                self.selftest = "Success! Ready to go."
            return ""
        if path == "/save/channel1" and method == "POST":
            for key, attr, lo, hi in (
                ("channel1_min", "point_a", -90, 90),
                ("channel1_max", "point_b", -90, 90),
                ("channel1_speed", "speed", 10, 250),
            ):
                try:
                    v = int(data[key])
                except (KeyError, ValueError, TypeError):
                    continue
                if lo <= v <= hi:  # out of range is silently ignored, like the device
                    setattr(self, attr, v)
            return ""
        if path == "/restart":
            self.running = False
            self.selftest = "Pending."
            return ""
        raise web.HTTPNotFound()

    def app(self) -> web.Application:
        async def any_route(request: web.Request) -> web.Response:
            data = dict(await request.post()) if request.method == "POST" else None
            body = self.handle(request.method, str(request.url), data)
            if request.path == "/":
                return web.Response(text=body, content_type="text/html")
            raise web.HTTPFound("/")

        app = web.Application()
        app.router.add_route("*", "/{tail:.*}", any_route)
        return app

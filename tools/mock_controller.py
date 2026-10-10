#!/usr/bin/env python3
"""Small AutoGen X Pro API simulator for integration development."""

from __future__ import annotations

import argparse
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any

DEVICE_ID = "f23a1d4b8c9e0f6572ac001122334455"
PAIRING_CODE = "482731"
ACCESS_TOKEN = "a" * 64


class ControllerState:
    """Mutable state held by the simulator."""

    generator_running = False
    sequence = 0


class Handler(BaseHTTPRequestHandler):
    """Implement the firmware's version-one API contract."""

    server_version = "AutoGenXProSimulator/1"

    def _send(self, status: int, payload: dict[str, Any]) -> None:
        body = json.dumps(payload).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _read_json(self) -> dict[str, Any]:
        length = int(self.headers.get("Content-Length", "0"))
        payload = json.loads(self.rfile.read(length) or b"{}")
        return payload if isinstance(payload, dict) else {}

    def _authenticated(self) -> bool:
        return self.headers.get("Authorization") == f"Bearer {ACCESS_TOKEN}"

    def _require_authentication(self) -> bool:
        if self._authenticated():
            return True
        self._send(401, {"error": "invalid_token"})
        return False

    def do_GET(self) -> None:  # noqa: N802
        if not self._require_authentication():
            return
        if self.path == "/api/v1/info":
            self._send(
                200,
                {
                    "device_id": DEVICE_ID,
                    "name": "AutoGen X Pro 334455",
                    "manufacturer": "DC AutoGen",
                    "model": "AutoGen X Pro",
                    "firmware_version": "3.4.0-ha.simulator",
                    "api_version": "1",
                    "capabilities": ["status", "start_stop"],
                },
            )
            return
        if self.path == "/api/v1/status":
            ControllerState.sequence += 1
            running = ControllerState.generator_running
            self._send(
                200,
                {
                    "device_id": DEVICE_ID,
                    "sequence": ControllerState.sequence,
                    "uptime_seconds": 120,
                    "battery_voltage": 12.7,
                    "charge_current": 8.4 if running else 0.0,
                    "ac_voltage": 230.1 if running else 0.0,
                    "temperature_c": 31.2,
                    "state": "running" if running else "standby",
                    "state_code": 2 if running else 5,
                    "generator_running": running,
                    "fault": False,
                    "total_runtime_seconds": 381223,
                    "last_run_seconds": 1450,
                    "cloud_connected": True,
                },
            )
            return
        self._send(404, {"error": "not_found"})

    def do_POST(self) -> None:  # noqa: N802
        payload = self._read_json()
        if self.path == "/api/v1/pair":
            if payload.get("pairing_code") != PAIRING_CODE:
                self._send(401, {"error": "invalid_pairing_code"})
                return
            self._send(
                200,
                {
                    "device_id": DEVICE_ID,
                    "name": "AutoGen X Pro 334455",
                    "model": "AutoGen X Pro",
                    "firmware_version": "3.4.0-ha.simulator",
                    "api_version": "1",
                    "access_token": ACCESS_TOKEN,
                    "capabilities": ["status", "start_stop"],
                    "scopes": ["status", "control"],
                },
            )
            return
        if self.path != "/api/v1/command":
            self._send(404, {"error": "not_found"})
            return
        if not self._require_authentication():
            return
        if payload.get("device_id") != DEVICE_ID:
            self._send(409, {"error": "device_id_mismatch"})
            return
        command = payload.get("command")
        if command not in {"start", "stop"}:
            self._send(400, {"error": "unsupported_command"})
            return
        ControllerState.generator_running = command == "start"
        self._send(
            202,
            {
                "device_id": DEVICE_ID,
                "command": command,
                "accepted": True,
                "state": "starting" if command == "start" else "stopped",
                "state_code": 1 if command == "start" else 0,
                "generator_running": ControllerState.generator_running,
            },
        )

    def log_message(self, format: str, *args: Any) -> None:
        """Keep automated test output concise."""


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=32100)
    args = parser.parse_args()
    print(f"AutoGen X Pro simulator listening on {args.host}:{args.port}", flush=True)
    ThreadingHTTPServer((args.host, args.port), Handler).serve_forever()


if __name__ == "__main__":
    main()

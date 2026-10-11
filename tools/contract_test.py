#!/usr/bin/env python3
"""Exercise the local API safety contract against the simulator only."""

from __future__ import annotations

import json
import threading
from http.server import ThreadingHTTPServer
from urllib.error import HTTPError

from mock_controller import (
    ACCESS_TOKEN,
    DEVICE_ID,
    PAIRING_CODE,
    ControllerState,
    Handler,
)
from validate_controller import request_json


def expect_http_error(
    expected_status: int,
    base_url: str,
    path: str,
    *,
    token: str | None = None,
    payload: dict | None = None,
) -> dict:
    """Return a rejected JSON response and verify its status code."""
    try:
        request_json(base_url, path, token=token, payload=payload)
    except RuntimeError as err:
        message = str(err)
        marker = f"HTTP {expected_status}: "
        if marker not in message:
            raise AssertionError(
                f"Expected HTTP {expected_status} from {path}, received: {message}"
            ) from err
        return json.loads(message.split(marker, 1)[1])
    raise AssertionError(f"Expected HTTP {expected_status} from {path}")


def main() -> None:
    """Run positive and negative protocol checks without real hardware."""
    ControllerState.generator_running = False
    ControllerState.fault = True
    ControllerState.sequence = 0
    ControllerState.pairing_available = True
    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    base_url = f"http://127.0.0.1:{server.server_port}"

    try:
        invalid_auth = expect_http_error(
            401, base_url, "/api/v1/status", token="invalid"
        )
        assert invalid_auth["error"] == "invalid_token"

        invalid_pairing = expect_http_error(
            401,
            base_url,
            "/api/v1/pair",
            payload={"pairing_code": "000000"},
        )
        assert invalid_pairing["error"] == "invalid_pairing_code"

        paired = request_json(
            base_url,
            "/api/v1/pair",
            payload={"pairing_code": PAIRING_CODE},
        )
        assert paired["device_id"] == DEVICE_ID
        assert paired["access_token"] == ACCESS_TOKEN

        reused_pairing = expect_http_error(
            403,
            base_url,
            "/api/v1/pair",
            payload={"pairing_code": PAIRING_CODE},
        )
        assert reused_pairing["error"] == "pairing_disabled"

        info = request_json(base_url, "/api/v1/info", token=ACCESS_TOKEN)
        status = request_json(base_url, "/api/v1/status", token=ACCESS_TOKEN)
        assert info["device_id"] == DEVICE_ID
        assert status["device_id"] == DEVICE_ID
        assert status["generator_running"] is False
        assert status["fault"] is True

        mismatch = expect_http_error(
            409,
            base_url,
            "/api/v1/command",
            token=ACCESS_TOKEN,
            payload={"device_id": "wrong-device", "command": "start"},
        )
        assert mismatch["error"] == "device_id_mismatch"
        assert ControllerState.generator_running is False

        unsupported = expect_http_error(
            400,
            base_url,
            "/api/v1/command",
            token=ACCESS_TOKEN,
            payload={"device_id": DEVICE_ID, "command": "unsupported"},
        )
        assert unsupported["error"] == "unsupported_command"
        assert ControllerState.generator_running is False

        reset = request_json(
            base_url,
            "/api/v1/command",
            token=ACCESS_TOKEN,
            payload={"device_id": DEVICE_ID, "command": "reset_fault"},
        )
        assert reset["accepted"] is True
        assert ControllerState.fault is False

        repeated_reset = expect_http_error(
            409,
            base_url,
            "/api/v1/command",
            token=ACCESS_TOKEN,
            payload={"device_id": DEVICE_ID, "command": "reset_fault"},
        )
        assert repeated_reset["reason"] == "no_active_fault"
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)

    print("PASS: simulator authentication, identity, reset, and rejection contract")
    print("No start or stop command was accepted.")


if __name__ == "__main__":
    try:
        main()
    except HTTPError as err:
        raise SystemExit(f"Unexpected HTTP error: {err}") from err

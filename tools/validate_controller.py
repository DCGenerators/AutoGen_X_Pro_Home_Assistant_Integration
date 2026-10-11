#!/usr/bin/env python3
"""Validate AutoGen identity and read-only API behavior without Home Assistant."""

from __future__ import annotations

import argparse
import json
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


def request_json(
    base_url: str,
    path: str,
    *,
    token: str | None = None,
    payload: dict[str, Any] | None = None,
    method: str | None = None,
) -> dict[str, Any]:
    body = json.dumps(payload).encode() if payload is not None else None
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    request = Request(
        f"{base_url}{path}",
        data=body,
        headers=headers,
        method=method or ("POST" if body is not None else "GET"),
    )
    try:
        with urlopen(request, timeout=10) as response:  # noqa: S310
            result = json.load(response)
    except HTTPError as error:
        detail = error.read().decode(errors="replace")
        raise RuntimeError(f"{path} returned HTTP {error.code}: {detail}") from error
    except URLError as error:
        raise RuntimeError(f"Unable to reach {base_url}: {error.reason}") from error
    if not isinstance(result, dict):
        raise RuntimeError(f"{path} returned non-object JSON")
    return result


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run identity and read-only checks against an AutoGen controller"
    )
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=32100)
    credentials = parser.add_mutually_exclusive_group(required=True)
    credentials.add_argument("--token")
    credentials.add_argument("--pairing-code")
    parser.add_argument("--device-id", help="Expected permanent AutoGen device ID")
    args = parser.parse_args()

    base_url = f"http://{args.host}:{args.port}"
    token = args.token
    paired_device_id: str | None = None
    if args.pairing_code:
        paired = request_json(
            base_url,
            "/api/v1/pair",
            payload={
                "pairing_code": args.pairing_code,
                "client_name": "AutoGen validation tool",
            },
        )
        token = str(paired.get("access_token", ""))
        paired_device_id = str(paired.get("device_id", ""))
        if not token:
            raise RuntimeError("Pairing response omitted access_token")

    info = request_json(base_url, "/api/v1/info", token=token)
    status = request_json(base_url, "/api/v1/status", token=token)
    info_device_id = str(info.get("device_id", ""))
    status_device_id = str(status.get("device_id", ""))
    expected = args.device_id or paired_device_id or info_device_id

    if not expected:
        raise RuntimeError("Controller did not return a permanent device_id")
    if info_device_id != expected or status_device_id != expected:
        raise RuntimeError(
            "Identity mismatch: "
            f"expected={expected}, info={info_device_id}, status={status_device_id}"
        )
    required_status = {
        "state",
        "generator_running",
        "fault",
        "battery_voltage",
        "cloud_connected",
    }
    missing = sorted(required_status - status.keys())
    if missing:
        raise RuntimeError(f"Status response is missing: {', '.join(missing)}")

    print("PASS: authenticated info and status API")
    print(f"Device ID: {expected}")
    print(f"Firmware: {info.get('firmware_version', 'unknown')}")
    print(f"State: {status.get('state', 'unknown')}")
    print("No control command was sent.")


if __name__ == "__main__":
    main()

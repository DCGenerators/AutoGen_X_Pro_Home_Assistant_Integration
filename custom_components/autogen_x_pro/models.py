"""Data models for AutoGen X Pro."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class AutoGenDeviceInfo:
    """Identity and capability data returned by the controller."""

    device_id: str
    name: str
    model: str
    firmware_version: str
    api_version: str
    capabilities: tuple[str, ...]

    @classmethod
    def from_payload(cls, payload: dict[str, Any]) -> AutoGenDeviceInfo:
        """Validate and construct device information from an API payload."""
        device_id = str(payload.get("device_id", "")).strip()
        if not device_id:
            raise ValueError("Controller response did not contain a device_id")

        return cls(
            device_id=device_id,
            name=str(payload.get("name") or f"AutoGen X Pro {device_id[-6:]}"),
            model=str(payload.get("model") or "AutoGen X Pro"),
            firmware_version=str(payload.get("firmware_version") or "unknown"),
            api_version=str(payload.get("api_version") or "1"),
            capabilities=tuple(str(item) for item in payload.get("capabilities", [])),
        )

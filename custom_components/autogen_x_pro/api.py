"""Async client for the AutoGen X Pro local API."""

from __future__ import annotations

import asyncio
from typing import Any

from aiohttp import ClientError, ClientResponseError, ClientSession

from .const import API_COMMAND_PATH, API_INFO_PATH, API_PAIR_PATH, API_STATUS_PATH
from .models import AutoGenDeviceInfo


class AutoGenApiError(Exception):
    """Base error raised by the AutoGen local API client."""


class AutoGenAuthenticationError(AutoGenApiError):
    """Raised when the controller rejects the pairing token."""


class AutoGenConnectionError(AutoGenApiError):
    """Raised when the controller cannot be reached."""


class AutoGenIdentityError(AutoGenApiError):
    """Raised when a response belongs to a different AutoGen device ID."""


class AutoGenCommandError(AutoGenApiError):
    """Raised when a controller safely rejects a control command."""

    def __init__(self, command: str, reason: str) -> None:
        super().__init__(f"Controller rejected {command}: {reason}")
        self.command = command
        self.reason = reason


class AutoGenApiClient:
    """Small client for the versioned, authenticated controller API."""

    def __init__(
        self,
        session: ClientSession,
        host: str,
        port: int,
        token: str | None,
        expected_device_id: str | None = None,
    ) -> None:
        self._session = session
        self._base_url = f"http://{host}:{port}"
        self._token = token
        self._expected_device_id = expected_device_id

    async def async_pair(self, pairing_code: str) -> tuple[AutoGenDeviceInfo, str]:
        """Exchange a short-lived pairing code for a revocable API token."""
        payload = await self._async_request_json(
            "POST",
            API_PAIR_PATH,
            json={"pairing_code": pairing_code, "client_name": "Home Assistant"},
            authenticated=False,
        )
        token = str(payload.get("access_token", "")).strip()
        if not token:
            raise AutoGenApiError("Pairing response did not contain an access_token")
        try:
            info = AutoGenDeviceInfo.from_payload(payload)
        except (TypeError, ValueError) as err:
            raise AutoGenApiError(str(err)) from err
        self._validate_device_id(info.device_id)
        return info, token

    async def async_get_info(self) -> AutoGenDeviceInfo:
        """Return controller identity and API capabilities."""
        payload = await self._async_request_json("GET", API_INFO_PATH)
        try:
            info = AutoGenDeviceInfo.from_payload(payload)
        except (TypeError, ValueError) as err:
            raise AutoGenApiError(str(err)) from err
        self._validate_device_id(info.device_id)
        return info

    async def async_get_status(self) -> dict[str, Any]:
        """Return the latest read-only controller snapshot."""
        payload = await self._async_request_json("GET", API_STATUS_PATH)
        self._validate_device_id(str(payload.get("device_id", "")))
        return payload

    async def async_command(self, command: str) -> dict[str, Any]:
        """Send an authenticated command to the identified controller."""
        if command not in {"start", "stop", "reset_fault"}:
            raise AutoGenApiError(f"Unsupported command: {command}")
        if not self._expected_device_id:
            raise AutoGenIdentityError("No expected AutoGen device ID is configured")
        payload = await self._async_request_json(
            "POST",
            API_COMMAND_PATH,
            json={"device_id": self._expected_device_id, "command": command},
        )
        self._validate_device_id(str(payload.get("device_id", "")))
        if not payload.get("accepted", False):
            reason = str(payload.get("reason") or "command_rejected")
            raise AutoGenCommandError(command, reason)
        return payload

    def _validate_device_id(self, actual_device_id: str) -> None:
        """Prevent discovery, address changes, or responses crossing devices."""
        if not actual_device_id:
            raise AutoGenIdentityError("Controller response omitted device_id")
        if self._expected_device_id and actual_device_id != self._expected_device_id:
            raise AutoGenIdentityError(
                "Controller device_id does not match the configured AutoGen device"
            )

    async def _async_request_json(
        self,
        method: str,
        path: str,
        *,
        json: dict[str, Any] | None = None,
        authenticated: bool = True,
    ) -> dict[str, Any]:
        headers: dict[str, str] = {}
        if authenticated:
            if not self._token:
                raise AutoGenAuthenticationError("No controller token is configured")
            headers["Authorization"] = f"Bearer {self._token}"
        try:
            async with asyncio.timeout(10):
                response = await self._session.request(
                    method,
                    f"{self._base_url}{path}",
                    headers=headers,
                    json=json,
                )
                if response.status in (401, 403):
                    raise AutoGenAuthenticationError("Controller rejected credentials")
                payload = await response.json(content_type=None)
                if response.status >= 400:
                    error = (
                        str(
                            payload.get("error") or payload.get("reason") or "api_error"
                        )
                        if isinstance(payload, dict)
                        else "api_error"
                    )
                    if path == API_COMMAND_PATH:
                        command = str((json or {}).get("command") or "command")
                        raise AutoGenCommandError(command, error)
                    raise AutoGenApiError(
                        f"Controller returned HTTP {response.status}: {error}"
                    )
        except AutoGenAuthenticationError:
            raise
        except AutoGenApiError:
            raise
        except (TimeoutError, ClientResponseError, ClientError) as err:
            raise AutoGenConnectionError(str(err)) from err

        if not isinstance(payload, dict):
            raise AutoGenApiError("Controller returned a non-object JSON response")
        return payload

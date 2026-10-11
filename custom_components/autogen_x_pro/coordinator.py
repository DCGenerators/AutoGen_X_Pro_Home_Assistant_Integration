"""Data update coordinator for AutoGen X Pro."""

from __future__ import annotations

import logging
from datetime import timedelta
from time import monotonic
from typing import Any

from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import AutoGenApiClient, AutoGenApiError, AutoGenAuthenticationError
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


class AutoGenCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Fetch one authoritative controller snapshot for all entities."""

    def __init__(self, hass, client: AutoGenApiClient) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            # Generator state transitions are operational feedback, not slow
            # telemetry. Poll the local controller often enough for Home
            # Assistant to show starting, retry, and pause states instead of
            # skipping them between snapshots.
            update_interval=timedelta(seconds=2),
        )
        self.client = client
        self.settings_supported = False
        self._settings: dict[str, Any] = {}
        self._settings_refresh_at = 0.0

    async def _async_setup(self) -> None:
        """Discover optional capabilities once per config-entry load."""
        try:
            device = await self.client.async_get_info()
            self.settings_supported = "settings" in device.capabilities
        except AutoGenAuthenticationError as err:
            raise ConfigEntryAuthFailed("Controller credentials were rejected") from err
        except AutoGenApiError as err:
            raise UpdateFailed(str(err)) from err

    async def _async_update_data(self) -> dict[str, Any]:
        try:
            data = await self.client.async_get_status()
            now = monotonic()
            if self.settings_supported and now >= self._settings_refresh_at:
                self._settings = await self.client.async_get_settings()
                self._settings_refresh_at = now + 10
            data.update(self._settings)
            return data
        except AutoGenAuthenticationError as err:
            raise ConfigEntryAuthFailed("Controller credentials were rejected") from err
        except AutoGenApiError as err:
            raise UpdateFailed(str(err)) from err

    async def async_update_settings(self, changes: dict[str, Any]) -> None:
        """Write settings and publish the confirmed controller values."""
        confirmed = await self.client.async_update_settings(changes)
        self._settings = confirmed
        self._settings_refresh_at = monotonic() + 10
        data = dict(self.data)
        data.update(confirmed)
        self.async_set_updated_data(data)

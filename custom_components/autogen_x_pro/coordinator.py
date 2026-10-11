"""Data update coordinator for AutoGen X Pro."""

from __future__ import annotations

import logging
from datetime import timedelta
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

    async def _async_update_data(self) -> dict[str, Any]:
        try:
            return await self.client.async_get_status()
        except AutoGenAuthenticationError as err:
            raise ConfigEntryAuthFailed("Controller credentials were rejected") from err
        except AutoGenApiError as err:
            raise UpdateFailed(str(err)) from err

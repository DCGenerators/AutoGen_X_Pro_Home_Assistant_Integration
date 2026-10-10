"""Redacted diagnostics for AutoGen X Pro."""

from __future__ import annotations

from typing import Any

from homeassistant.components.diagnostics import async_redact_data
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import CONF_TOKEN, DOMAIN


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: ConfigEntry
) -> dict[str, Any]:
    """Return configuration and snapshot data with credentials removed."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    return {
        "entry": async_redact_data(entry.as_dict(), {CONF_TOKEN}),
        "snapshot": coordinator.data,
    }

"""Weekly schedule start time for AutoGen X Pro."""

from __future__ import annotations

from datetime import time

from homeassistant.components.time import TimeEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .const import DOMAIN
from .coordinator import AutoGenCoordinator
from .entity import AutoGenEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Create the schedule time for firmware that supports settings."""
    coordinator: AutoGenCoordinator = hass.data[DOMAIN][entry.entry_id]
    if not coordinator.settings_supported:
        return
    device = await coordinator.client.async_get_info()
    async_add_entities([AutoGenScheduleStartTime(coordinator, device)])


class AutoGenScheduleStartTime(AutoGenEntity, TimeEntity):
    """Controller-local weekly schedule start time."""

    _attr_translation_key = "schedule_start_time"
    _attr_entity_category = EntityCategory.CONFIG

    def __init__(self, coordinator, device) -> None:
        super().__init__(coordinator, device, "schedule_start_time")

    @property
    def native_value(self) -> time | None:
        """Return the confirmed schedule time."""
        hour = self.coordinator.data.get("schedule_start_hour")
        minute = self.coordinator.data.get("schedule_start_minute")
        if hour is None or minute is None:
            return None
        return time(hour=int(hour), minute=int(minute))

    async def async_set_value(self, value: time) -> None:
        """Persist both components as one settings update."""
        await self.coordinator.async_update_settings(
            {
                "schedule_start_hour": value.hour,
                "schedule_start_minute": value.minute,
            }
        )

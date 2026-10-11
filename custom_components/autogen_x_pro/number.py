"""Editable customer settings for AutoGen X Pro."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from homeassistant.components.number import (
    NumberEntity,
    NumberEntityDescription,
    NumberMode,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    EntityCategory,
    UnitOfElectricPotential,
    UnitOfTemperature,
    UnitOfTime,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .const import DOMAIN
from .coordinator import AutoGenCoordinator
from .entity import AutoGenEntity


@dataclass(frozen=True, kw_only=True)
class AutoGenNumberDescription(NumberEntityDescription):
    """Describe an editable numeric controller setting."""

    value_key: str
    minimum: float
    maximum: float
    step: float
    integer: bool = False


NUMBERS = (
    AutoGenNumberDescription(
        key="battery_low_voltage",
        translation_key="battery_low_voltage",
        value_key="battery_low_voltage",
        minimum=0,
        maximum=100,
        step=0.1,
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
    ),
    AutoGenNumberDescription(
        key="battery_high_voltage",
        translation_key="battery_high_voltage",
        value_key="battery_high_voltage",
        minimum=0,
        maximum=100,
        step=0.1,
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
    ),
    AutoGenNumberDescription(
        key="temperature_low_c",
        translation_key="temperature_low_c",
        value_key="temperature_low_c",
        minimum=-55,
        maximum=50,
        step=0.5,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
    ),
    AutoGenNumberDescription(
        key="temperature_high_c",
        translation_key="temperature_high_c",
        value_key="temperature_high_c",
        minimum=-55,
        maximum=125,
        step=0.5,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
    ),
    AutoGenNumberDescription(
        key="schedule_duration_minutes",
        translation_key="schedule_duration_minutes",
        value_key="schedule_duration_minutes",
        minimum=1,
        maximum=1440,
        step=1,
        integer=True,
        native_unit_of_measurement=UnitOfTime.MINUTES,
    ),
    AutoGenNumberDescription(
        key="schedule_utc_offset_hours",
        translation_key="schedule_utc_offset_hours",
        value_key="schedule_utc_offset_hours",
        minimum=-12,
        maximum=14,
        step=1,
        integer=True,
        native_unit_of_measurement=UnitOfTime.HOURS,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Create settings numbers only for firmware that supports them."""
    coordinator: AutoGenCoordinator = hass.data[DOMAIN][entry.entry_id]
    if not coordinator.settings_supported:
        return
    device = await coordinator.client.async_get_info()
    async_add_entities(
        AutoGenSettingsNumber(coordinator, device, description)
        for description in NUMBERS
    )


class AutoGenSettingsNumber(AutoGenEntity, NumberEntity):
    """Number backed by a validated, persistent controller setting."""

    entity_description: AutoGenNumberDescription
    _attr_entity_category = EntityCategory.CONFIG
    _attr_mode = NumberMode.BOX

    def __init__(self, coordinator, device, description) -> None:
        super().__init__(coordinator, device, description.key)
        self.entity_description = description
        self._attr_native_min_value = description.minimum
        self._attr_native_max_value = description.maximum
        self._attr_native_step = description.step

    @property
    def native_value(self) -> Any:
        """Return the controller-confirmed setting."""
        return self.coordinator.data.get(self.entity_description.value_key)

    async def async_set_native_value(self, value: float) -> None:
        """Validate and persist the value through the controller API."""
        api_value: float | int = (
            int(value) if self.entity_description.integer else value
        )
        await self.coordinator.async_update_settings(
            {self.entity_description.value_key: api_value}
        )

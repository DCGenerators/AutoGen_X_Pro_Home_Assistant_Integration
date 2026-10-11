"""Read-only sensor entities for AutoGen X Pro."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    UnitOfElectricCurrent,
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
class AutoGenSensorDescription(SensorEntityDescription):
    """Describe an AutoGen status field."""

    value_key: str


SENSORS = (
    AutoGenSensorDescription(
        key="battery_voltage",
        translation_key="battery_voltage",
        value_key="battery_voltage",
        device_class=SensorDeviceClass.VOLTAGE,
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=2,
    ),
    AutoGenSensorDescription(
        key="charge_current",
        translation_key="charge_current",
        value_key="charge_current",
        device_class=SensorDeviceClass.CURRENT,
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=2,
    ),
    AutoGenSensorDescription(
        key="ac_voltage",
        translation_key="ac_voltage",
        value_key="ac_voltage",
        device_class=SensorDeviceClass.VOLTAGE,
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=1,
    ),
    AutoGenSensorDescription(
        key="temperature",
        translation_key="temperature",
        value_key="temperature_c",
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=1,
    ),
    AutoGenSensorDescription(
        key="controller_state",
        translation_key="controller_state",
        value_key="state",
    ),
    AutoGenSensorDescription(
        key="total_runtime",
        translation_key="total_runtime",
        value_key="total_runtime_seconds",
        device_class=SensorDeviceClass.DURATION,
        native_unit_of_measurement=UnitOfTime.SECONDS,
        state_class=SensorStateClass.TOTAL_INCREASING,
    ),
    AutoGenSensorDescription(
        key="last_run_duration",
        translation_key="last_run_duration",
        value_key="last_run_seconds",
        device_class=SensorDeviceClass.DURATION,
        native_unit_of_measurement=UnitOfTime.SECONDS,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Create all read-only sensor entities."""
    coordinator: AutoGenCoordinator = hass.data[DOMAIN][entry.entry_id]
    device = await coordinator.client.async_get_info()
    async_add_entities(
        AutoGenSensor(coordinator, device, description) for description in SENSORS
    )


class AutoGenSensor(AutoGenEntity, SensorEntity):
    """Sensor backed by one field in the coordinated snapshot."""

    entity_description: AutoGenSensorDescription

    def __init__(self, coordinator, device, description) -> None:
        super().__init__(coordinator, device, description.key)
        self.entity_description = description

    @property
    def native_value(self) -> Any:
        """Return the latest native value."""
        return self.coordinator.data.get(self.entity_description.value_key)

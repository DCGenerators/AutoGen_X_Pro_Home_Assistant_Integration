"""Read-only binary sensors for AutoGen X Pro."""

from __future__ import annotations

from dataclasses import dataclass

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
    BinarySensorEntityDescription,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .const import DOMAIN
from .coordinator import AutoGenCoordinator
from .entity import AutoGenEntity


@dataclass(frozen=True, kw_only=True)
class AutoGenBinarySensorDescription(BinarySensorEntityDescription):
    """Describe a boolean field from the controller snapshot."""

    value_key: str


BINARY_SENSORS = (
    AutoGenBinarySensorDescription(
        key="generator_running",
        translation_key="generator_running",
        value_key="generator_running",
        device_class=BinarySensorDeviceClass.RUNNING,
    ),
    AutoGenBinarySensorDescription(
        key="fault",
        translation_key="fault",
        value_key="fault",
        device_class=BinarySensorDeviceClass.PROBLEM,
    ),
    AutoGenBinarySensorDescription(
        key="cloud_connected",
        translation_key="cloud_connected",
        value_key="cloud_connected",
        device_class=BinarySensorDeviceClass.CONNECTIVITY,
    ),
)

LORAGEN_BINARY_SENSORS = (
    AutoGenBinarySensorDescription(
        key="loragen_connected",
        translation_key="loragen_connected",
        value_key="loragen_connected",
        device_class=BinarySensorDeviceClass.CONNECTIVITY,
    ),
    AutoGenBinarySensorDescription(
        key="loragen_ac_input",
        translation_key="loragen_ac_input",
        value_key="loragen_ac_input",
        device_class=BinarySensorDeviceClass.POWER,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Create all read-only binary sensor entities."""
    coordinator: AutoGenCoordinator = hass.data[DOMAIN][entry.entry_id]
    device = await coordinator.client.async_get_info()
    descriptions = list(BINARY_SENSORS)
    if "loragen" in device.capabilities:
        descriptions.extend(LORAGEN_BINARY_SENSORS)
    async_add_entities(
        AutoGenBinarySensor(coordinator, device, description)
        for description in descriptions
    )


class AutoGenBinarySensor(AutoGenEntity, BinarySensorEntity):
    """Binary sensor backed by one field in the coordinated snapshot."""

    entity_description: AutoGenBinarySensorDescription

    def __init__(self, coordinator, device, description) -> None:
        super().__init__(coordinator, device, description.key)
        self.entity_description = description

    @property
    def is_on(self) -> bool | None:
        """Return the latest boolean state."""
        value = self.coordinator.data.get(self.entity_description.value_key)
        return bool(value) if value is not None else None

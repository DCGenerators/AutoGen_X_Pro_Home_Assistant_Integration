"""Base entity for AutoGen X Pro."""

from __future__ import annotations

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import AutoGenCoordinator
from .models import AutoGenDeviceInfo


class AutoGenEntity(CoordinatorEntity[AutoGenCoordinator]):
    """Base class shared by AutoGen X Pro entities."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: AutoGenCoordinator,
        device: AutoGenDeviceInfo,
        key: str,
    ) -> None:
        super().__init__(coordinator)
        self._key = key
        self._attr_unique_id = f"{device.device_id}_{key}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, device.device_id)},
            name=device.name,
            manufacturer="DC AutoGen",
            model=device.model,
            serial_number=device.device_id,
            sw_version=device.firmware_version,
        )

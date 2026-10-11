"""Fault reset control for AutoGen X Pro."""

from __future__ import annotations

from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
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
    """Create the fault-reset button when the firmware advertises support."""
    coordinator: AutoGenCoordinator = hass.data[DOMAIN][entry.entry_id]
    device = await coordinator.client.async_get_info()
    if "reset_fault" in device.capabilities:
        async_add_entities([AutoGenResetFaultButton(coordinator, device)])


class AutoGenResetFaultButton(AutoGenEntity, ButtonEntity):
    """Clear an active controller error through its existing state machine."""

    _attr_translation_key = "reset_fault"

    def __init__(self, coordinator, device) -> None:
        super().__init__(coordinator, device, "reset_fault")

    @property
    def available(self) -> bool:
        """Allow reset only while the controller confirms an active fault."""
        return super().available and self.coordinator.data.get("fault") is True

    async def async_press(self) -> None:
        """Request a fault reset using the authenticated controller command path."""
        await self.coordinator.client.async_command("reset_fault")
        await self.coordinator.async_request_refresh()

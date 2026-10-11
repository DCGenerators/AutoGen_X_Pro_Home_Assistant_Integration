"""Authenticated generator control for AutoGen X Pro."""

from __future__ import annotations

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .const import DOMAIN
from .coordinator import AutoGenCoordinator
from .entity import AutoGenEntity

_CONTROL_ON_STATES = frozenset({1, 2, 6, 7, 10, 11, 12, 13, 14, 15})
_CONTROL_OFF_STATES = frozenset({0, 3, 4, 5, 9, 16, 17, 18})


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Create the generator control when the firmware advertises support."""
    coordinator: AutoGenCoordinator = hass.data[DOMAIN][entry.entry_id]
    device = await coordinator.client.async_get_info()
    if "start_stop" in device.capabilities:
        async_add_entities([AutoGenGeneratorSwitch(coordinator, device)])


class AutoGenGeneratorSwitch(AutoGenEntity, SwitchEntity):
    """Start or stop the generator through the controller state machine."""

    _attr_translation_key = "generator_control"

    def __init__(self, coordinator, device) -> None:
        super().__init__(coordinator, device, "generator_control")

    @property
    def is_on(self) -> bool | None:
        """Reflect whether the controller is executing an operating sequence."""
        state_code = self.coordinator.data.get("state_code")
        if state_code in _CONTROL_ON_STATES:
            return True
        if state_code in _CONTROL_OFF_STATES:
            return False

        # Retain sensible behavior with older or future firmware that does not
        # provide a recognized state code. The separate Generator running
        # binary sensor remains the authoritative physical run indication.
        value = self.coordinator.data.get("generator_running")
        return bool(value) if value is not None else None

    async def async_turn_on(self, **kwargs) -> None:
        """Request a start using the controller's existing safety checks."""
        await self.coordinator.client.async_command("start")
        await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs) -> None:
        """Request a stop using the controller's existing command path."""
        await self.coordinator.client.async_command("stop")
        await self.coordinator.async_request_refresh()

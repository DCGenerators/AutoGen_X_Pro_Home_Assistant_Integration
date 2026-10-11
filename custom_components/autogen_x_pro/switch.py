"""Authenticated generator control for AutoGen X Pro."""

from __future__ import annotations

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory
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
    entities: list[SwitchEntity] = []
    if "start_stop" in device.capabilities:
        entities.append(AutoGenGeneratorSwitch(coordinator, device))
    if "settings" in device.capabilities:
        entities.append(
            AutoGenScheduleSwitch(
                coordinator,
                device,
                key="schedule_enabled",
                translation_key="schedule_enabled",
            )
        )
        entities.extend(
            AutoGenScheduleSwitch(
                coordinator,
                device,
                key=f"schedule_{name}",
                translation_key=f"schedule_{name}",
                mask=mask,
            )
            for name, mask in (
                ("monday", 1 << 0),
                ("tuesday", 1 << 1),
                ("wednesday", 1 << 2),
                ("thursday", 1 << 3),
                ("friday", 1 << 4),
                ("saturday", 1 << 5),
                ("sunday", 1 << 6),
            )
        )
    if "loragen" in device.capabilities:
        entities.extend(
            AutoGenLoRaGenRelaySwitch(coordinator, device, relay)
            for relay in (1, 2)
        )
    async_add_entities(entities)


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


class AutoGenScheduleSwitch(AutoGenEntity, SwitchEntity):
    """Persistent weekly schedule enable or weekday setting."""

    _attr_entity_category = EntityCategory.CONFIG

    def __init__(
        self,
        coordinator,
        device,
        *,
        key: str,
        translation_key: str,
        mask: int | None = None,
    ) -> None:
        super().__init__(coordinator, device, key)
        self._attr_translation_key = translation_key
        self._mask = mask

    @property
    def is_on(self) -> bool | None:
        """Return the confirmed controller setting."""
        if self._mask is None:
            value = self.coordinator.data.get("schedule_enabled")
            return bool(value) if value is not None else None
        week_mask = self.coordinator.data.get("schedule_week_mask")
        if week_mask is None:
            return None
        return bool(int(week_mask) & self._mask)

    async def _async_set_state(self, enabled: bool) -> None:
        if self._mask is None:
            await self.coordinator.async_update_settings(
                {"schedule_enabled": enabled}
            )
            return
        week_mask = int(self.coordinator.data.get("schedule_week_mask", 0))
        updated_mask = week_mask | self._mask if enabled else week_mask & ~self._mask
        await self.coordinator.async_update_settings(
            {"schedule_week_mask": updated_mask}
        )

    async def async_turn_on(self, **kwargs) -> None:
        """Enable the schedule or weekday."""
        await self._async_set_state(True)

    async def async_turn_off(self, **kwargs) -> None:
        """Disable the schedule or weekday."""
        await self._async_set_state(False)


class AutoGenLoRaGenRelaySwitch(AutoGenEntity, SwitchEntity):
    """Optimistic relay control for the legacy LoRaGen UART protocol."""

    _attr_assumed_state = True

    def __init__(self, coordinator, device, relay: int) -> None:
        super().__init__(coordinator, device, f"loragen_relay_{relay}")
        self._relay = relay
        self._attr_translation_key = f"loragen_relay_{relay}"

    @property
    def available(self) -> bool:
        """Make relay control unavailable when node telemetry is stale."""
        return super().available and bool(
            self.coordinator.data.get("loragen_connected")
        )

    @property
    def is_on(self) -> bool | None:
        """Return the last command because the legacy node has no relay ACK."""
        known = self.coordinator.data.get(f"loragen_relay_{self._relay}_known")
        if not known:
            return None
        return bool(self.coordinator.data.get(f"loragen_relay_{self._relay}"))

    async def _async_set_state(self, enabled: bool) -> None:
        action = "on" if enabled else "off"
        await self.coordinator.client.async_command(
            f"loragen_relay_{self._relay}_{action}"
        )
        await self.coordinator.async_request_refresh()

    async def async_turn_on(self, **kwargs) -> None:
        """Request relay activation over the existing LoRa protocol."""
        await self._async_set_state(True)

    async def async_turn_off(self, **kwargs) -> None:
        """Request relay deactivation over the existing LoRa protocol."""
        await self._async_set_state(False)

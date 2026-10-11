"""UI and Zeroconf setup flow for AutoGen X Pro."""

from __future__ import annotations

from typing import Any

import probatio
from homeassistant.config_entries import ConfigEntry, ConfigFlow, ConfigFlowResult
from homeassistant.const import CONF_HOST, CONF_PORT
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.service_info.zeroconf import ZeroconfServiceInfo

from .api import (
    AutoGenApiClient,
    AutoGenApiError,
    AutoGenAuthenticationError,
    AutoGenConnectionError,
)
from .const import CONF_DEVICE_ID, CONF_PAIRING_CODE, CONF_TOKEN, DEFAULT_PORT, DOMAIN


class AutoGenConfigFlow(ConfigFlow, domain=DOMAIN):
    """Configure an AutoGen X Pro controller through the UI."""

    VERSION = 1

    def __init__(self) -> None:
        self._discovered_host: str | None = None
        self._discovered_port = DEFAULT_PORT
        self._discovered_device_id: str | None = None
        self._discovered_name = "AutoGen X Pro"

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle manual local setup."""
        errors: dict[str, str] = {}
        if user_input is not None:
            try:
                info, data = await self._async_pair(user_input)
            except AutoGenAuthenticationError:
                errors["base"] = "invalid_auth"
            except AutoGenConnectionError:
                errors["base"] = "cannot_connect"
            except AutoGenApiError:
                errors["base"] = "unknown"
            else:
                await self.async_set_unique_id(info.device_id)
                self._abort_if_unique_id_configured()
                return self.async_create_entry(title=info.name, data=data)

        return self.async_show_form(
            step_id="user",
            data_schema=probatio.Schema(
                {
                    probatio.Required(CONF_HOST): str,
                    probatio.Optional(CONF_PORT, default=DEFAULT_PORT): int,
                    probatio.Required(CONF_PAIRING_CODE): str,
                }
            ),
            errors=errors,
        )

    async def async_step_zeroconf(
        self, discovery_info: ZeroconfServiceInfo
    ) -> ConfigFlowResult:
        """Handle a controller discovered on the local network."""
        self._discovered_host = discovery_info.host
        self._discovered_port = discovery_info.port or DEFAULT_PORT
        properties = discovery_info.properties
        self._discovered_device_id = properties.get("device_id")
        self._discovered_name = properties.get("name", "AutoGen X Pro")

        if self._discovered_device_id:
            await self.async_set_unique_id(self._discovered_device_id)
            self._abort_if_unique_id_configured(
                updates={
                    CONF_HOST: self._discovered_host,
                    CONF_PORT: self._discovered_port,
                }
            )

        self.context["title_placeholders"] = {"name": self._discovered_name}
        return await self.async_step_zeroconf_confirm()

    async def async_step_zeroconf_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Confirm discovery and validate the short-lived pairing token."""
        if self._discovered_host is None:
            return self.async_abort(reason="cannot_connect")

        errors: dict[str, str] = {}
        if user_input is not None:
            data = {
                CONF_HOST: self._discovered_host,
                CONF_PORT: self._discovered_port,
                CONF_PAIRING_CODE: user_input[CONF_PAIRING_CODE],
            }
            try:
                info, entry_data = await self._async_pair(data)
            except AutoGenAuthenticationError:
                errors["base"] = "invalid_auth"
            except AutoGenConnectionError:
                errors["base"] = "cannot_connect"
            except AutoGenApiError:
                errors["base"] = "unknown"
            else:
                await self.async_set_unique_id(info.device_id)
                self._abort_if_unique_id_configured()
                return self.async_create_entry(title=info.name, data=entry_data)

        return self.async_show_form(
            step_id="zeroconf_confirm",
            data_schema=probatio.Schema({probatio.Required(CONF_PAIRING_CODE): str}),
            errors=errors,
            description_placeholders={"name": self._discovered_name},
        )

    async def async_step_reauth(
        self, entry_data: dict[str, Any]
    ) -> ConfigFlowResult:
        """Start local-token reauthentication for an existing controller."""
        entry = self._get_reauth_entry()
        self._load_discovered_values(entry)
        return await self.async_step_reauth_confirm()

    async def async_step_reauth_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Exchange a fresh local pairing code and reload the existing entry."""
        entry = self._get_reauth_entry()
        errors: dict[str, str] = {}
        if user_input is not None:
            try:
                info, entry_data = await self._async_pair(
                    {
                        CONF_HOST: self._discovered_host,
                        CONF_PORT: self._discovered_port,
                        CONF_PAIRING_CODE: user_input[CONF_PAIRING_CODE],
                    }
                )
            except AutoGenAuthenticationError:
                errors["base"] = "invalid_auth"
            except AutoGenConnectionError:
                errors["base"] = "cannot_connect"
            except AutoGenApiError:
                errors["base"] = "unknown"
            else:
                await self.async_set_unique_id(info.device_id)
                self._abort_if_unique_id_mismatch()
                return self.async_update_reload_and_abort(
                    entry,
                    data_updates=entry_data,
                )

        return self.async_show_form(
            step_id="reauth_confirm",
            data_schema=probatio.Schema({probatio.Required(CONF_PAIRING_CODE): str}),
            errors=errors,
            description_placeholders={"name": entry.title},
        )

    async def async_step_reconfigure(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Allow an existing local controller address to be changed manually."""
        entry = self._get_reconfigure_entry()
        errors: dict[str, str] = {}
        if user_input is not None:
            client = AutoGenApiClient(
                async_get_clientsession(self.hass),
                user_input[CONF_HOST],
                user_input[CONF_PORT],
                entry.data[CONF_TOKEN],
                entry.data[CONF_DEVICE_ID],
            )
            try:
                info = await client.async_get_info()
            except AutoGenAuthenticationError:
                errors["base"] = "invalid_auth"
            except AutoGenConnectionError:
                errors["base"] = "cannot_connect"
            except AutoGenApiError:
                errors["base"] = "unknown"
            else:
                await self.async_set_unique_id(info.device_id)
                self._abort_if_unique_id_mismatch()
                return self.async_update_reload_and_abort(
                    entry,
                    data_updates={
                        **entry.data,
                        CONF_HOST: user_input[CONF_HOST],
                        CONF_PORT: user_input[CONF_PORT],
                    },
                )

        return self.async_show_form(
            step_id="reconfigure",
            data_schema=probatio.Schema(
                {
                    probatio.Required(
                        CONF_HOST, default=entry.data[CONF_HOST]
                    ): str,
                    probatio.Optional(
                        CONF_PORT, default=entry.data[CONF_PORT]
                    ): int,
                }
            ),
            errors=errors,
        )

    def _load_discovered_values(self, entry: ConfigEntry) -> None:
        """Load the existing endpoint and identity for a recovery flow."""
        self._discovered_host = entry.data[CONF_HOST]
        self._discovered_port = entry.data[CONF_PORT]
        self._discovered_device_id = entry.data[CONF_DEVICE_ID]
        self._discovered_name = entry.title

    async def _async_pair(self, data: dict[str, Any]):
        client = AutoGenApiClient(
            async_get_clientsession(self.hass),
            data[CONF_HOST],
            data[CONF_PORT],
            None,
            self._discovered_device_id,
        )
        info, token = await client.async_pair(data[CONF_PAIRING_CODE])
        return info, {
            CONF_HOST: data[CONF_HOST],
            CONF_PORT: data[CONF_PORT],
            CONF_DEVICE_ID: info.device_id,
            CONF_TOKEN: token,
        }

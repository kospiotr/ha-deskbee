from __future__ import annotations

from typing import Any

import homeassistant.helpers.config_validation as cv
import voluptuous as vol
from homeassistant.config_entries import ConfigFlow
from homeassistant.const import CONF_ACCESS_TOKEN
from homeassistant.data_entry_flow import FlowResult

from .const import CONF_DOMAIN

AUTH_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_DOMAIN): cv.string,
        vol.Required(CONF_ACCESS_TOKEN): cv.string,
    }
)


class DeskbeeConfigFlow(ConfigFlow, domain="deskbee"):
    """Handle a config flow for Deskbee."""

    async def async_step_import(self, import_config: dict[str, Any]) -> FlowResult:
        return self.async_abort(reason="not_supported")

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        errors: dict[str, str] = {}
        if user_input is not None:
            return self.async_create_entry(
                title=user_input[CONF_DOMAIN], data=user_input
            )
        return self.async_show_form(
            step_id="user", data_schema=AUTH_SCHEMA, errors=errors
        )
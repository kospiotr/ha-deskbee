from __future__ import annotations

from typing import Any

import voluptuous as vol
from homeassistant import config_entries

from .const import DOMAIN


DATA_SCHEMA = vol.Schema(
    {
        vol.Required("name", default="Deskbee"): str,
        vol.Required("token"): str,
    }
)


class DeskbeeConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Deskbee."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.FlowResult:
        """Handle the initial step."""

        if user_input is None:
            return self.async_show_form(step_id="user", data_schema=DATA_SCHEMA)

        # Store the provided name and token in the config entry.
        return self.async_create_entry(
            title=user_input["name"],
            data={
                "name": user_input["name"],
                "token": user_input["token"],
            },
        )

from __future__ import annotations

from typing import Any

import homeassistant.helpers.config_validation as cv
import voluptuous as vol
from homeassistant.config_entries import ConfigEntry, ConfigFlow, OptionsFlow
from homeassistant.const import CONF_ACCESS_TOKEN
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers.selector import (
    SelectSelector,
    SelectSelectorConfig,
    TextSelector,
    TimeSelector,
)

from .const import CONF_BOOKINGS, CONF_DOMAIN

AUTH_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_DOMAIN): cv.string,
        vol.Required(CONF_ACCESS_TOKEN): cv.string,
    }
)


class DeskbeeConfigFlow(ConfigFlow, domain="deskbee"):
    """Handle a config flow for Deskbee."""

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry) -> DeskbeeOptionsFlow:
        return DeskbeeOptionsFlow(config_entry)

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


class DeskbeeOptionsFlow(OptionsFlow):
    """Handle Deskbee options (predefined booking templates)."""

    def __init__(self, config_entry: ConfigEntry) -> None:
        self._bookings: list[dict] = list(
            config_entry.options.get(CONF_BOOKINGS, [])
        )

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        menu_options = ["add_booking"]
        if self._bookings:
            menu_options.append("remove_booking")
        return self.async_show_menu(step_id="init", menu_options=menu_options)

    async def async_step_add_booking(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        errors: dict[str, str] = {}
        if user_input is not None:
            place_uuids = [
                u.strip()
                for u in user_input["place_uuids"].split(",")
                if u.strip()
            ]
            if not place_uuids:
                errors["place_uuids"] = "required"
            else:
                self._bookings.append(
                    {
                        "name": user_input["name"],
                        "start_time": user_input["start_time"],
                        "end_time": user_input["end_time"],
                        "place_uuids": place_uuids,
                    }
                )
                return self.async_create_entry(data={CONF_BOOKINGS: self._bookings})

        return self.async_show_form(
            step_id="add_booking",
            data_schema=vol.Schema(
                {
                    vol.Required("name"): TextSelector(),
                    vol.Required("start_time", default="08:30:00"): TimeSelector(),
                    vol.Required("end_time", default="17:00:00"): TimeSelector(),
                    vol.Required("place_uuids"): TextSelector(),
                }
            ),
            errors=errors,
        )

    async def async_step_remove_booking(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        if user_input is not None:
            self._bookings = [
                b for b in self._bookings if b["name"] != user_input["name"]
            ]
            return self.async_create_entry(data={CONF_BOOKINGS: self._bookings})

        return self.async_show_form(
            step_id="remove_booking",
            data_schema=vol.Schema(
                {
                    vol.Required("name"): SelectSelector(
                        SelectSelectorConfig(
                            options=[b["name"] for b in self._bookings]
                        )
                    ),
                }
            ),
        )

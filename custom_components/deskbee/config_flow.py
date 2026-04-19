from __future__ import annotations

from typing import Any, ClassVar

import homeassistant.helpers.config_validation as cv
import voluptuous as vol
from homeassistant.config_entries import ConfigEntry, ConfigFlow, ConfigSubentryFlow
from homeassistant.const import CONF_ACCESS_TOKEN
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers.selector import (
    TextSelector,
    TimeSelector,
)

from .const import CONF_DOMAIN

AUTH_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_DOMAIN): cv.string,
        vol.Required(CONF_ACCESS_TOKEN): cv.string,
    }
)


def _booking_schema(
    name: str = "",
    start_time: str = "08:30:00",
    end_time: str = "17:00:00",
    place_uuids: str = "",
) -> vol.Schema:
    """Return the schema for a booking template form, pre-filled with defaults."""
    return vol.Schema(
        {
            vol.Required("name", default=name): TextSelector(),
            vol.Required("start_time", default=start_time): TimeSelector(),
            vol.Required("end_time", default=end_time): TimeSelector(),
            vol.Required("place_uuids", default=place_uuids): TextSelector(),
        }
    )


def _parse_place_uuids(raw: str) -> list[str]:
    return [u.strip() for u in raw.split(",") if u.strip()]


class DeskbeeConfigFlow(ConfigFlow, domain="deskbee"):
    """Handle a config flow for Deskbee."""

    SUBENTRY_FLOWS: ClassVar[dict[str, type[ConfigSubentryFlow]]] = {
        "booking": DeskbeeBookingSubentryFlow,
    }

    async def async_step_reconfigure(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        entry = self._get_reconfigure_entry()
        if user_input is not None:
            return self.async_update_reload_and_abort(
                entry,
                data_updates=user_input,
            )
        return self.async_show_form(
            step_id="reconfigure",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_DOMAIN, default=entry.data.get(CONF_DOMAIN, "")): cv.string,
                    vol.Required(CONF_ACCESS_TOKEN): cv.string,
                }
            ),
        )

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


class DeskbeeBookingSubentryFlow(ConfigSubentryFlow):
    """Sub-entry flow for adding and editing a single booking template.

    Each booking template appears as a child row under the Deskbee integration
    card in Settings → Integrations.
    """

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Add a new booking template."""
        errors: dict[str, str] = {}
        if user_input is not None:
            place_uuids = _parse_place_uuids(user_input["place_uuids"])
            if not place_uuids:
                errors["place_uuids"] = "required"
            else:
                return self.async_create_entry(
                    title=user_input["name"],
                    data={
                        "name": user_input["name"],
                        "start_time": user_input["start_time"],
                        "end_time": user_input["end_time"],
                        "place_uuids": place_uuids,
                    },
                )

        return self.async_show_form(
            step_id="user",
            data_schema=_booking_schema(),
            errors=errors,
        )

    async def async_step_reconfigure(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Edit an existing booking template."""
        subentry = self._get_reconfigure_subentry()
        errors: dict[str, str] = {}

        if user_input is not None:
            place_uuids = _parse_place_uuids(user_input["place_uuids"])
            if not place_uuids:
                errors["place_uuids"] = "required"
            else:
                return self.async_update_and_abort(
                    self._config_entry,
                    subentry,
                    title=user_input["name"],
                    data={
                        "name": user_input["name"],
                        "start_time": user_input["start_time"],
                        "end_time": user_input["end_time"],
                        "place_uuids": place_uuids,
                    },
                )

        return self.async_show_form(
            step_id="reconfigure",
            data_schema=_booking_schema(
                name=subentry.data.get("name", ""),
                start_time=subentry.data.get("start_time", "08:30:00"),
                end_time=subentry.data.get("end_time", "17:00:00"),
                place_uuids=", ".join(subentry.data.get("place_uuids", [])),
            ),
            errors=errors,
        )

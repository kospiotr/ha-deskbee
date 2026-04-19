from __future__ import annotations

from typing import Any

import homeassistant.helpers.config_validation as cv
import voluptuous as vol
from homeassistant.config_entries import ConfigEntry, ConfigFlow, ConfigFlowResult, ConfigSubentryFlow, SubentryFlowResult
from homeassistant.const import CONF_ACCESS_TOKEN
from homeassistant.core import callback
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

    @classmethod
    @callback
    def async_get_supported_subentry_types(
        cls, config_entry: ConfigEntry
    ) -> dict[str, type[ConfigSubentryFlow]]:
        return {"booking": DeskbeeBookingSubentryFlow}

    async def async_step_reconfigure(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
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

    async def async_step_import(self, import_config: dict[str, Any]) -> ConfigFlowResult:
        return self.async_abort(reason="not_supported")

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        errors: dict[str, str] = {}
        if user_input is not None:
            await self.async_set_unique_id(user_input[CONF_DOMAIN])
            self._abort_if_unique_id_configured()
            return self.async_create_entry(
                title=user_input[CONF_DOMAIN], data=user_input
            )
        return self.async_show_form(
            step_id="user", data_schema=AUTH_SCHEMA, errors=errors
        )


class DeskbeeBookingSubentryFlow(ConfigSubentryFlow):
    """Subentry flow for managing a single booking template."""

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> SubentryFlowResult:
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
    ) -> SubentryFlowResult:
        subentry = self._get_reconfigure_subentry()
        errors: dict[str, str] = {}

        if user_input is not None:
            place_uuids = _parse_place_uuids(user_input["place_uuids"])
            if not place_uuids:
                errors["place_uuids"] = "required"
            else:
                return self.async_update_and_abort(
                    self._get_entry(),
                    self._get_reconfigure_subentry(),
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

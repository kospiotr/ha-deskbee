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

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry) -> DeskbeeOptionsFlow:
        return DeskbeeOptionsFlow(config_entry)

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


class DeskbeeOptionsFlow(OptionsFlow):
    """Options flow: manage booking templates via a navigable menu.

    init ──► add_booking  ──► (save)
         └─► select_booking ──► booking_menu ──► edit_booking  ──► (save)
                                             └─► delete_booking ──► (save)
    """

    def __init__(self, config_entry: ConfigEntry) -> None:
        self._bookings: list[dict] = list(
            config_entry.options.get(CONF_BOOKINGS, [])
        )
        self._selected: str | None = None

    # ------------------------------------------------------------------ #
    # Root                                                                 #
    # ------------------------------------------------------------------ #

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        if self._bookings:
            lines = [
                f"• {b['name']}  ({b['start_time'][:5]}–{b['end_time'][:5]})"
                for b in self._bookings
            ]
            bookings_list = "\n".join(lines)
        else:
            bookings_list = "No booking templates configured yet."

        menu_options = ["add_booking"]
        if self._bookings:
            menu_options.append("select_booking")

        return self.async_show_menu(
            step_id="init",
            menu_options=menu_options,
            description_placeholders={"bookings_list": bookings_list},
        )

    # ------------------------------------------------------------------ #
    # Add                                                                  #
    # ------------------------------------------------------------------ #

    async def async_step_add_booking(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        errors: dict[str, str] = {}
        if user_input is not None:
            place_uuids = _parse_place_uuids(user_input["place_uuids"])
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
            data_schema=_booking_schema(),
            errors=errors,
        )

    # ------------------------------------------------------------------ #
    # Select → per-booking menu                                            #
    # ------------------------------------------------------------------ #

    async def async_step_select_booking(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        if user_input is not None:
            self._selected = user_input["name"]
            return await self.async_step_booking_menu()

        return self.async_show_form(
            step_id="select_booking",
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

    async def async_step_booking_menu(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        booking = self._get_selected()
        return self.async_show_menu(
            step_id="booking_menu",
            menu_options=["edit_booking", "delete_booking"],
            description_placeholders={
                "name": booking["name"],
                "start_time": booking["start_time"][:5],
                "end_time": booking["end_time"][:5],
                "place_uuids": ", ".join(booking["place_uuids"]),
            },
        )

    # ------------------------------------------------------------------ #
    # Edit                                                                 #
    # ------------------------------------------------------------------ #

    async def async_step_edit_booking(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        booking = self._get_selected()
        errors: dict[str, str] = {}

        if user_input is not None:
            place_uuids = _parse_place_uuids(user_input["place_uuids"])
            if not place_uuids:
                errors["place_uuids"] = "required"
            else:
                idx = next(
                    i for i, b in enumerate(self._bookings)
                    if b["name"] == self._selected
                )
                self._bookings[idx] = {
                    "name": user_input["name"],
                    "start_time": user_input["start_time"],
                    "end_time": user_input["end_time"],
                    "place_uuids": place_uuids,
                }
                return self.async_create_entry(data={CONF_BOOKINGS: self._bookings})

        return self.async_show_form(
            step_id="edit_booking",
            data_schema=_booking_schema(
                name=booking["name"],
                start_time=booking["start_time"],
                end_time=booking["end_time"],
                place_uuids=", ".join(booking["place_uuids"]),
            ),
            errors=errors,
        )

    # ------------------------------------------------------------------ #
    # Delete                                                               #
    # ------------------------------------------------------------------ #

    async def async_step_delete_booking(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        if user_input is not None:
            self._bookings = [
                b for b in self._bookings if b["name"] != self._selected
            ]
            return self.async_create_entry(data={CONF_BOOKINGS: self._bookings})

        return self.async_show_form(
            step_id="delete_booking",
            data_schema=vol.Schema({}),
            description_placeholders={"name": self._selected},
        )

    # ------------------------------------------------------------------ #
    # Helpers                                                              #
    # ------------------------------------------------------------------ #

    def _get_selected(self) -> dict:
        return next(b for b in self._bookings if b["name"] == self._selected)

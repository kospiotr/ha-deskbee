from __future__ import annotations

from datetime import time

import voluptuous as vol
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_ACCESS_TOKEN
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import config_validation as cv

import logging

from .const import CONF_DOMAIN, DOMAIN

_LOGGER = logging.getLogger(__name__)
from .coordinator import DeskbeeCoordinator

SERVICE_CREATE_RESERVATION = "create_reservation"

_SERVICE_SCHEMA = vol.Schema(
    {
        vol.Required("place_uuids"): vol.All(cv.ensure_list, [cv.string]),
        vol.Required("date"): cv.date,
        vol.Optional("start_time", default=time(8, 30)): cv.time,
        vol.Optional("end_time", default=time(17, 0)): cv.time,
        vol.Optional("reason", default=""): cv.string,
    }
)


async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    """Set up the Deskbee integration from YAML (not used)."""
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Deskbee from a config entry."""
    coordinator = DeskbeeCoordinator(
        hass,
        account=entry.data[CONF_DOMAIN],
        token=entry.data[CONF_ACCESS_TOKEN],
    )
    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, ["sensor"])

    # Register the service once (when the first entry is set up).
    if not hass.services.has_service(DOMAIN, SERVICE_CREATE_RESERVATION):

        async def _handle_create_reservation(call: ServiceCall) -> None:
            coordinators: list[DeskbeeCoordinator] = list(
                hass.data.get(DOMAIN, {}).values()
            )
            if not coordinators:
                raise HomeAssistantError("No Deskbee config entry is loaded")

            coord = coordinators[0]
            date_str = call.data["date"].strftime("%d/%m/%Y")
            start_hour = call.data["start_time"].strftime("%H:%M")
            end_hour = call.data["end_time"].strftime("%H:%M")
            place_uuids: list[str] = call.data["place_uuids"]

            for place_uuid in place_uuids:
                try:
                    await coord.async_create_reservation(
                        place_uuid=place_uuid,
                        start_date=date_str,
                        start_hour=start_hour,
                        end_date=date_str,
                        end_hour=end_hour,
                        reason=call.data.get("reason", ""),
                    )
                    _LOGGER.info("Deskbee reservation created for place %s", place_uuid)
                    break
                except Exception as err:
                    _LOGGER.warning(
                        "Deskbee booking failed for place %s, trying next: %s",
                        place_uuid,
                        err,
                    )
            else:
                raise HomeAssistantError(
                    f"All {len(place_uuids)} place(s) failed — no reservation was created"
                )

            # Refresh so the reservations sensor reflects the new booking.
            await coord.async_request_refresh()

        hass.services.async_register(
            DOMAIN,
            SERVICE_CREATE_RESERVATION,
            _handle_create_reservation,
            schema=_SERVICE_SCHEMA,
        )

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, ["sensor"])
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id, None)

    # Remove the service when the last entry is gone.
    if not hass.data.get(DOMAIN):
        hass.services.async_remove(DOMAIN, SERVICE_CREATE_RESERVATION)

    return unload_ok
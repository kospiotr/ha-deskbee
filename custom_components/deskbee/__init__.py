from __future__ import annotations

import logging
from datetime import date, time, timedelta

import voluptuous as vol
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_ACCESS_TOKEN
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import config_validation as cv
from homeassistant.util import slugify

from .const import CONF_BOOKINGS, CONF_DOMAIN, DOMAIN
from .coordinator import DeskbeeCoordinator

_LOGGER = logging.getLogger(__name__)

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


def _format_time(t: str) -> str:
    """Slice a stored time string (HH:MM or HH:MM:SS) to HH:MM for the API."""
    return t[:5]


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

    # ── Generic create_reservation service (registered once across all entries) ──
    if not hass.services.has_service(DOMAIN, SERVICE_CREATE_RESERVATION):

        async def _handle_create_reservation(call: ServiceCall) -> None:
            coords = [
                v for v in hass.data.get(DOMAIN, {}).values()
                if isinstance(v, DeskbeeCoordinator)
            ]
            if not coords:
                raise HomeAssistantError("No Deskbee config entry is loaded")

            coord = coords[0]
            date_str = call.data["date"].strftime("%d/%m/%Y")
            start_hour = call.data["start_time"].strftime("%H:%M")
            end_hour = call.data["end_time"].strftime("%H:%M")

            for place_uuid in call.data["place_uuids"]:
                try:
                    await coord.async_create_reservation(
                        place_uuid=place_uuid,
                        start_date=date_str,
                        start_hour=start_hour,
                        end_date=date_str,
                        end_hour=end_hour,
                        reason=call.data.get("reason", ""),
                    )
                    _LOGGER.info("Reservation created for place %s", place_uuid)
                    break
                except Exception as err:
                    _LOGGER.warning("Booking failed for %s, trying next: %s", place_uuid, err)
            else:
                raise HomeAssistantError(
                    f"All {len(call.data['place_uuids'])} place(s) failed — no reservation created"
                )
            await coord.async_request_refresh()

        hass.services.async_register(
            DOMAIN, SERVICE_CREATE_RESERVATION, _handle_create_reservation,
            schema=_SERVICE_SCHEMA,
        )

    # ── Per-booking template services ──
    booking_service_names: list[str] = []

    for booking in entry.options.get(CONF_BOOKINGS, []):
        slug = slugify(booking["name"])

        for label, delta in [("today", 0), ("tomorrow", 1)]:
            svc_name = f"{slug}_book_{label}"

            async def _handle_book(
                call: ServiceCall,
                _b: dict = booking,
                _delta: int = delta,
            ) -> None:
                coord: DeskbeeCoordinator = hass.data[DOMAIN][entry.entry_id]
                target = date.today() + timedelta(days=_delta)
                date_str = target.strftime("%d/%m/%Y")

                for place_uuid in _b["place_uuids"]:
                    try:
                        await coord.async_create_reservation(
                            place_uuid=place_uuid,
                            start_date=date_str,
                            start_hour=_format_time(_b["start_time"]),
                            end_date=date_str,
                            end_hour=_format_time(_b["end_time"]),
                        )
                        _LOGGER.info(
                            "Booking '%s' created for %s on %s",
                            _b["name"], place_uuid, target,
                        )
                        break
                    except Exception as err:
                        _LOGGER.warning(
                            "Booking '%s' failed for %s: %s", _b["name"], place_uuid, err
                        )
                else:
                    raise HomeAssistantError(
                        f"All places failed for booking '{_b['name']}'"
                    )
                await coord.async_request_refresh()

            hass.services.async_register(DOMAIN, svc_name, _handle_book)
            booking_service_names.append(svc_name)

    hass.data[DOMAIN].setdefault("_booking_services", {})[entry.entry_id] = booking_service_names

    # Reload entry whenever options change (new/removed booking templates).
    entry.add_update_listener(_async_update_listener)

    return True


async def _async_update_listener(hass: HomeAssistant, entry: ConfigEntry) -> None:
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, ["sensor"])
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id, None)
        for svc_name in hass.data[DOMAIN].get("_booking_services", {}).pop(entry.entry_id, []):
            hass.services.async_remove(DOMAIN, svc_name)

    remaining = [
        k for k in hass.data.get(DOMAIN, {})
        if not k.startswith("_")
    ]
    if not remaining:
        hass.services.async_remove(DOMAIN, SERVICE_CREATE_RESERVATION)

    return unload_ok

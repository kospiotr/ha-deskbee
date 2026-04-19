from __future__ import annotations

import logging
from datetime import date, datetime, timedelta, timezone
from typing import Any

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_ACCESS_TOKEN
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.util import slugify

from .const import CONF_DOMAIN, DOMAIN
from .coordinator import DeskbeeCoordinator, decode_jwt_expiry

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Deskbee sensors for a config entry."""
    domain = entry.data[CONF_DOMAIN]
    token = entry.data[CONF_ACCESS_TOKEN]
    coordinator: DeskbeeCoordinator = hass.data[DOMAIN][entry.entry_id]

    entities: list[SensorEntity] = [
        DeskbeeTokenExpirySensor(entry.entry_id, domain, token),
        DeskbeeTokenValidSensor(entry.entry_id, domain, token),
        DeskbeeReservationsSensor(entry.entry_id, domain, coordinator),
    ]

    for subentry in entry.subentries.values():
        booking = dict(subentry.data)
        for when in ("today", "tomorrow", "other"):
            entities.append(
                DeskbeeBookingSensor(entry.entry_id, booking, coordinator, when)
            )

    async_add_entities(entities)


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------

def _reservation_local_date(r: dict) -> date:
    """Parse the local date from a reservation's start_date field."""
    return datetime.fromisoformat(r["start_date"]).date()


def _reservation_summary(r: dict) -> dict[str, Any]:
    return {
        "uuid": r["uuid"],
        "start_date": r["start_date"],
        "end_date": r["end_date"],
        "place_type": r.get("place_type"),
        "place": r["place"]["name_display"],
        "area": r["place"]["area_full"],
        "status": r["status"]["name"],
    }


# ---------------------------------------------------------------------------
# Token sensors
# ---------------------------------------------------------------------------

class DeskbeeTokenExpirySensor(SensorEntity):
    """Sensor reporting when the Deskbee API token expires."""

    _attr_device_class = SensorDeviceClass.TIMESTAMP

    def __init__(self, entry_id: str, domain: str, token: str) -> None:
        self._attr_name = f"Deskbee Token Expiry ({domain})"
        self._attr_unique_id = f"{entry_id}_token_expiry"
        self._token = token

    @property
    def native_value(self) -> datetime | None:
        return decode_jwt_expiry(self._token)


class DeskbeeTokenValidSensor(SensorEntity):
    """Sensor reporting whether the Deskbee API token is currently valid."""

    def __init__(self, entry_id: str, domain: str, token: str) -> None:
        self._attr_name = f"Deskbee Token Valid ({domain})"
        self._attr_unique_id = f"{entry_id}_token_valid"
        self._token = token

    @property
    def native_value(self) -> str:
        expiry = decode_jwt_expiry(self._token)
        if expiry is None:
            return "invalid"
        return "valid" if datetime.now(tz=timezone.utc) < expiry else "invalid"


# ---------------------------------------------------------------------------
# Live reservations sensor (all upcoming)
# ---------------------------------------------------------------------------

class DeskbeeReservationsSensor(CoordinatorEntity[DeskbeeCoordinator], SensorEntity):
    """Sensor exposing the count and details of all upcoming reservations."""

    def __init__(
        self, entry_id: str, domain: str, coordinator: DeskbeeCoordinator
    ) -> None:
        super().__init__(coordinator)
        self._attr_name = f"Deskbee Reservations ({domain})"
        self._attr_unique_id = f"{entry_id}_reservations"

    @property
    def native_value(self) -> int:
        return len(self.coordinator.data or [])

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        return {
            "reservations": [
                _reservation_summary(r) for r in (self.coordinator.data or [])
            ]
        }


# ---------------------------------------------------------------------------
# Booking template sensors (today / tomorrow / other)
# ---------------------------------------------------------------------------

class DeskbeeBookingSensor(CoordinatorEntity[DeskbeeCoordinator], SensorEntity):
    """Counts reservations for a predefined booking template in a time window.

    when='today'    → reservations whose start_date is today
    when='tomorrow' → reservations whose start_date is tomorrow
    when='other'    → reservations whose start_date is the day after tomorrow or later
    """

    def __init__(
        self,
        entry_id: str,
        booking: dict,
        coordinator: DeskbeeCoordinator,
        when: str,
    ) -> None:
        super().__init__(coordinator)
        self._booking = booking
        self._when = when
        slug = slugify(booking["name"])
        self._attr_name = f"{booking['name']} Reservations {when.capitalize()}"
        self._attr_unique_id = f"{entry_id}_{slug}_reservations_{when}"

    def _matching(self) -> list[dict]:
        today = date.today()
        tomorrow = today + timedelta(days=1)

        def _date_ok(d: date) -> bool:
            if self._when == "today":
                return d == today
            if self._when == "tomorrow":
                return d == tomorrow
            return d > tomorrow  # "other"

        return [
            r for r in (self.coordinator.data or [])
            if r["place"]["uuid"] in self._booking["place_uuids"]
            and _date_ok(_reservation_local_date(r))
        ]

    @property
    def native_value(self) -> int:
        return len(self._matching())

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        return {"reservations": [_reservation_summary(r) for r in self._matching()]}

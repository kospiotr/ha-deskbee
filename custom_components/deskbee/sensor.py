from __future__ import annotations

import base64
import json
import logging
from datetime import datetime, timezone
from typing import Any

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_ACCESS_TOKEN
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import CONF_DOMAIN, DOMAIN
from .coordinator import DeskbeeCoordinator

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
    async_add_entities(
        [
            DeskbeeTokenExpirySensor(entry.entry_id, domain, token),
            DeskbeeTokenValidSensor(entry.entry_id, domain, token),
            DeskbeeReservationsSensor(entry.entry_id, domain, coordinator),
        ]
    )


# ---------------------------------------------------------------------------
# JWT helpers
# ---------------------------------------------------------------------------

def _decode_jwt_expiry(token: str) -> datetime | None:
    """Return the exp claim from a JWT as an aware UTC datetime, without verifying the signature."""
    try:
        payload_b64 = token.split(".")[1]
        # JWT uses base64url without padding — restore it before decoding.
        payload_b64 += "=" * (-len(payload_b64) % 4)
        payload = json.loads(base64.urlsafe_b64decode(payload_b64))
        return datetime.fromtimestamp(payload["exp"], tz=timezone.utc)
    except Exception as err:
        _LOGGER.error("Failed to decode JWT expiry: %s", err)
        return None


# ---------------------------------------------------------------------------
# Token sensors (static — derived from the JWT in config entry data)
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
        """Return the token expiry as a UTC datetime."""
        return _decode_jwt_expiry(self._token)


class DeskbeeTokenValidSensor(SensorEntity):
    """Sensor reporting whether the Deskbee API token is currently valid."""

    def __init__(self, entry_id: str, domain: str, token: str) -> None:
        self._attr_name = f"Deskbee Token Valid ({domain})"
        self._attr_unique_id = f"{entry_id}_token_valid"
        self._token = token

    @property
    def native_value(self) -> str:
        """Return 'valid' if the token has not expired, 'invalid' otherwise."""
        expiry = _decode_jwt_expiry(self._token)
        if expiry is None:
            return "invalid"
        return "valid" if datetime.now(tz=timezone.utc) < expiry else "invalid"


# ---------------------------------------------------------------------------
# Reservations sensor (live — backed by the coordinator)
# ---------------------------------------------------------------------------

class DeskbeeReservationsSensor(CoordinatorEntity[DeskbeeCoordinator], SensorEntity):
    """Sensor exposing the count and details of upcoming Deskbee reservations."""

    def __init__(
        self, entry_id: str, domain: str, coordinator: DeskbeeCoordinator
    ) -> None:
        super().__init__(coordinator)
        self._attr_name = f"Deskbee Reservations ({domain})"
        self._attr_unique_id = f"{entry_id}_reservations"

    @property
    def native_value(self) -> int:
        """Return the number of reservations."""
        return len(self.coordinator.data or [])

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return each reservation's key fields as attributes."""
        return {
            "reservations": [
                {
                    "uuid": r["uuid"],
                    "start_date": r["start_date"],
                    "end_date": r["end_date"],
                    "place_type": r.get("place_type"),
                    "place": r["place"]["name_display"],
                    "area": r["place"]["area_full"],
                    "status": r["status"]["name"],
                }
                for r in (self.coordinator.data or [])
            ]
        }
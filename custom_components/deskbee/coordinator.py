from __future__ import annotations

import logging
from datetime import timedelta

from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

_BOOKINGS_URL = "https://api.deskbee.io/api/bookings/me"
_CREATE_BOOKING_URL = "https://api.deskbee.io/api/bookings"
_BOOKINGS_PARAMS = {
    "page": "1",
    "limit": "10",
    "search": "type:;search:;period:;filter:;uuid:",
    "include": "service;recurrences;meeting;calendar_integration;is_extend;resources;checkin;type;parking;tolerance;reason;parent",
}
_APP_VERSION = "1.237.6060"
_UPDATE_INTERVAL = timedelta(minutes=30)


class DeskbeeCoordinator(DataUpdateCoordinator[list[dict]]):
    """Polls the Deskbee bookings API on a schedule."""

    def __init__(self, hass: HomeAssistant, account: str, token: str) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=_UPDATE_INTERVAL,
        )
        self._account = account
        self._token = token

    async def _async_update_data(self) -> list[dict]:
        session = async_get_clientsession(self.hass)
        headers = {
            "accept": "application/json",
            "authorization": f"Bearer {self._token}",
            "x-app-account": self._account,
            "x-app-version": _APP_VERSION,
        }
        try:
            async with session.get(
                _BOOKINGS_URL, headers=headers, params=_BOOKINGS_PARAMS
            ) as response:
                response.raise_for_status()
                body = await response.json()
                return body.get("data", [])
        except Exception as err:
            raise UpdateFailed(f"Error fetching Deskbee reservations: {err}") from err

    async def async_create_reservation(
        self,
        place_uuid: str,
        start_date: str,
        start_hour: str,
        end_date: str,
        end_hour: str,
        reason: str = "",
    ) -> dict:
        """POST a new booking to the Deskbee API.

        Dates must be formatted as DD/MM/YYYY; hours as HH:MM.
        """
        session = async_get_clientsession(self.hass)
        headers = {
            "accept": "application/json",
            "authorization": f"Bearer {self._token}",
            "content-type": "application/json",
            "x-app-account": self._account,
            "x-app-version": _APP_VERSION,
        }
        payload = {
            "uuid": place_uuid,
            "start_date": start_date,
            "start_hour": start_hour,
            "end_date": end_date,
            "end_hour": end_hour,
            "reason": reason,
            "booking_uuid_identifier": None,
        }
        async with session.post(
            _CREATE_BOOKING_URL, headers=headers, json=payload
        ) as response:
            response.raise_for_status()
            return await response.json()
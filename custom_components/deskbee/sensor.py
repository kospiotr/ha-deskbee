from __future__ import annotations

from datetime import datetime
from typing import Any

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    add_entities: AddEntitiesCallback,
    ) -> None:
    """Set up Deskbee sensors for a config entry."""

    # For the initial hello-world implementation we expose a single demo sensor.
    add_entities([DeskbeeDemoReservationSensor()])


async def async_setup_platform(
    hass: HomeAssistant,
    config: ConfigType,
    async_add_entities: AddEntitiesCallback,
    discovery_info: DiscoveryInfoType | None = None,
) -> None:
    """Set up Deskbee sensors from YAML configuration."""

    async_add_entities([DeskbeeDemoReservationSensor()])


class DeskbeeDemoReservationSensor(SensorEntity):
    """Demo sensor showing a synthetic Deskbee reservation status."""

    _attr_name = "Deskbee Demo Reservation Status"
    _attr_unique_id = "deskbee_demo_reservation_status"

    @property
    def native_value(self) -> str:
        """Return a dynamic demo value.

        This will later be replaced with real Deskbee reservation data.
        """

        return f"demo-active-{datetime.now().strftime('%H:%M')}"

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.util import dt as dt_util

from .const import DOMAIN
from .coordinator import DHLPackstationCoordinator
from .entity import DHLPackstationEntity

WEEKDAYS = (
    "Monday",
    "Tuesday",
    "Wednesday",
    "Thursday",
    "Friday",
    "Saturday",
    "Sunday",
)

FORECAST_OPTIONS = ["high", "low", "very_low", "unknown"]

STATUS_ICONS = {
    "high": "mdi:check-circle-outline",
    "low": "mdi:alert-circle-outline",
    "very_low": "mdi:close-circle-outline",
    "unknown": "mdi:help-circle-outline",
}


@dataclass(frozen=True, kw_only=True)
class ForecastDescription(SensorEntityDescription):
    """Description for one weekday forecast entity."""

    weekday: str


WEEKDAY_DESCRIPTIONS = tuple(
    ForecastDescription(
        key=f"forecast_{weekday.lower()}",
        translation_key=f"forecast_{weekday.lower()}",
        weekday=weekday,
        device_class=SensorDeviceClass.ENUM,
        options=FORECAST_OPTIONS,
    )
    for weekday in WEEKDAYS
)


def _normalize_capacity(value: str | None) -> str:
    """Convert DHL values to Home Assistant enum-compatible states."""
    if value == "very-low":
        return "very_low"
    if value in FORECAST_OPTIONS:
        return value
    return "unknown"


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up all Packstation sensors."""
    coordinator: DHLPackstationCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        [
            CapacitySensor(coordinator),
            *(
                ForecastDaySensor(coordinator, description)
                for description in WEEKDAY_DESCRIPTIONS
            ),
            LastUpdateSensor(coordinator),
        ]
    )


class ForecastSensorEntity(DHLPackstationEntity, SensorEntity):
    """Base class for translated Packstation forecast sensors."""

    _attr_has_entity_name = True
    _attr_device_class = SensorDeviceClass.ENUM
    _attr_options = FORECAST_OPTIONS

    @property
    def icon(self) -> str:
        """Return an icon matching the forecast state."""
        return STATUS_ICONS.get(self.native_value, STATUS_ICONS["unknown"])


class CapacitySensor(ForecastSensorEntity):
    """Expose the forecast for the current local weekday."""

    _attr_translation_key = "capacity"

    def __init__(self, coordinator: DHLPackstationCoordinator) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.data.location_id}_capacity"

    @property
    def native_value(self) -> str:
        """Return today's normalized forecast."""
        weekday = dt_util.now().strftime("%A")
        return _normalize_capacity(
            self.coordinator.data.capacity_for_weekday(weekday)
        )

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Expose station metadata and the normalized weekly forecast."""
        data = self.coordinator.data
        weekday = dt_util.now().strftime("%A")
        weekly = {
            day: _normalize_capacity(data.weekly_forecast.get(day))
            for day in WEEKDAYS
        }
        return {
            "location_id": data.location_id,
            "station_number": data.station_number,
            "station_name": data.station_name,
            "display_name": data.display_name,
            "street": data.street,
            "postal_code": data.postal_code,
            "city": data.city,
            "country_code": data.country_code,
            "contained_in_place": data.contained_in_place,
            "latitude": data.latitude,
            "longitude": data.longitude,
            "current_weekday": weekday,
            "capacity_today": weekly.get(weekday, "unknown"),
            "weekly_forecast": weekly,
            "averageCapacityDayOfWeek": [
                {"dayOfWeek": day, "capacity": weekly[day]}
                for day in WEEKDAYS
            ],
            "data_type": "average_capacity_by_weekday",
            "is_live_data": False,
            "last_successful_update": (
                self.coordinator.last_successful_update.isoformat()
                if self.coordinator.last_successful_update
                else None
            ),
        }


class ForecastDaySensor(ForecastSensorEntity):
    """Expose the forecast for one fixed weekday."""

    entity_description: ForecastDescription

    def __init__(
        self,
        coordinator: DHLPackstationCoordinator,
        description: ForecastDescription,
    ) -> None:
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = (
            f"{coordinator.data.location_id}_{description.key}"
        )

    @property
    def native_value(self) -> str:
        """Return the normalized forecast for this weekday."""
        return _normalize_capacity(
            self.coordinator.data.capacity_for_weekday(
                self.entity_description.weekday
            )
        )

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Expose stable metadata for card and automation matching."""
        return {
            "location_id": self.coordinator.data.location_id,
            "weekday": self.entity_description.weekday,
            "is_live_data": False,
            "data_type": "weekday_capacity_forecast",
        }


class LastUpdateSensor(DHLPackstationEntity, SensorEntity):
    """Expose the timestamp of the last successful DHL request."""

    _attr_has_entity_name = True
    _attr_translation_key = "last_update"
    _attr_device_class = SensorDeviceClass.TIMESTAMP
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(self, coordinator: DHLPackstationCoordinator) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.data.location_id}_last_update"

    @property
    def native_value(self):
        """Return the coordinator's last successful update timestamp."""
        return self.coordinator.last_successful_update

from __future__ import annotations

from typing import Any

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity
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

WEEKDAY_TRANSLATION_KEYS = {
    "Monday": "forecast_monday",
    "Tuesday": "forecast_tuesday",
    "Wednesday": "forecast_wednesday",
    "Thursday": "forecast_thursday",
    "Friday": "forecast_friday",
    "Saturday": "forecast_saturday",
    "Sunday": "forecast_sunday",
}

FORECAST_OPTIONS = ["high", "low", "very_low", "unknown"]

STATUS_ICONS = {
    "high": "mdi:check-circle-outline",
    "low": "mdi:alert-circle-outline",
    "very_low": "mdi:close-circle-outline",
    "unknown": "mdi:help-circle-outline",
}


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
            *(ForecastDaySensor(coordinator, weekday) for weekday in WEEKDAYS),
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
    _attr_icon = "mdi:package-variant-closed"

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

    def __init__(
        self,
        coordinator: DHLPackstationCoordinator,
        weekday: str,
    ) -> None:
        super().__init__(coordinator)
        self._weekday = weekday
        self._attr_translation_key = WEEKDAY_TRANSLATION_KEYS[weekday]
        self._attr_unique_id = (
            f"{coordinator.data.location_id}_forecast_{weekday.lower()}"
        )

    @property
    def native_value(self) -> str:
        """Return the normalized forecast for this weekday."""
        return _normalize_capacity(
            self.coordinator.data.capacity_for_weekday(self._weekday)
        )

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Expose the stable English weekday key."""
        return {
            "weekday": self._weekday,
            "is_live_data": False,
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

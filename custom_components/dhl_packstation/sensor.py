from homeassistant.components.sensor import SensorDeviceClass, SensorEntity
from homeassistant.const import EntityCategory
from homeassistant.util import dt as dt_util

from .const import DOMAIN
from .entity import DHLPackstationEntity


async def async_setup_entry(hass, entry, async_add_entities):
    coordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        [
            CapacitySensor(coordinator),
            LastUpdateSensor(coordinator),
        ]
    )


class CapacitySensor(DHLPackstationEntity, SensorEntity):
    _attr_translation_key = "capacity"
    _attr_icon = "mdi:package-variant-closed"

    def __init__(self, coordinator):
        super().__init__(coordinator)
        self._attr_unique_id = (
            f"{coordinator.data.location_id}_capacity"
        )

    @property
    def native_value(self):
        weekday = dt_util.now().strftime("%A")
        return self.coordinator.data.capacity_for_weekday(weekday)

    @property
    def extra_state_attributes(self):
        data = self.coordinator.data
        weekday = dt_util.now().strftime("%A")
        ordered_days = (
            "Monday",
            "Tuesday",
            "Wednesday",
            "Thursday",
            "Friday",
            "Saturday",
            "Sunday",
        )
        weekly = {
            day: data.weekly_forecast.get(day, "unknown")
            for day in ordered_days
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
                {
                    "dayOfWeek": day,
                    "capacity": weekly[day],
                }
                for day in ordered_days
            ],
            "data_type": "average_capacity_by_weekday",
            "is_live_data": False,
            "last_successful_update": (
                self.coordinator.last_successful_update.isoformat()
                if self.coordinator.last_successful_update
                else None
            ),
        }


class LastUpdateSensor(DHLPackstationEntity, SensorEntity):
    _attr_translation_key = "last_update"
    _attr_device_class = SensorDeviceClass.TIMESTAMP
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(self, coordinator):
        super().__init__(coordinator)
        self._attr_unique_id = (
            f"{coordinator.data.location_id}_last_update"
        )

    @property
    def native_value(self):
        return self.coordinator.last_successful_update

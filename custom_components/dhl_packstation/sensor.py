from datetime import datetime
from homeassistant.components.sensor import SensorEntity,SensorDeviceClass
from homeassistant.const import EntityCategory
from .const import DOMAIN
from .entity import DHLPackstationEntity
async def async_setup_entry(hass,entry,async_add_entities):
 c=hass.data[DOMAIN][entry.entry_id]; async_add_entities([CapacitySensor(c),LastUpdateSensor(c)])
class CapacitySensor(DHLPackstationEntity,SensorEntity):
 _attr_translation_key="capacity"; _attr_icon="mdi:package-variant-closed"
 def __init__(self,c): super().__init__(c); self._attr_unique_id=f"{c.data.location_id}_capacity"
 @property
 def native_value(self): return self.coordinator.data.capacity_for_weekday(datetime.now().strftime("%A"))
 @property
 def extra_state_attributes(self):
  d=self.coordinator.data
  return {"location_id":d.location_id,"station_number":d.station_number,"station_name":d.station_name,"display_name":d.display_name,"street":d.street,"postal_code":d.postal_code,"city":d.city,"country_code":d.country_code,"contained_in_place":d.contained_in_place,"latitude":d.latitude,"longitude":d.longitude,"weekly_forecast":d.weekly_forecast,"averageCapacityDayOfWeek":[{"dayOfWeek":k,"capacity":v} for k,v in d.weekly_forecast.items()],"data_type":"average_capacity_by_weekday","is_live_data":False}
class LastUpdateSensor(DHLPackstationEntity,SensorEntity):
 _attr_translation_key="last_update"; _attr_device_class=SensorDeviceClass.TIMESTAMP; _attr_entity_category=EntityCategory.DIAGNOSTIC
 def __init__(self,c): super().__init__(c); self._attr_unique_id=f"{c.data.location_id}_last_update"
 @property
 def native_value(self): return self.coordinator.last_update_success_time

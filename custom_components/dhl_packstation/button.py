from homeassistant.components.button import ButtonEntity
from homeassistant.const import EntityCategory
from .const import DOMAIN
from .entity import DHLPackstationEntity
async def async_setup_entry(hass,entry,async_add_entities): async_add_entities([RefreshButton(hass.data[DOMAIN][entry.entry_id])])
class RefreshButton(DHLPackstationEntity,ButtonEntity):
 _attr_translation_key="refresh"; _attr_icon="mdi:refresh"; _attr_entity_category=EntityCategory.CONFIG
 def __init__(self,c): super().__init__(c); self._attr_unique_id=f"{c.data.location_id}_refresh"
 async def async_press(self): await self.coordinator.async_request_refresh()

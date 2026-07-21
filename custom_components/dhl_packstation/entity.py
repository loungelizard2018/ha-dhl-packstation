from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from .const import DOMAIN
class DHLPackstationEntity(CoordinatorEntity):
 _attr_has_entity_name=True
 def __init__(self,coordinator):
  super().__init__(coordinator); self._attr_device_info=DeviceInfo(identifiers={(DOMAIN,coordinator.data.location_id)},name=coordinator.data.display_name,manufacturer="DHL",model="Packstation capacity forecast")

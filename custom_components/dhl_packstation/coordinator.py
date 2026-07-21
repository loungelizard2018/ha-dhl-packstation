from datetime import timedelta
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator,UpdateFailed
from .api import DHLAuthError,DHLError
from .const import *
class DHLPackstationCoordinator(DataUpdateCoordinator):
 def __init__(self,hass,entry,client):
  self.entry=entry; self.client=client
  super().__init__(hass,name=f"{DOMAIN}_{entry.entry_id}",update_interval=timedelta(hours=int(entry.options.get(CONF_UPDATE_INTERVAL,DEFAULT_UPDATE_INTERVAL))),config_entry=entry)
 async def _async_update_data(self):
  try:return await self.client.async_get_station(country_code=self.entry.data[CONF_COUNTRY_CODE],postal_code=self.entry.data[CONF_POSTAL_CODE],station_number=self.entry.data[CONF_STATION_NUMBER],display_name=self.entry.options.get(CONF_DISPLAY_NAME,self.entry.data.get(CONF_DISPLAY_NAME)))
  except DHLAuthError as e: raise ConfigEntryAuthFailed from e
  except DHLError as e: raise UpdateFailed(str(e)) from e

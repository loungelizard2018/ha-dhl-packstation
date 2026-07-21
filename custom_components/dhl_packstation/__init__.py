from pathlib import Path
from homeassistant.components.frontend import DATA_EXTRA_MODULE_URL
from homeassistant.components.http import StaticPathConfig
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from .api import DHLPackstationApiClient
from .const import *
from .coordinator import DHLPackstationCoordinator
async def async_setup(hass,config):
 await hass.http.async_register_static_paths([StaticPathConfig(STATIC_URL,str(Path(__file__).parent/"frontend"),True)])
 urls=hass.data.get(DATA_EXTRA_MODULE_URL)
 if urls is not None: urls.add(CARD_URL)
 hass.data.setdefault(DOMAIN,{})
 return True
async def async_setup_entry(hass,entry):
 c=DHLPackstationCoordinator(hass,entry,DHLPackstationApiClient(async_get_clientsession(hass),entry.data[CONF_API_KEY])); await c.async_config_entry_first_refresh(); hass.data.setdefault(DOMAIN,{})[entry.entry_id]=c; await hass.config_entries.async_forward_entry_setups(entry,PLATFORMS); entry.async_on_unload(entry.add_update_listener(_reload)); return True
async def async_unload_entry(hass,entry):
 ok=await hass.config_entries.async_unload_platforms(entry,PLATFORMS)
 if ok:hass.data[DOMAIN].pop(entry.entry_id,None)
 return ok
async def _reload(hass,entry): await hass.config_entries.async_reload(entry.entry_id)

from typing import Any
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.selector import NumberSelector,NumberSelectorConfig,NumberSelectorMode
from .api import DHLPackstationApiClient,DHLAuthError,DHLNotFoundError,DHLConnectionError,DHLResponseError
from .const import *
class DHLPackstationConfigFlow(config_entries.ConfigFlow,domain=DOMAIN):
 VERSION=1
 async def async_step_user(self,user_input=None):
  errors={}
  if user_input is not None:
   try:s=await DHLPackstationApiClient(async_get_clientsession(self.hass),user_input[CONF_API_KEY]).async_get_station(country_code=user_input[CONF_COUNTRY_CODE],postal_code=user_input[CONF_POSTAL_CODE],station_number=user_input[CONF_STATION_NUMBER],display_name=user_input.get(CONF_DISPLAY_NAME))
   except DHLAuthError: errors["base"]="invalid_auth"
   except DHLNotFoundError: errors["base"]="station_not_found"
   except DHLConnectionError: errors["base"]="cannot_connect"
   except DHLResponseError: errors["base"]="invalid_response"
   except Exception: errors["base"]="unknown"
   else:
    await self.async_set_unique_id(s.location_id); self._abort_if_unique_id_configured(); title=user_input.get(CONF_DISPLAY_NAME) or s.station_name
    return self.async_create_entry(title=title,data={CONF_API_KEY:user_input[CONF_API_KEY],CONF_COUNTRY_CODE:user_input[CONF_COUNTRY_CODE],CONF_POSTAL_CODE:user_input[CONF_POSTAL_CODE],CONF_STATION_NUMBER:user_input[CONF_STATION_NUMBER],CONF_DISPLAY_NAME:title},options={CONF_UPDATE_INTERVAL:DEFAULT_UPDATE_INTERVAL})
  return self.async_show_form(step_id="user",data_schema=vol.Schema({vol.Required(CONF_API_KEY):str,vol.Required(CONF_COUNTRY_CODE,default=DEFAULT_COUNTRY_CODE):str,vol.Required(CONF_POSTAL_CODE):str,vol.Required(CONF_STATION_NUMBER):str,vol.Optional(CONF_DISPLAY_NAME):str}),errors=errors)
 @staticmethod
 @callback
 def async_get_options_flow(entry): return OptionsFlow(entry)
class OptionsFlow(config_entries.OptionsFlow):
 def __init__(self,entry): self.entry=entry
 async def async_step_init(self,user_input=None):
  if user_input is not None:return self.async_create_entry(title="",data=user_input)
  return self.async_show_form(step_id="init",data_schema=vol.Schema({vol.Optional(CONF_DISPLAY_NAME,default=self.entry.options.get(CONF_DISPLAY_NAME,self.entry.data.get(CONF_DISPLAY_NAME,self.entry.title))):str,vol.Required(CONF_UPDATE_INTERVAL,default=self.entry.options.get(CONF_UPDATE_INTERVAL,DEFAULT_UPDATE_INTERVAL)):NumberSelector(NumberSelectorConfig(min=1,max=24,step=1,mode=NumberSelectorMode.BOX,unit_of_measurement="h"))}))

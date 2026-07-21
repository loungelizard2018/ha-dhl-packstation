from homeassistant.helpers.redact import async_redact_data
from .const import DOMAIN,CONF_API_KEY
async def async_get_config_entry_diagnostics(hass,entry):
 c=hass.data[DOMAIN][entry.entry_id]; return {"entry":async_redact_data({"data":dict(entry.data),"options":dict(entry.options)},{CONF_API_KEY}),"station":c.data.raw,"last_update_success":c.last_update_success}

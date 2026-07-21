from datetime import timedelta
import logging

from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import DHLAuthError, DHLError
from .const import (
    CONF_COUNTRY_CODE,
    CONF_DISPLAY_NAME,
    CONF_POSTAL_CODE,
    CONF_STATION_NUMBER,
    CONF_UPDATE_INTERVAL,
    DEFAULT_UPDATE_INTERVAL,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)


class DHLPackstationCoordinator(DataUpdateCoordinator):
    def __init__(self, hass, entry, client):
        self.entry = entry
        self.client = client
        super().__init__(
            hass,
            _LOGGER,
            name=f"{DOMAIN}_{entry.entry_id}",
            update_interval=timedelta(
                hours=int(
                    entry.options.get(
                        CONF_UPDATE_INTERVAL,
                        DEFAULT_UPDATE_INTERVAL,
                    )
                )
            ),
            config_entry=entry,
        )

    async def _async_update_data(self):
        try:
            return await self.client.async_get_station(
                country_code=self.entry.data[CONF_COUNTRY_CODE],
                postal_code=self.entry.data[CONF_POSTAL_CODE],
                station_number=self.entry.data[CONF_STATION_NUMBER],
                display_name=self.entry.options.get(
                    CONF_DISPLAY_NAME,
                    self.entry.data.get(CONF_DISPLAY_NAME),
                ),
            )
        except DHLAuthError as err:
            raise ConfigEntryAuthFailed from err
        except DHLError as err:
            raise UpdateFailed(str(err)) from err

from __future__ import annotations

from datetime import datetime, timedelta
import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.util import dt as dt_util

from .api import DHLPackstationApiClient, DHLAuthError, DHLError, PackstationData
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


class DHLPackstationCoordinator(DataUpdateCoordinator[PackstationData]):
    """Coordinate updates for one configured Packstation."""

    config_entry: ConfigEntry

    def __init__(
        self,
        hass: HomeAssistant,
        entry: ConfigEntry,
        client: DHLPackstationApiClient,
    ) -> None:
        self.entry = entry
        self.client = client
        self.last_successful_update: datetime | None = None

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

    async def _async_update_data(self) -> PackstationData:
        """Fetch the latest forecast data from DHL."""
        try:
            data = await self.client.async_get_station(
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

        self.last_successful_update = dt_util.utcnow()
        return data

from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.selector import (
    NumberSelector,
    NumberSelectorConfig,
    NumberSelectorMode,
)

from .api import (
    DHLPackstationApiClient,
    DHLAuthError,
    DHLConnectionError,
    DHLNotFoundError,
    DHLResponseError,
)
from .const import (
    CONF_API_KEY,
    CONF_COUNTRY_CODE,
    CONF_DISPLAY_NAME,
    CONF_POSTAL_CODE,
    CONF_STATION_NUMBER,
    CONF_UPDATE_INTERVAL,
    DEFAULT_COUNTRY_CODE,
    DEFAULT_UPDATE_INTERVAL,
    DOMAIN,
)


class DHLPackstationConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle setup for DHL Packstation Capacity."""

    VERSION = 1

    async def async_step_user(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> FlowResult:
        errors: dict[str, str] = {}

        if user_input is not None:
            station, error = await self._async_validate(user_input)
            if error:
                errors["base"] = error
            else:
                await self.async_set_unique_id(station.location_id)
                self._abort_if_unique_id_configured()
                title = user_input.get(CONF_DISPLAY_NAME) or station.station_name
                return self.async_create_entry(
                    title=title,
                    data={
                        CONF_API_KEY: user_input[CONF_API_KEY],
                        CONF_COUNTRY_CODE: user_input[CONF_COUNTRY_CODE],
                        CONF_POSTAL_CODE: user_input[CONF_POSTAL_CODE],
                        CONF_STATION_NUMBER: user_input[CONF_STATION_NUMBER],
                        CONF_DISPLAY_NAME: title,
                    },
                    options={CONF_UPDATE_INTERVAL: DEFAULT_UPDATE_INTERVAL},
                )

        return self.async_show_form(
            step_id="user",
            data_schema=self._schema(user_input or {}),
            errors=errors,
        )

    async def _async_validate(
        self,
        values: dict[str, Any],
    ):
        client = DHLPackstationApiClient(
            async_get_clientsession(self.hass),
            values[CONF_API_KEY],
        )
        try:
            station = await client.async_get_station(
                country_code=values[CONF_COUNTRY_CODE],
                postal_code=values[CONF_POSTAL_CODE],
                station_number=values[CONF_STATION_NUMBER],
                display_name=values.get(CONF_DISPLAY_NAME),
            )
        except DHLAuthError:
            return None, "invalid_auth"
        except DHLNotFoundError:
            return None, "station_not_found"
        except DHLConnectionError:
            return None, "cannot_connect"
        except DHLResponseError:
            return None, "invalid_response"
        except Exception:
            return None, "unknown"
        return station, None

    @staticmethod
    def _schema(defaults: dict[str, Any]) -> vol.Schema:
        return vol.Schema(
            {
                vol.Required(
                    CONF_API_KEY,
                    default=defaults.get(CONF_API_KEY, ""),
                ): str,
                vol.Required(
                    CONF_COUNTRY_CODE,
                    default=defaults.get(
                        CONF_COUNTRY_CODE,
                        DEFAULT_COUNTRY_CODE,
                    ),
                ): str,
                vol.Required(
                    CONF_POSTAL_CODE,
                    default=defaults.get(CONF_POSTAL_CODE, ""),
                ): str,
                vol.Required(
                    CONF_STATION_NUMBER,
                    default=defaults.get(CONF_STATION_NUMBER, ""),
                ): str,
                vol.Optional(
                    CONF_DISPLAY_NAME,
                    default=defaults.get(CONF_DISPLAY_NAME, ""),
                ): str,
            }
        )

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> "DHLPackstationOptionsFlow":
        return DHLPackstationOptionsFlow(config_entry)


class DHLPackstationOptionsFlow(config_entries.OptionsFlow):
    """Handle editable Packstation and polling settings."""

    def __init__(self, entry: config_entries.ConfigEntry) -> None:
        self.entry = entry

    async def async_step_init(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> FlowResult:
        errors: dict[str, str] = {}
        current = {**self.entry.data, **self.entry.options}

        if user_input is not None:
            client = DHLPackstationApiClient(
                async_get_clientsession(self.hass),
                user_input[CONF_API_KEY],
            )
            try:
                station = await client.async_get_station(
                    country_code=user_input[CONF_COUNTRY_CODE],
                    postal_code=user_input[CONF_POSTAL_CODE],
                    station_number=user_input[CONF_STATION_NUMBER],
                    display_name=user_input.get(CONF_DISPLAY_NAME),
                )
            except DHLAuthError:
                errors["base"] = "invalid_auth"
            except DHLNotFoundError:
                errors["base"] = "station_not_found"
            except DHLConnectionError:
                errors["base"] = "cannot_connect"
            except DHLResponseError:
                errors["base"] = "invalid_response"
            except Exception:
                errors["base"] = "unknown"
            else:
                title = user_input.get(CONF_DISPLAY_NAME) or station.station_name
                self.hass.config_entries.async_update_entry(
                    self.entry,
                    title=title,
                    data={
                        CONF_API_KEY: user_input[CONF_API_KEY],
                        CONF_COUNTRY_CODE: user_input[CONF_COUNTRY_CODE],
                        CONF_POSTAL_CODE: user_input[CONF_POSTAL_CODE],
                        CONF_STATION_NUMBER: user_input[CONF_STATION_NUMBER],
                        CONF_DISPLAY_NAME: title,
                    },
                )
                return self.async_create_entry(
                    title="",
                    data={
                        CONF_DISPLAY_NAME: title,
                        CONF_UPDATE_INTERVAL: int(
                            user_input[CONF_UPDATE_INTERVAL]
                        ),
                    },
                )

        defaults = user_input or current
        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_API_KEY,
                        default=defaults.get(CONF_API_KEY, ""),
                    ): str,
                    vol.Required(
                        CONF_COUNTRY_CODE,
                        default=defaults.get(
                            CONF_COUNTRY_CODE,
                            DEFAULT_COUNTRY_CODE,
                        ),
                    ): str,
                    vol.Required(
                        CONF_POSTAL_CODE,
                        default=defaults.get(CONF_POSTAL_CODE, ""),
                    ): str,
                    vol.Required(
                        CONF_STATION_NUMBER,
                        default=defaults.get(CONF_STATION_NUMBER, ""),
                    ): str,
                    vol.Optional(
                        CONF_DISPLAY_NAME,
                        default=defaults.get(
                            CONF_DISPLAY_NAME,
                            self.entry.title,
                        ),
                    ): str,
                    vol.Required(
                        CONF_UPDATE_INTERVAL,
                        default=defaults.get(
                            CONF_UPDATE_INTERVAL,
                            DEFAULT_UPDATE_INTERVAL,
                        ),
                    ): NumberSelector(
                        NumberSelectorConfig(
                            min=1,
                            max=24,
                            step=1,
                            mode=NumberSelectorMode.BOX,
                            unit_of_measurement="h",
                        )
                    ),
                }
            ),
            errors=errors,
        )

from __future__ import annotations

import logging
from pathlib import Path

from homeassistant.components.frontend import DATA_EXTRA_MODULE_URL
from homeassistant.components.http import StaticPathConfig
from homeassistant.components.lovelace.const import LOVELACE_DATA
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_ID, CONF_TYPE, CONF_URL
from homeassistant.core import HomeAssistant
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import DHLPackstationApiClient
from .const import CARD_URL, CONF_API_KEY, DOMAIN, PLATFORMS, STATIC_URL
from .coordinator import DHLPackstationCoordinator

_LOGGER = logging.getLogger(__name__)
_CARD_RESOURCE_URL = f"{CARD_URL}?v=1.0.1"

CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)


def _resource_base_url(url: str) -> str:
    """Return a resource URL without any cache-busting query string."""
    return url.partition("?")[0]


async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    """Register the static files used by the bundled Lovelace card."""
    await hass.http.async_register_static_paths(
        [
            StaticPathConfig(
                STATIC_URL,
                str(Path(__file__).parent / "frontend"),
                False,
            )
        ]
    )
    hass.data.setdefault(DOMAIN, {})
    return True


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
) -> bool:
    """Set up one configured DHL Packstation."""
    await _async_register_card(hass)

    coordinator = DHLPackstationCoordinator(
        hass,
        entry,
        DHLPackstationApiClient(
            async_get_clientsession(hass),
            entry.data[CONF_API_KEY],
        ),
    )
    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(_async_reload_entry))
    return True


async def async_unload_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
) -> bool:
    """Unload a configured Packstation."""
    unloaded = await hass.config_entries.async_unload_platforms(
        entry,
        PLATFORMS,
    )
    if unloaded:
        hass.data[DOMAIN].pop(entry.entry_id, None)
    return unloaded


async def _async_register_card(hass: HomeAssistant) -> None:
    """Register exactly one current Lovelace resource for the bundled card."""
    module_urls = hass.data.get(DATA_EXTRA_MODULE_URL)
    if module_urls is not None:
        stale_module_urls = {
            url
            for url in module_urls.urls
            if _resource_base_url(str(url)) == CARD_URL
            and str(url) != _CARD_RESOURCE_URL
        }
        for stale_url in stale_module_urls:
            module_urls.remove(stale_url)
        if _CARD_RESOURCE_URL not in module_urls.urls:
            module_urls.add(_CARD_RESOURCE_URL)

    lovelace_data = hass.data.get(LOVELACE_DATA)
    if lovelace_data is None:
        _LOGGER.warning(
            "Lovelace is not loaded; add %s as a JavaScript module resource",
            _CARD_RESOURCE_URL,
        )
        return

    resources = lovelace_data.resources
    if not hasattr(resources, "async_create_item"):
        return

    await resources.async_get_info()
    items = resources.async_items() or []
    matching = [
        item
        for item in items
        if _resource_base_url(str(item.get(CONF_URL, ""))) == CARD_URL
    ]

    if not matching:
        await resources.async_create_item(
            {
                "res_type": "module",
                CONF_URL: _CARD_RESOURCE_URL,
            }
        )
        _LOGGER.info("Registered DHL Packstation Lovelace card resource")
        return

    primary = matching[0]
    primary_id = primary.get(CONF_ID)
    if (
        primary_id
        and primary.get(CONF_URL) != _CARD_RESOURCE_URL
        and hasattr(resources, "async_update_item")
    ):
        await resources.async_update_item(
            primary_id,
            {
                "res_type": primary.get(CONF_TYPE, "module"),
                CONF_URL: _CARD_RESOURCE_URL,
            },
        )
        _LOGGER.info("Updated DHL Packstation Lovelace card resource")

    if hasattr(resources, "async_delete_item"):
        for duplicate in matching[1:]:
            duplicate_id = duplicate.get(CONF_ID)
            if duplicate_id:
                await resources.async_delete_item(duplicate_id)
                _LOGGER.info(
                    "Removed duplicate DHL Packstation Lovelace resource %s",
                    duplicate.get(CONF_URL),
                )


async def _async_reload_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
) -> None:
    """Reload an entry when its options change."""
    await hass.config_entries.async_reload(entry.entry_id)

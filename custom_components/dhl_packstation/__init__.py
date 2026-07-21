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
_CARD_RESOURCE_URL = f"{CARD_URL}?v=0.1.4"

CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)


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
    """Load the bundled card and add it to storage-mode resources."""
    module_urls = hass.data.get(DATA_EXTRA_MODULE_URL)
    if module_urls is not None:
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
    existing = next(
        (
            item
            for item in items
            if str(item.get(CONF_URL, "")).split("?", 1)[0] == CARD_URL
        ),
        None,
    )

    if existing is None:
        await resources.async_create_item(
            {
                "res_type": "module",
                CONF_URL: _CARD_RESOURCE_URL,
            }
        )
        _LOGGER.info("Registered DHL Packstation Lovelace card resource")
        return

    if (
        existing.get(CONF_URL) != _CARD_RESOURCE_URL
        and existing.get(CONF_ID)
        and hasattr(resources, "async_update_item")
    ):
        await resources.async_update_item(
            existing[CONF_ID],
            {
                "res_type": existing.get(CONF_TYPE, "module"),
                CONF_URL: _CARD_RESOURCE_URL,
            },
        )
        _LOGGER.info("Updated DHL Packstation Lovelace card resource")


async def _async_reload_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
) -> None:
    """Reload an entry when its options change."""
    await hass.config_entries.async_reload(entry.entry_id)

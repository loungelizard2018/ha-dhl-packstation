from datetime import timedelta

DOMAIN = "dhl_packstation"
PLATFORMS = ["sensor", "button"]

CONF_API_KEY = "api_key"
CONF_COUNTRY_CODE = "country_code"
CONF_POSTAL_CODE = "postal_code"
CONF_STATION_NUMBER = "station_number"
CONF_DISPLAY_NAME = "display_name"
CONF_UPDATE_INTERVAL = "update_interval"

DEFAULT_COUNTRY_CODE = "DE"
DEFAULT_UPDATE_INTERVAL = 6

API_BASE_URL = "https://api.dhl.com"
API_PATH = "/location-finder/v1/find-by-keyword-id"

STATIC_URL = "/dhl_packstation_static"
CARD_URL = f"{STATIC_URL}/dhl-packstation-card.js?v=0.1.5"

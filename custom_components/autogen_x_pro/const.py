"""Constants for the AutoGen X Pro integration."""

from typing import Final

DOMAIN: Final = "autogen_x_pro"
NAME: Final = "AutoGen X Pro"

CONF_TOKEN: Final = "token"
CONF_PAIRING_CODE: Final = "pairing_code"
CONF_DEVICE_ID: Final = "device_id"
DEFAULT_PORT: Final = 32100

API_INFO_PATH: Final = "/api/v1/info"
API_PAIR_PATH: Final = "/api/v1/pair"
API_STATUS_PATH: Final = "/api/v1/status"
API_COMMAND_PATH: Final = "/api/v1/command"
API_SETTINGS_PATH: Final = "/api/v1/settings"

PLATFORMS: Final = ["sensor", "binary_sensor", "switch", "button", "number", "time"]

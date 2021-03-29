"""
PRCustomComponent for Home Assistant.

SPDX-License-Identifier: Apache-2.0

Constants Platform

For more details about this integration, please refer to
https://github.com/alandtse/pr_custom_component
"""

# Base component constants
NAME = "pr_custom_component"
DOMAIN = "pr_custom_component"
HACS_DOMAIN = "hacs"
DOMAIN_DATA = f"{DOMAIN}_data"
VERSION = "0.1.4"
ISSUE_URL = "https://github.com/alandtse/pr_custom_component/issues"

# GitHub constants
PATCH_DOMAIN = "patch-diff.githubusercontent.com"
PATCH_PATH_PREFIX = "raw"
PATCH_PATH_SUFFIX = ".patch"
API_DOMAIN = "api.github.com"
API_PATH_PREFIX = "repos"

# HA Constants
COMPONENT_PATH = "homeassistant/components/"
CUSTOM_COMPONENT_PATH = "custom_components/"
TRANSLATIONS_PATH = "translations/"
STRING_FILE = "strings.json"
ENGLISH_JSON = "en.json"

# Icons
ICON = "mdi:update"

# Device classes
BINARY_SENSOR_DEVICE_CLASS = "power"
SENSOR_DEVICE_CLASS = "timestamp"

# Platforms
BINARY_SENSOR = "binary_sensor"
SENSOR = "sensor"
SWITCH = "switch"
PLATFORMS = [BINARY_SENSOR, SENSOR, SWITCH]


# Configuration and options
CONF_ENABLED = "enabled"
CONF_PR_URL = "pr_url"

# Defaults
DEFAULT_NAME = DOMAIN


STARTUP_MESSAGE = f"""
-------------------------------------------------------------------
{NAME}
Version: {VERSION}
This is a custom integration!
If you have any issues with this you need to open an issue here:
{ISSUE_URL}
-------------------------------------------------------------------
"""

EXCEPTION_TEMPLATE = "An exception of type {0} occurred. Arguments:\n{1!r}"

"""
PRCustomComponent for Home Assistant.

SPDX-License-Identifier: Apache-2.0

Exceptions

For more details about this integration, please refer to
https://github.com/alandtse/pr_custom_component
"""
import logging
from typing import Any, Dict, Text

_LOGGER = logging.getLogger(__name__)


class PRCustomComponentException(Exception):
    """Class of PR Custom Component exceptions."""

    pass


class RateLimitException(PRCustomComponentException):
    """Class of exceptions for hitting retry limits."""

    pass

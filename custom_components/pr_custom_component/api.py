"""
PRCustomComponent for Home Assistant.

SPDX-License-Identifier: Apache-2.0

GitHub API

For more details about this integration, please refer to
https://github.com/alandtse/pr_custom_component
"""
import asyncio
import base64
import json
from json.decoder import JSONDecodeError
import logging
import os
import shutil
import socket
from typing import Dict, List, Union

import aiofiles
import aiohttp
import async_timeout
import yarl

from .const import (
    API_DOMAIN,
    API_PATH_PREFIX,
    COMPONENT_PATH,
    CUSTOM_COMPONENT_PATH,
    ENGLISH_JSON,
    EXCEPTION_TEMPLATE,
    PATCH_DOMAIN,
    PATCH_PATH_PREFIX,
    PATCH_PATH_SUFFIX,
    STRING_FILE,
    TRANSLATIONS_PATH,
)
from .exceptions import RateLimitException

TIMEOUT = 10


_LOGGER: logging.Logger = logging.getLogger(__package__)

HEADERS = {"Content-type": "application/json; charset=UTF-8"}


class PRCustomComponentApiClient:
    """Api Client."""

    def __init__(
        self,
        session: aiohttp.ClientSession,
        pull_url: yarl.URL,
        config_path: str = "/config",
    ) -> None:
        """Initialize API client.

        Args:
            session (aiohttp.ClientSession): Websession to use
            pull_url (yarl.URL): URL of pull request, e.g.,
                https://github.com/home-assistant/core/pull/46558
            config_path (str): base path for config, e.g., /config

        """
        self._pull_url: yarl.URL = pull_url
        self._session: aiohttp.ClientSession = session
        self._config_path: str = config_path
        self._manifest: Dict[str, Union[str, List[str]]] = {}
        self._component_name: str = ""
        self._updated_at: str = ""
        self._base_path: str = ""
        self._update_available: str = ""
        self._token: str = ""
        self._headers: Dict[str, str] = {}
        self._auto_update: bool = False
        self._pull_number: int = 0

    @property
    def name(self) -> str:
        """Return the component name."""
        return self._component_name

    @property
    def pull_number(self) -> int:
        """Return the pull number."""
        return self._pull_number

    @property
    def updated_at(self) -> str:
        """Return the last updated time."""
        return self._updated_at

    @updated_at.setter
    def updated_at(self, value: str) -> None:
        """Set the last updated time."""
        self._updated_at = value

    @property
    def update_available(self) -> str:
        """Return the whether an update is available."""
        return self._update_available

    @property
    def auto_update(self) -> bool:
        """Return the whether an to autoupdate when available."""
        return self._auto_update

    def set_token(self, token: str = "") -> None:
        """Set auth token for GitHub to avoid rate limits.

        Args:
            token (str, optional): Authentication token from GitHub. Defaults to "".
        """
        if token:
            self._token = token
            self._headers["Authorization"] = f"token {self._token}"

    async def async_update_data(self, download: bool = False) -> dict:
        """Update custom component."""
        pull_json = await self.async_get_pull_data()
        if not pull_json or pull_json.get("message") == "Not Found":
            _LOGGER.debug("No pull data found")
            return {}
        component_name: str = ""
        for label in pull_json["labels"]:
            if label["name"].startswith("integration: "):
                component_name = label["name"].replace("integration: ", "")
                break
        if not component_name:
            _LOGGER.error("Unable to find integration in pull request")
            return {}
        else:
            _LOGGER.debug("Found %s integration", component_name)
        branch: str = pull_json["head"]["ref"]
        pull_number: int = pull_json["number"]
        user: str = pull_json["head"]["user"]["login"]
        path: str = f"{COMPONENT_PATH}{component_name}"
        contents_url: str = pull_json["head"]["repo"]["contents_url"]
        url: yarl.URL = yarl.URL(contents_url.replace("{+path}", path)).with_query(
            {"ref": branch}
        )
        self._base_path = path
        self._pull_number = pull_number
        self._update_available = self._updated_at != pull_json["updated_at"]
        self._updated_at = pull_json["updated_at"]
        self._manifest = {
            "name": f"Custom {component_name.capitalize()} PR#{pull_number}",
            "issue_tracker": str(self._pull_url),
            "codeowners": [f"@{user}"],
            "version": self._updated_at.replace("-", "."),
        }
        self._component_name = component_name
        component_path: str = os.path.join(
            self._config_path, CUSTOM_COMPONENT_PATH, self._component_name
        )
        if not os.path.isdir(component_path):
            _LOGGER.debug("%s not detected in config directory", self._component_name)
        if download or not os.path.isdir(component_path):
            if await self.async_download(
                str(url),
                component_path,
            ):
                self._update_available = ""
        return pull_json

    async def async_get_pull_data(self) -> dict:
        """Get pull data from the API.

        e.g., https://api.github.com/repos/home-assistant/core/pulls/46558
        """
        url = self._pull_url.with_path(
            API_PATH_PREFIX + self._pull_url.path.replace("pull", "pulls")
        ).with_host(API_DOMAIN)
        return await self.api_wrapper("get", url)

    async def async_get_patch_data(self) -> dict:
        """Get data from the API."""
        url = self._pull_url.with_path(
            PATCH_PATH_PREFIX + self._pull_url.path + PATCH_PATH_SUFFIX
        ).with_host(PATCH_DOMAIN)
        return await self.api_wrapper("get", url)

    async def async_download(self, url: str, path: str) -> bool:
        """Download and save files to path.

        Args:
            url (yarl.URL): Remote path to download
            path (str): Local path to save to

        Returns:
            bool: Whether saved successful
        """
        if not path:
            _LOGGER.debug("Path not specified")
            return False
        _LOGGER.debug("Downloading url %s to %s", url, path)
        result = await self.api_wrapper("get", url)
        if not result or (
            isinstance(result, dict) and result.get("message") == "Not Found"
        ):
            return False
        if not result:
            _LOGGER.debug("%s is empty", url)
            return True
        if isinstance(result, list):
            if os.path.isfile(path):
                _LOGGER.error("Trying to save directory into an existing file %s", path)
                return False
            if not os.path.isdir(path):
                _LOGGER.debug("Creating new directory %s", path)
                os.mkdir(path)
            _LOGGER.debug("Processing directory")
            tasks = []
            for file_json in result:
                file_path: str = os.path.join(path, file_json["name"])
                if file_json["type"] == "dir" and not os.path.isdir(file_path):
                    _LOGGER.debug("Creating new sub directory %s", file_path)
                    os.mkdir(file_path)
                tasks.append(self.async_download(file_json["url"], path))
            await asyncio.gather(*tasks)
            await self.async_create_translations()
            return True
        if isinstance(result, dict):
            path.split(os.sep)
            file_name: str = result["name"]
            file_path = result["path"].replace(self._base_path, "")
            full_path: str = os.path.join(path, file_path.lstrip(os.sep))
            contents = base64.b64decode(result["content"].encode("utf-8"))
            _LOGGER.debug("Saving %s size: %s KB", full_path, result["size"] / 1000)
            if file_name == "manifest.json":
                manifest = json.loads(contents)
                manifest.update(self._manifest)
                contents = json.dumps(manifest).encode("utf-8")
            try:
                async with aiofiles.open(full_path, mode="wb") as localfile:
                    await localfile.write(contents)
            except (OSError, EOFError, TypeError, AttributeError) as ex:
                _LOGGER.debug(
                    "Error saving file %s: %s",
                    full_path,
                    EXCEPTION_TEMPLATE.format(type(ex).__name__, ex.args),
                )
                return False
            return True
        return False

    async def async_create_translations(self) -> bool:
        """Create translations directory if needed.

        Returns:
            bool: Whether translations directory exists
        """
        if not self._config_path:
            _LOGGER.debug("Config path not initialized")
            return False
        if not self._component_name:
            _LOGGER.debug("Component name not initialized")
            return False
        component_path: str = os.path.join(
            self._config_path, CUSTOM_COMPONENT_PATH, self._component_name
        )
        translations_path = os.path.join(component_path, TRANSLATIONS_PATH)
        strings_path = os.path.join(component_path, STRING_FILE)
        english_path = os.path.join(translations_path, ENGLISH_JSON)
        _LOGGER.debug("Checking for translations in %s", component_path)
        if os.path.isdir(translations_path) and os.path.isfile(english_path):
            _LOGGER.debug("Translations directory and en.json already exists")
            return True
        if not os.path.isfile(strings_path):
            _LOGGER.debug(
                "%s does not exist, not able to create translations directory",
                strings_path,
            )
            return False
        else:
            if not os.path.isdir(translations_path):
                _LOGGER.debug("Creating translations directory %s", translations_path)
                try:
                    os.mkdir(translations_path)
                except (OSError) as ex:
                    _LOGGER.debug(
                        "Error creating directory %s",
                        translations_path,
                        EXCEPTION_TEMPLATE.format(type(ex).__name__, ex.args),
                    )
                    return False
            try:
                async with aiofiles.open(strings_path) as localfile:
                    contents = await localfile.read()
                    strings_json: str = json.loads(contents)
            except (OSError, EOFError, JSONDecodeError, TypeError) as ex:
                _LOGGER.debug(
                    "Error reading file %s: %s",
                    strings_path,
                    EXCEPTION_TEMPLATE.format(type(ex).__name__, ex.args),
                )
                return False
            if strings_json.get("title") and self._manifest.get("name"):
                strings_json["title"] = self._manifest["name"]
            contents = json.dumps(strings_json).encode("utf-8")
            try:
                async with aiofiles.open(english_path, mode="wb") as localfile:
                    await localfile.write(contents)
            except (OSError) as ex:
                _LOGGER.debug(
                    "Error saving file %s: %s",
                    english_path,
                    EXCEPTION_TEMPLATE.format(type(ex).__name__, ex.args),
                )
                return False
        return True

    async def api_wrapper(
        self,
        method: str,
        url: Union[str, yarl.URL],
        data: dict = None,
        headers: dict = None,
    ) -> dict:
        """Get information from the API."""
        headers = headers or {}
        headers = self._headers if not headers else headers
        data = data or {}
        try:
            async with async_timeout.timeout(TIMEOUT, loop=asyncio.get_event_loop()):
                if method == "get":
                    response = await self._session.get(url, headers=headers)
                    response_json = await response.json()
                    if (
                        response_json
                        and isinstance(response_json, dict)
                        and response_json.get("message")
                        and response_json["message"].startswith(
                            "API rate limit exceeded"
                        )
                    ):
                        _LOGGER.error("Rate limited: %s", response_json["message"])
                        raise RateLimitException("Rate limited")
                    return response_json
                if method == "put":
                    return await (
                        await self._session.put(url, headers=headers, json=data)
                    ).json()

                if method == "patch":
                    return await (
                        await self._session.patch(url, headers=headers, json=data)
                    ).json()

                if method == "post":
                    return await (
                        await self._session.post(url, headers=headers, json=data)
                    ).json()

        except asyncio.TimeoutError as exception:
            _LOGGER.error(
                "Timeout error fetching information from %s - %s",
                url,
                exception,
            )
        except (KeyError, TypeError) as exception:
            _LOGGER.error(
                "Error parsing information from %s - %s",
                url,
                exception,
            )
        except (aiohttp.ClientError, socket.gaierror) as exception:
            _LOGGER.error(
                "Error fetching information from %s - %s",
                url,
                exception,
            )
        except RateLimitException as exception:
            raise exception
        except Exception as exception:  # pylint: disable=broad-except
            _LOGGER.error("Something really wrong happened! - %s", exception)
        return {}

    async def async_delete(self) -> bool:
        """Delete files from config path.

        Args:
            path (str): Delete component files.

        Returns:
            bool: Whether delete is successful.
        """
        component_path: str = os.path.join(
            self._config_path, CUSTOM_COMPONENT_PATH, self._component_name
        )
        if not self._component_name or component_path == os.path.join(
            self._config_path, CUSTOM_COMPONENT_PATH
        ):
            _LOGGER.warning("Component name was empty while delete was called.")
            return False
        if os.path.isdir(component_path):
            _LOGGER.debug("Deleting %s", component_path)
            try:
                shutil.rmtree(component_path)
            except (OSError, EOFError, TypeError, AttributeError) as ex:
                _LOGGER.debug(
                    "Error deleting component: %s %s; please manually remove",
                    component_path,
                    EXCEPTION_TEMPLATE.format(type(ex).__name__, ex.args),
                )
                return False
        return True

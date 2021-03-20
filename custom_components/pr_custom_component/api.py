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
import logging
import os
import shutil
import socket
from typing import Dict, Text, Union, List

import aiofiles
import aiohttp
import async_timeout
import yarl

from .const import (
    API_DOMAIN,
    API_PATH_PREFIX,
    COMPONENT_PATH,
    CUSTOM_COMPONENT_PATH,
    EXCEPTION_TEMPLATE,
    PATCH_DOMAIN,
    PATCH_PATH_PREFIX,
    PATCH_PATH_SUFFIX,
)
from .exceptions import RateLimitException

TIMEOUT = 10


_LOGGER: logging.Logger = logging.getLogger(__package__)

HEADERS = {"Content-type": "application/json; charset=UTF-8"}


class PRCustomComponentApiClient:
    def __init__(
        self,
        session: aiohttp.ClientSession,
        pull_url: yarl.URL,
        config_path: Text = "/config",
    ) -> None:
        """Initialize API client.

        Args:
            session (aiohttp.ClientSession): Websession to use
            pull_url (yarl.URL): URL of pull request, e.g., https://github.com/home-assistant/core/pull/46558
            config_path (Text): base path for config, e.g., /config

        """
        self._pull_url: yarl.URL = pull_url
        self._session: aiohttp.ClientSession = session
        self._config_path: Text = config_path
        self._manifest: Dict[Text, Union[Text, List[Text]]] = {}
        self._component_name: Text = ""
        self._updated_at: Text = ""
        self._base_path: Text = ""
        self._update_available: Text = ""
        self._token: Text = ""
        self._headers: Dict[Text, Text] = {}
        self._auto_update: bool = False
        self._pull_number: int = 0

    @property
    def name(self) -> Text:
        """Return the component name."""
        return self._component_name

    @property
    def pull_number(self) -> int:
        """Return the pull number."""
        return self._pull_number

    @property
    def updated_at(self) -> Text:
        """Return the last updated time."""
        return self._updated_at

    @updated_at.setter
    def updated_at(self, value: Text) -> None:
        """Set the last updated time."""
        self._updated_at = value

    @property
    def update_available(self) -> Text:
        """Return the whether an update is available."""
        return self._update_available

    @property
    def auto_update(self) -> bool:
        """Return the whether an to autoupdate when available."""
        return self._auto_update

    def set_token(self, token: Text = "") -> None:
        """Set auth token for GitHub to avoid rate limits.

        Args:
            token (Text, optional): Authentication token from GitHub. Defaults to "".
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
        component_name: Text = ""
        for label in pull_json["labels"]:
            if label["name"].startswith("integration: "):
                component_name = label["name"].replace("integration: ", "")
                break
        if not component_name:
            _LOGGER.error("Unable to find integration in pull request")
        else:
            _LOGGER.debug("Found %s integration", component_name)
        branch: Text = pull_json["head"]["ref"]
        pull_number: int = pull_json["number"]
        user: Text = pull_json["head"]["user"]["login"]
        path: Text = f"{COMPONENT_PATH}{component_name}"
        contents_url: Text = pull_json["head"]["repo"]["contents_url"]
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
        }
        self._component_name = component_name
        component_path: Text = os.path.join(
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

    async def async_download(self, url: Text, path: Text) -> bool:
        """Download and save files to path.

        Args:
            url (yarl.URL): Remote path to download
            path (Text): Local path to save to

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
        # [
        # {
        #     "name": "__init__.py",
        #     "path": "homeassistant/components/tesla/__init__.py",
        #     "sha": "9e6db33d24ab50c1af1e1e2818580cc96069e076",
        #     "size": 9220,
        #     "url": "https://api.github.com/repos/alandtse/home-assistant/contents/homeassistant/components/tesla/__init__.py?ref=tesla_oauth_callback",
        #     "html_url": "https://github.com/alandtse/home-assistant/blob/tesla_oauth_callback/homeassistant/components/tesla/__init__.py",
        #     "git_url": "https://api.github.com/repos/alandtse/home-assistant/git/blobs/9e6db33d24ab50c1af1e1e2818580cc96069e076",
        #     "download_url": "https://raw.githubusercontent.com/alandtse/home-assistant/tesla_oauth_callback/homeassistant/components/tesla/__init__.py",
        #     "type": "file",
        #     "content": "IiIiU3V<SNIP>\n",
        #     "encoding": "base64",
        #     "_links": {
        #         "self": "https://api.github.com/repos/alandtse/home-assistant/contents/homeassistant/components/tesla/__init__.py?ref=tesla_oauth_callback",
        #         "git": "https://api.github.com/repos/alandtse/home-assistant/git/blobs/9e6db33d24ab50c1af1e1e2818580cc96069e076",
        #         "html": "https://github.com/alandtse/home-assistant/blob/tesla_oauth_callback/homeassistant/components/tesla/__init__.py"
        #     }
        # }
        # ]
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
                file_path: Text = os.path.join(path, file_json["name"])
                if file_json["type"] == "dir" and not os.path.isdir(file_path):
                    _LOGGER.debug("Creating new sub directory %s", file_path)
                    os.mkdir(file_path)
                tasks.append(self.async_download(file_json["url"], path))
            await asyncio.gather(*tasks)
            return True
        if isinstance(result, dict):
            path.split(os.sep)
            file_name: Text = result["name"]
            file_path = result["path"].replace(self._base_path, "")
            full_path: Text = os.path.join(path, file_path.lstrip(os.sep))
            # if len(file_path.split(os.sep)) > 1:
            #     directory = file_path.split(os.sep)[0]
            #     directory_path = os.path.join(path, directory.lstrip(os.sep))
            #     if not os.path.isdir(directory_path):
            #         _LOGGER.debug("Creating new directory %s", directory_path)
            #         os.mkdir(directory_path)
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

    async def api_wrapper(
        self,
        method: str,
        url: Union[str, yarl.URL],
        data: dict = {},
        headers: dict = {},
    ) -> dict:
        """Get information from the API."""
        headers = self._headers if not headers else headers
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
                elif method == "put":
                    return await (
                        await self._session.put(url, headers=headers, json=data)
                    ).json()

                elif method == "patch":
                    return await (
                        await self._session.patch(url, headers=headers, json=data)
                    ).json()

                elif method == "post":
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
            path (Text): Delete component files.

        Returns:
            bool: Whether delete is successful.
        """
        component_path: Text = os.path.join(
            self._config_path, CUSTOM_COMPONENT_PATH, self._component_name
        )
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

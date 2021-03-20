"""Tests for PRCustomComponent api."""
import asyncio

import aiohttp
from homeassistant.helpers.aiohttp_client import async_get_clientsession
import yarl
from custom_components.pr_custom_component import PRCustomComponentApiClient

from .const import (
    MOCK_PR_RESPONSE,
    TEST_CONFIG_PATH,
    TEST_PR_URL,
    TEST_API_PR_URL,
    TEST_API_DATA_URL,
    TEST_INIT_URL,
    TEST_TRANSLATIONS_URL,
    MOCK_INIT_RESPONSE,
    MOCK_TRANSLATIONS_RESPONSE,
)


async def test_api(hass, aioclient_mock, caplog):
    """Test API calls."""

    # To test the api submodule, we first create an instance of our API client
    api = PRCustomComponentApiClient(
        async_get_clientsession(hass),
        yarl.URL(TEST_PR_URL),
        TEST_CONFIG_PATH,
    )

    # Use aioclient_mock which is provided by `pytest_homeassistant_custom_components`
    # to mock responses to aiohttp requests. In this case we are telling the mock to
    # return {"test": "test"} when a `GET` call is made to the specified URL. We then
    # call `async_update_data` which will make that `GET` request.
    aioclient_mock.get(TEST_API_PR_URL, json=MOCK_PR_RESPONSE)
    aioclient_mock.get(TEST_INIT_URL, json=MOCK_INIT_RESPONSE)
    aioclient_mock.get(TEST_TRANSLATIONS_URL, json=MOCK_TRANSLATIONS_RESPONSE)

    assert await api.async_update_data() == MOCK_PR_RESPONSE

    # In order to get 100% coverage, we need to test `api_wrapper` to test the code
    # that isn't already called by `async_update_data` Because the
    # only logic that lives inside `api_wrapper` that is not being handled by a third
    # party library (aiohttp) is the exception handling, we also want to simulate
    # raising the exceptions to ensure that the function handles them as expected.
    # The caplog fixture allows access to log messages in tests. This is particularly
    # useful during exception handling testing since often the only action as part of
    # exception handling is a logging statement
    caplog.clear()
    aioclient_mock.put(TEST_API_PR_URL, exc=asyncio.TimeoutError)
    assert await api.api_wrapper("put", TEST_API_PR_URL) is None
    assert (
        len(caplog.record_tuples) == 1
        and "Timeout error fetching information from" in caplog.record_tuples[0][2]
    )

    caplog.clear()
    aioclient_mock.post(TEST_API_PR_URL, exc=aiohttp.ClientError)
    assert await api.api_wrapper("post", TEST_API_PR_URL) is None
    assert (
        len(caplog.record_tuples) == 1
        and "Error fetching information from" in caplog.record_tuples[0][2]
    )

    caplog.clear()
    aioclient_mock.post(TEST_API_PR_URL, exc=Exception)
    assert await api.api_wrapper("post", TEST_API_PR_URL) is None
    assert (
        len(caplog.record_tuples) == 1
        and "Something really wrong happened!" in caplog.record_tuples[0][2]
    )

    caplog.clear()
    aioclient_mock.post(TEST_API_PR_URL, exc=TypeError)
    assert await api.api_wrapper("post", TEST_API_PR_URL) is None
    assert (
        len(caplog.record_tuples) == 1
        and "Error parsing information from" in caplog.record_tuples[0][2]
    )

"""Conftest for DSMS-SDK"""
import json
from typing import TYPE_CHECKING
from urllib.parse import urljoin

import pytest
import responses

if TYPE_CHECKING:
    from typing import Any, Dict


class MockDB:
    """Mock database"""

    kitems = {
        "78dfd0c7-0348-412c-8eb6-c91a4d340477": {
            "name": "foo123",
            "id": "78dfd0c7-0348-412c-8eb6-c91a4d340477",
        },
        "82c7a5a8-0983-4830-8fcf-5c8d167a928b": {
            "name": "foo456",
            "id": "82c7a5a8-0983-4830-8fcf-5c8d167a928b",
        },
        "a00af336-e714-499a-9dbf-298651939e62": {
            "name": "foo789",
            "id": "a00af336-e714-499a-9dbf-298651939e62",
        },
        "698acdc5-dd97-4217-906e-2c0b44248c17": {
            "name": "bar123",
            "id": "698acdc5-dd97-4217-906e-2c0b44248c17",
        },
    }

    hdf5 = {
        "698acdc5-dd97-4217-906e-2c0b44248c17": [
            {
                "column_id": 0,
                "name": "bar123column",
            },
        ]
    }


@pytest.fixture(scope="function")
def custom_address(request) -> str:
    try:
        url = getattr(request, "param")
    except Exception:
        url = "https://www.example.org/"
    return url


@pytest.fixture(scope="function")
def mock_responses(custom_address) -> "Dict[str, Any]":
    kitems = urljoin(custom_address, "api/knowledge/kitems")
    ping = urljoin(custom_address, "api/knowledge/docs")

    return {
        ping: [
            {"method": responses.GET, "returns": {"status": 200, "json": {}}}
        ],
        kitems: [
            {"method": responses.GET, "returns": {"status": 200, "json": {}}}
        ],
    }


@pytest.fixture(scope="function")
def mock_callbacks(custom_address) -> "Dict[str, Any]":
    ktypes = urljoin(custom_address, "api/knowledge-type/")

    def return_ktypes(request):
        ktypes = [
            {
                "name": "organization",
                "id": "organization",
                "data_schema": {
                    "title": "Organization",
                    "type": "object",
                    "properties": {},
                },
            },
        ]
        header = {"content_type": "application/json"}
        return (200, header, json.dumps(ktypes))

    def return_kitems(request):
        # Extract 'id' parameter from the URL
        url_parts = request.url.split("/")
        item_id = url_parts[-1]

        # Your logic to generate a dynamic response based on 'item_id'
        # This is just a placeholder; you should replace it with your actual logic
        if item_id not in MockDB.kitems:
            return 404, {}, "KItem does not exist"
        else:
            return 200, {}, json.dumps(MockDB.kitems[item_id])

    def return_hdf5(request):
        # Extract 'id' parameter from the URL
        url_parts = request.url.split("/")
        item_id = url_parts[-1]

        # Your logic to generate a dynamic response based on 'item_id'
        # This is just a placeholder; you should replace it with your actual logic
        if item_id not in MockDB.hdf5:
            return 404, {}, "KItem does not exist"
        else:
            return 200, {}, json.dumps(MockDB.hdf5[item_id])

    def _get_kitems() -> "Dict[str, Any]":
        return {
            urljoin(custom_address, f"api/knowledge/kitems/{uid}"): [
                {
                    "method": responses.GET,
                    "returns": {
                        "content_type": "application/json",
                        "callback": return_kitems,
                    },
                }
            ]
            for uid in MockDB.kitems
        }

    def _get_hdf5() -> "Dict[str, Any]":
        return {
            urljoin(custom_address, f"api/knowledge/data_api/{uid}"): [
                {
                    "method": responses.GET,
                    "returns": {
                        "content_type": "application/json",
                        "callback": return_hdf5,
                    },
                }
            ]
            for uid in MockDB.kitems
        }

    return {
        ktypes: [
            {
                "method": responses.GET,
                "returns": {
                    "content_type": "application/json",
                    "callback": return_ktypes,
                },
            }
        ],
        **_get_kitems(),
        **_get_hdf5(),
    }


@pytest.fixture(autouse=True, scope="function")
def register_mocks(mock_responses, mock_callbacks, custom_address) -> str:
    for url, endpoints in mock_responses.items():
        for response in endpoints:
            responses.add(
                response["method"],
                url,
                **response["returns"],
            )
    for url, endpoints in mock_callbacks.items():
        for response in endpoints:
            responses.add_callback(
                response["method"],
                url,
                **response["returns"],
            )
    return custom_address


@pytest.fixture(autouse=True, scope="function")
def reset_dsms_context():
    from dsms.core.context import Context

    Context.dsms = None


@pytest.fixture(scope="function")
def get_mock_kitem_ids():
    return list(MockDB.kitems.keys())

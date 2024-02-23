"""KItem Apps utils"""

from typing import TYPE_CHECKING

from dsms.apps.apps import App
from dsms.core.utils import _perform_request

if TYPE_CHECKING:
    from typing import List


def _get_available_apps() -> "List[App]":
    """Get available KItem app."""
    response = _perform_request("api/knowledge/apps", "get")
    if not response.ok:
        message = f"""Something went wrong fetching the available app
        list in the DSMS: {response.text}"""
        raise RuntimeError(message)
    return [App(**app) for app in response.json()]

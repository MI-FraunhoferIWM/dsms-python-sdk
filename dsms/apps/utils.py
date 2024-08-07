"""KItem Apps utils"""

import urllib.parse
from typing import TYPE_CHECKING

from dsms.core.utils import _perform_request

if TYPE_CHECKING:
    from typing import Any, Dict, List


def _get_available_apps() -> "List[Dict[str, Any]]":
    """Get available KItem app."""
    response = _perform_request("api/knowledge/apps", "get")
    if not response.ok:
        message = f"""Something went wrong fetching the available app
        list in the DSMS: {response.text}"""
        raise RuntimeError(message)
    return response.json()


def _get_app_specification(appname) -> str:
    safe_filename = urllib.parse.quote_plus(appname)
    response = _perform_request(
        f"knowledge/api/apps/{safe_filename}",
        "get",
    )
    if not response.ok:
        message = f"Something went wrong downloading app `{appname}`: {response.text}"
        raise RuntimeError(message)
    return response.text

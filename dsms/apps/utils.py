"""KItem Apps utils"""

from typing import TYPE_CHECKING

from dsms.core.utils import _perform_request

if TYPE_CHECKING:
    from typing import Any, Dict, List


def _get_available_apps_specs() -> "List[Dict[str, Any]]":
    """Get available KItem app specs."""
    response = _perform_request("api/knowledge/apps/argo/list", "get")
    if not response.ok:
        message = f"""Something went wrong fetching the available app configs
        list in the DSMS: {response.text}"""
        raise RuntimeError(message)
    return response.json()


def _app_spec_exists(name: str) -> bool:
    """Check whether the specification of the app already exists."""
    response = _perform_request(f"api/knowledge/apps/argo/spec/{name}", "head")
    return response.ok


def _get_app_specification(appname) -> str:
    response = _perform_request(
        f"api/knowledge/apps/argo/spec/{appname}",
        "get",
    )
    if not response.ok:
        message = f"Something went wrong downloading app config `{appname}`: {response.text}"
        raise RuntimeError(message)
    return response.text

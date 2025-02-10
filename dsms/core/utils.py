"""Core utils of the DSMS core"""
import json
import logging
import re
from importlib import import_module
from typing import TYPE_CHECKING
from urllib.parse import urljoin
from uuid import UUID

import requests
from pydantic import SecretStr
from requests import Response

from dsms.core.logging import handler  # isort:skip

if TYPE_CHECKING:
    from typing import Any, Callable

logger = logging.getLogger(__name__)
logger.addHandler(handler)
logger.propagate = False


def _kitem_id2uri(kitem_id: UUID) -> str:
    "Convert a kitem id in the DSMS to the full resolvable URI"
    from dsms import Session

    return urljoin(str(Session.dsms.config.host_url), str(kitem_id))


def _uri2kitem_idi(uri: str) -> str:
    "Extract the kitem id from an URI of the DSMS"
    from dsms import Session

    return uri.replace(f"{Session.dsms.config.host_url}/", "").split("/")[0]


def _ping_dsms():
    """General check if the remote DSMS instance is up and running"""
    return _perform_request("api/knowledge/docs", "get")


def _perform_request(
    route: str, method: str, retry=True, headers=None, **kwargs: "Any"
) -> Response:
    """Perform a general request for a certain route and with a certain method.
    Kwargs are general arguments which can be passed to the `requests.request`-function.
    """
    from dsms import Session

    dsms = Session.dsms
    response = requests.request(
        method,
        url=urljoin(str(dsms.config.host_url), route),
        headers=headers or dsms.headers,
        timeout=dsms.config.request_timeout,
        verify=dsms.config.ssl_verify,
        **kwargs,
    )
    response.encoding = Session.dsms.config.encoding
    try:
        debug_text = json.dumps(response.json(), indent=2)
    except Exception:
        debug_text = response.text
    logger.debug("Received the follow response from route `%s`:", route)
    logger.debug(debug_text)
    if (
        response.status_code == 401
        and dsms.config.enable_auto_reauth
        and retry
    ):
        if dsms.config.username and dsms.config.password:
            username = dsms.config.username.get_secret_value()
            passwd = dsms.config.password.get_secret_value()
            authorization = f"Basic {username}:{passwd}"
            reauth = _perform_request(
                "api/users/token",
                "get",
                retry=False,
                headers={"Authorization": authorization},
            )
            if not reauth.ok:
                raise RuntimeError(f"Reauthentication failed: {reauth.text}")
            logger.debug("Reauthentication successful.")
            token = reauth.json().get("token")
            if "Bearer " not in token:
                dsms.config.token = SecretStr(f"Bearer {token}")
            else:
                dsms.config.token = SecretStr(token)
            response = _perform_request(
                route, method, retry=False, headers=None, **kwargs
            )
        else:
            logger.debug("No credentials found for reauthentication.")
    else:
        logger.debug(
            "Reauthentication skipped. Either not needed or not enabled."
        )
    return response


def _snake_to_camel(snake_str: str, first_upper=False) -> str:
    """Convert a snare-cases string to a camel-cased string.
    Optionally, the first letter can be lowered."""
    camel = "".join(x.title() for x in snake_str.split("_"))
    if first_upper:
        camel = camel[0].upper() + camel[1:]
    else:
        camel = camel[0].lower() + camel[1:]
    return camel


def _name_to_camel(input_string):
    """Remove special characters and make a CamelCased-str"""
    words = re.findall(r"\w+", input_string)
    camel_case_words = [word.title() for word in words]
    camel_case_string = "".join(camel_case_words)
    return camel_case_string


def get_callable(module: str) -> "Callable":
    """Get callable from import-specification"""
    module, classname = module.strip().split(":")
    return getattr(import_module(module), classname)

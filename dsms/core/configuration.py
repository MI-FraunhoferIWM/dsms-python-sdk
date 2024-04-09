"""General config for the DSMS Python SDK"""

import urllib
import warnings
from typing import TYPE_CHECKING, Optional

import requests
from pydantic import AnyUrl, Field, SecretStr, field_validator
from pydantic_core.core_schema import ValidationInfo
from pydantic_settings import BaseSettings, SettingsConfigDict

from .utils import get_callable

if TYPE_CHECKING:
    from typing import Callable

MODULE_REGEX = r"^[a-zA-Z_][a-zA-Z0-9_]*(\.[a-zA-Z_][a-zA-Z0-9_]*)*:[a-zA-Z_][a-zA-Z0-9_]*$"
DEFAULT_UNIT_SPARQL = "dsms.knowledge.semantics.units.sparql:UnitSparqlQuery"


class Configuration(BaseSettings):
    """General config for DSMS-SDK"""

    host_url: AnyUrl = Field(
        ..., description="Url of the DSMS instance to connect."
    )
    request_timeout: int = Field(
        30,
        description="Timeout in seconds until the request to the DSMS is timed out.",
    )

    username: Optional[SecretStr] = Field(
        None,
        description="User name for connecting to the DSMS instance",
    )
    password: Optional[SecretStr] = Field(
        None,
        description="Password for connecting to the DSMS instance",
    )
    token: Optional[SecretStr] = Field(
        None,
        description="JWT bearer token for connecting to the DSMS instance",
    )
    ssl_verify: bool = Field(
        True,
        description="Whether the SSL of the DSMS shall be verified during connection.",
    )

    encoding: str = Field(
        "utf-8",
        description="General encoding to be used for reading/writing serializations.",
    )

    datetime_format: str = Field(
        "%Y-%m-%dT%H:%M:%S.%f",
        description="Datetime format used in the DSMS instance.",
    )

    kitem_repo: str = Field(
        "knowledge",
        description="Repository of the triplestore for KItems in the DSMS",
    )

    qudt_units: AnyUrl = Field(
        "http://qudt.org/2.1/vocab/unit",
        description="URI to QUDT Unit ontology for unit conversion",
    )

    qudt_quantity_kinds: AnyUrl = Field(
        "http://qudt.org/vocab/quantitykind/",
        description="URI to QUDT quantity kind ontology for unit conversion",
    )

    units_sparql_object: str = Field(
        DEFAULT_UNIT_SPARQL,
        pattern=MODULE_REGEX,
        description="""Class and Module specification in Python for a subclass of
          `dsms.knowledge.semantics.units.base:BaseUnitSparqlQuery` in order to retrieve
          the units of a HDF5 column/ custom property of a KItem.""",
    )

    @field_validator("units_sparql_object")
    def get_unit_sparql_object(cls, val: str) -> "Callable":
        """Source the class from the given module"""
        return get_callable(val)

    @field_validator("token")
    def validate_auth(cls, val, info: ValidationInfo):
        """Validate the provided authentication/authorization secrets."""
        username = info.data.get("username")
        passwd = info.data.get("password")
        host_url = info.data.get("host_url")
        timeout = info.data.get("request_timeout")
        if username and passwd and val:
            raise ValueError(
                "Either `username` and `password` or `token` must be provided. Not both."
            )
        if username and not passwd:
            raise ValueError("`username` provided, but `password` not.")
        if not username and passwd:
            raise ValueError("`password` but not the `username` is defined.")
        if not username and not passwd and not val:
            warnings.warn(
                """No authentication details provided. Either `username` and `password`
                or `token` must be provided."""
            )
        if not val and username and passwd:
            url = urllib.parse.urljoin(str(host_url), "api/users/token")
            authorization = f"Basic {username.get_secret_value()}:{passwd.get_secret_value()}"
            response = requests.get(
                url,
                headers={"Authorization": authorization},
                timeout=timeout,
            )
            if not response.ok:
                raise RuntimeError(
                    f"Something went wrong fetching the access token: {response.text}"
                )
            val = response.json().get("token")
        if isinstance(val, str):
            if "Bearer " not in val:
                val = SecretStr(f"Bearer {val}")
            else:
                val = SecretStr(val)
        elif isinstance(val, SecretStr):
            if "Bearer " not in val.get_secret_value():
                val = SecretStr(f"Bearer {val.get_secret_value()}")

        return val

    model_config = SettingsConfigDict(env_prefix="DSMS_")

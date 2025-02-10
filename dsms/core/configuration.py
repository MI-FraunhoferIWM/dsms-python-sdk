"""General config for the DSMS Python SDK"""

import logging
import urllib
import warnings
from enum import Enum
from typing import Callable, Optional, Set, Union

import requests

from pydantic_core.core_schema import ValidationInfo  # isort: skip
from pydantic_settings import BaseSettings, SettingsConfigDict  # isort: skip


from pydantic import (  # isort: skip
    AliasChoices,
    AnyUrl,
    ConfigDict,
    Field,
    SecretStr,
    field_validator,
)

from .utils import get_callable  # isort: skip

MODULE_REGEX = r"^[a-zA-Z_][a-zA-Z0-9_]*(\.[a-zA-Z_][a-zA-Z0-9_]*)*:[a-zA-Z_][a-zA-Z0-9_]*$"
DEFAULT_UNIT_SPARQL = "dsms.knowledge.semantics.units.sparql:UnitSparqlQuery"
DEFAULT_REPO = "knowledge-items"


class Loglevel(Enum):
    """Enum mapping for default log levels"""

    DEBUG: logging.DEBUG
    INFO: logging.INFO
    ERROR: logging.ERROR
    CRITICAL: logging.CRITICAL
    WARNING: logging.WARNING


class Configuration(BaseSettings):
    """General config for DSMS-SDK"""

    host_url: AnyUrl = Field(
        ..., description="Url of the DSMS instance to connect."
    )
    request_timeout: int = Field(
        120,
        description="Timeout in seconds until the request to the DSMS is timed out.",
    )

    ssl_verify: bool = Field(
        True,
        description="Whether the SSL of the DSMS shall be verified during connection.",
    )

    strict_validation: bool = Field(
        True,
        description="""Whether the validation of custom properties shall be strict.
        Disabling this might be helpful when e.g. the schema of a KType has been changed
        and the custom properties are not compatible anymore and should be updated accordingly.""",
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

    enable_auto_reauth: bool = Field(
        True,
        description="""Whether to automatically reauthenticate with username and password
        when the token is expired.""",
    )

    ping_dsms: bool = Field(
        True, description="Check whether the host is a DSMS instance or not."
    )

    auto_fetch_ktypes: bool = Field(
        True,
        description="""Whether the KTypes of the DSMS should be fetched automatically
        when the session is started. They will be fetched if requested and cached
        in memory.""",
    )

    always_refetch_ktypes: bool = Field(
        False,
        description="""Whether the KTypes of the DSMS should be refetched
        every time used in the SDK. This can be helpful if the SDK is integrated
        in a service and the KTypes are updated.
        WARNING: This might lead to performance issues.""",
    )

    individual_slugs: bool = Field(
        True,
        description="""When set to `True`, the slugs of the KItems will receive the
        first few characters of the KItem-id, when the slug is derived automatically
        from the KItem-name.""",
    )

    encoding: str = Field(
        "utf-8",
        description="General encoding to be used for reading/writing serializations.",
    )

    datetime_format: str = Field(
        "%Y-%m-%dT%H:%M:%S.%f",
        description="Datetime format used in the DSMS instance.",
    )

    display_units: bool = Field(
        False,
        description="""Whether the custom properties or the dataframe columns shall
        directly reveal their unit when printed. WARNING: This might lead to performance issues.""",
    )

    autocomplete_units: bool = Field(
        True,
        description="""When a unit is fetched but does not hold a symbol
        next to its URI, it shall be fetched from the respective ontology
        (which is general side effect from the `units_sparq_object`.)
        WARNING: This might lead to performance issues.""",
    )

    kitem_repo: str = Field(
        DEFAULT_REPO,
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
          the units of a DataFrame column/ custom property of a KItem.""",
    )

    hide_properties: Set[Union[str, None]] = Field(
        set(),
        description="Properties to hide while printing, e.g {'external_links'}",
    )

    loglevel: Optional[Union[Loglevel, str]] = Field(
        None,
        description="Set level of logging messages",
        alias=AliasChoices("loglevel", "log_level"),
    )

    model_config = ConfigDict(use_enum_values=True)

    @field_validator("loglevel")
    def get_loglevel(
        cls, val: Optional[Union[Loglevel, str]]
    ) -> Optional[Loglevel]:
        """Set log level for package"""
        if val:
            logging.getLogger().setLevel(val)
        return val

    @field_validator("units_sparql_object")
    def get_unit_sparql_object(cls, val: str) -> "Callable":
        """Source the class from the given module"""
        return get_callable(val)

    @field_validator("hide_properties")
    def validate_hide_properties(cls, val: Set) -> "Callable":
        """Source the class from the given module"""
        from dsms import KItem

        for key in val:
            if key not in KItem.model_fields:  # pylint: disable=E1135
                raise KeyError(f"Property `{key}` not in KItem schema")
        return val

    @field_validator("strict_validation")
    def validate_strictness(cls, val: bool) -> bool:
        """
        Validate the strictness of the custom properties validation.

        If strict validation is disabled, custom properties are not validated
        against the schema. Instead, the custom properties are allowed to have
        any value.

        :param val: If True, use strict validation for custom properties.
        :return: The validated value.
        """
        if not val:
            warnings.warn(
                "Strict validation for custom properties is disabled."
            )
        return val

    @field_validator("token")
    def validate_auth(cls, val, info: ValidationInfo):
        """Validate the provided authentication/authorization secrets."""
        username = info.data.get("username")
        passwd = info.data.get("password")
        host_url = info.data.get("host_url")
        timeout = info.data.get("request_timeout")
        verify = info.data.get("ssl_verify")
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
                verify=verify,
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

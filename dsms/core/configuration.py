"""General config for the DSMS Python SDK"""

import logging
import urllib
import warnings
from enum import Enum
from typing import Callable, Optional, Set, Union

import requests

from pydantic_settings import BaseSettings, SettingsConfigDict  # isort: skip


from pydantic import (  # isort: skip
    AliasChoices,
    AnyUrl,
    ConfigDict,
    Field,
    SecretStr,
    model_validator,
    field_validator,
)

from dsms.core.utils import get_callable  # isort: skip
from dsms.core.logging import handler  # isort: skip

MODULE_REGEX = r"^[a-zA-Z_][a-zA-Z0-9_]*(\.[a-zA-Z_][a-zA-Z0-9_]*)*:[a-zA-Z_][a-zA-Z0-9_]*$"
DEFAULT_UNIT_SPARQL = "dsms.knowledge.semantics.units.sparql:UnitSparqlQuery"
DEFAULT_REPO = "knowledge-items"

logger = logging.getLogger(__name__)
logger.addHandler(handler)
logger.propagate = False


class Loglevel(Enum):
    """Enum mapping for default log levels"""

    DEBUG = logging.DEBUG
    INFO = logging.INFO
    ERROR = logging.ERROR
    CRITICAL = logging.CRITICAL
    WARNING = logging.WARNING


class Configuration(BaseSettings):
    """General config for DSMS-SDK"""

    host_url: AnyUrl = Field(
        ..., description="Url of the DSMS instance to connect."
    )

    username: Optional[SecretStr] = Field(
        None,
        description="User name for connecting to the DSMS instance",
    )
    password: Optional[SecretStr] = Field(
        None,
        description="Password for connecting to the DSMS instance",
    )

    client_id: Optional[SecretStr] = Field(
        None,
        description="""If a service account is used to authenticate,
        this will proviode the Client ID in Keycloak""",
        validation_alias=AliasChoices(
            "DSMS_CLIENT_ID", "KEYCLOAK_DSMS_CLIENT_ID", "KEYCLOAK_CLIENT_ID"
        ),
    )

    client_secret: Optional[SecretStr] = Field(
        None,
        description="""If a service account is used to authenticate,
        this will proviode the Client Secret in Keycloak""",
        validation_alias=AliasChoices(
            "DSMS_CLIENT_SECRET",
            "KEYCLOAK_DSMS_CLIENT_SECRET",
            "KEYCLOAK_CLIENT_SECRET",
        ),
    )

    realm: Optional[SecretStr] = Field(
        "dsms",
        description="""When the Cliend ID and Client secret is used for authentication
        with a service account, this is the realm name to be used""",
        validation_alias=AliasChoices("DSMS_REALM", "KEYCLOAK_REALM_NAME"),
    )

    token: Optional[SecretStr] = Field(
        None,
        description="JWT bearer token for connecting to the DSMS instance",
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

    enable_auto_reauth: bool = Field(
        True,
        description="""Whether to automatically reauthenticate with username and password
        when the token is expired.""",
    )

    auto_refresh: bool = Field(
        True,
        description="""Determines whether local objects like KItem, KType,
        and AppConfig should automatically update with the latest backend data
        after a successful commit.""",
    )

    ping_backend: bool = Field(
        True,
        description="Check whether the host is a DSMS instance or not.",
        alias=AliasChoices("ping_dsms", "ping_backend", "ping"),
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

    loglevel: Optional[Union[Loglevel, str]] = Field(
        None,
        description="Set level of logging messages",
        alias=AliasChoices("loglevel", "log_level"),
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

    model_config = ConfigDict(use_enum_values=True)

    @field_validator("loglevel")
    def get_loglevel(
        cls, val: Optional[Union[Loglevel, str]]
    ) -> Optional[Loglevel]:
        """Set log level for package"""
        if val:
            logging.getLogger().setLevel(val)
            logger.setLevel(val)
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

    @model_validator(mode="after")
    def validate_auth(self):
        """Validate the provided authentication/authorization secrets."""
        username = self.username
        passwd = self.password
        host_url = self.host_url
        client_id = self.client_id
        client_secret = self.client_secret
        realm = self.realm
        timeout = self.request_timeout
        verify = self.ssl_verify
        val = self.token

        if client_id and client_secret:
            token_url = urllib.parse.urljoin(
                str(host_url),
                f"/auth/realms/{realm.get_secret_value()}/protocol/openid-connect/token",  # pylint: disable=no-member
            )
            headers = {"Content-Type": "application/x-www-form-urlencoded"}
            data = {
                "grant_type": "client_credentials",
                "client_id": client_id.get_secret_value(),  # pylint: disable=no-member
                "client_secret": client_secret.get_secret_value(),  # pylint: disable=no-member
            }
            logger.debug("Sending post request to %s", token_url)
            response = requests.post(
                token_url,
                headers=headers,
                data=data,
                timeout=timeout,
                verify=verify,
            )
            if not response.ok:
                raise RuntimeError(
                    f"Authentication with service account was not successful: {response.text}",
                )
            val = response.json().get("access_token")
            logger.info(
                "Authenticated with Client ID and Client Secret at %s",
                host_url,
            )
        elif username and passwd:
            url = urllib.parse.urljoin(str(host_url), "api/users/token")
            authorization = f"Basic {username.get_secret_value()}:{passwd.get_secret_value()}"  # pylint: disable=no-member
            logger.debug("Sending get request to %s", url)
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
            logger.info(
                "Authenticated with User name and Password at %s", host_url
            )
        elif val:
            logger.info(
                "Authenticated using token copied from WebUI interface at %s",
                host_url,
            )
        else:
            provided = {
                key: value is not None
                for key, value in {
                    "client_id": client_id,
                    "client_secret": client_secret,
                    "username": username,
                    "password": passwd,
                    "token": val,
                }.items()
            }
            warnings.warn(
                f"""No authentication details provided - protected endpoints may be inaccessible.
                The followings were provided: {provided}""",
            )

        if isinstance(val, str):
            if "Bearer " not in val:
                val = SecretStr(f"Bearer {val}")
            else:
                val = SecretStr(val)
        elif isinstance(val, SecretStr):
            if (
                "Bearer "
                not in val.get_secret_value()  # pylint: disable=no-member
            ):
                val = SecretStr(
                    f"Bearer {val.get_secret_value()}"  # pylint: disable=no-member
                )

        # Set the validated token value and return self
        self.token = val
        return self

    model_config = SettingsConfigDict(env_prefix="DSMS_")

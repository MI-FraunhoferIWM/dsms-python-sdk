"""General config for the DSMS Python SDK"""

import urllib
import warnings
from typing import Optional

import requests
from pydantic import AnyUrl, Field, SecretStr, field_validator
from pydantic_core.core_schema import ValidationInfo
from pydantic_settings import BaseSettings, SettingsConfigDict


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

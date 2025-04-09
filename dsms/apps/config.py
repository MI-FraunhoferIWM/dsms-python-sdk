"""DSMS app models"""
import logging
import urllib.parse
import warnings
from typing import TYPE_CHECKING, Any, Dict, Union

import yaml

from pydantic import (  # isort:skip
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
    model_validator,
)

from dsms.knowledge.utils import print_model  # isort:skip

from dsms.core.logging import handler  # isort:skip

from dsms.core.session import Session  # isort:skip


logger = logging.getLogger(__name__)
logger.addHandler(handler)
logger.propagate = False

if TYPE_CHECKING:
    from dsms import DSMS


class AppConfig(BaseModel):
    """App config model"""

    name: str = Field(..., description="File name of the app in the DSMS.")

    specification: Union[str, Dict[str, Any]] = Field(
        ...,
        description="File path for YAML Specification of the app",
    )

    expose_sdk_config: bool = Field(
        False,
        description="""
            Determines whether SDK parameters (such as host URL, SSL verification, etc.)
            should be passed through or propagated to the app using the SDK.
            If set to True, the SDK's configuration will be made available
            for the app to use, allowing it to inherit settings such as the host URL
            or SSL configuration. If False, the app will not have access to these parameters,
            and the SDK will handle its own configuration independently.
            The `token` will not be set here.
            Defaults to False.
            """,
    )

    model_config = ConfigDict(
        extra="forbid",
        validate_assignment=True,
        arbitrary_types_allowed=True,
    )

    def __init__(self, **kwargs: "Any") -> None:
        """Initialize the AppConfig"""
        # set dsms instance if not already done
        if not self.dsms:
            raise ValueError(
                "DSMS instance not set. Please call DSMS() before initializing a KItem."
            )

        # initialize the app config
        super().__init__(**kwargs)

        logger.debug("AppConfig initialization successful.")

    def __str__(self) -> str:
        """Pretty print the kitem Fields"""
        return print_model(self, "app", exclude_extra={"specification"})

    def __repr__(self) -> str:
        """Pretty print the kitem Fields"""
        return str(self)

    def refresh(self):
        """Warn that AppConfig does not support refresh functionality."""

        warnings.warn(
            "AppConfigs do not have a refresh functionality since they are "
            "already up to date after committing. "
            "You can continue normally using the app config."
        )

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str) -> str:
        """Check whether the name of the app contains invalid characters."""
        new_value = urllib.parse.quote_plus(value)
        if not new_value == value:
            raise ValueError(f"Basename contains invalid characters: {value}")
        return value

    @model_validator(mode="after")
    @classmethod
    def validate_specification(cls, self: "AppConfig") -> str:
        """Check specification to be uploaded"""
        config = self.dsms.config

        if isinstance(self.specification, str):
            try:
                with open(
                    self.specification, encoding=config.encoding
                ) as file:
                    content = file.read()
            except Exception as error:
                raise FileNotFoundError(
                    f"Invalid file path. File does not exist under path `{self.specification}`."
                ) from error
            try:
                self.specification = yaml.safe_load(content)
            except Exception as error:
                raise RuntimeError(
                    f"Invalid yaml specification path: `{error.args[0]}`"
                ) from error

        if self.expose_sdk_config:
            self.specification["spec"]["arguments"]["parameters"] += [
                {
                    "name": "request_timeout",
                    "value": config.request_timeout,
                },
                {"name": "ping", "value": config.ping_backend},
                {"name": "host_url", "value": str(config.host_url)},
                {"name": "ssl_verify", "value": config.ssl_verify},
                {"name": "kitem_repo", "value": config.kitem_repo},
                {"name": "encoding", "value": config.encoding},
            ]
        return self

    @property
    def session(self) -> "Session":
        """Getter for Session"""
        return Session

    @property
    def dsms(self) -> "DSMS":
        """DSMS session getter"""
        return self.session.dsms

"""DSMS app models"""
import logging
import urllib.parse
from typing import TYPE_CHECKING, Any, Dict, Union

import yaml

from pydantic import (  # isort:skip
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
    model_validator,
)

from dsms.apps.utils import (  # isort:skip
    _app_spec_exists,
    _get_app_specification,
)


from dsms.core.logging import handler  # isort:skip


logger = logging.getLogger(__name__)
logger.addHandler(handler)
logger.propagate = False

if TYPE_CHECKING:
    from dsms import DSMS, Context


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
        """Initialize the KItem"""
        from dsms import DSMS

        logger.debug("Initialize KItem with model data: %s", kwargs)

        # set dsms instance if not already done
        if not self.dsms:
            self.dsms = DSMS()

        # initialize the app config
        super().__init__(**kwargs)

        # add app config to buffer
        if (
            not self.in_backend
            and self.name not in self.context.buffers.created
        ):
            logger.debug(
                """Marking AppConfig with name `%s` as created
                and updated during AppConfig initialization.""",
                self.name,
            )
            self.context.buffers.created.update({self.name: self})
            self.context.buffers.updated.update({self.name: self})

        logger.debug("AppConfig initialization successful.")

    def __setattr__(self, name, value) -> None:
        """Add app to updated-buffer if an attribute is set"""
        super().__setattr__(name, value)
        logger.debug(
            "Setting property with key `%s` on KItem level: %s.", name, value
        )
        if self.name not in self.context.buffers.updated:
            logger.debug(
                "Setting AppConfig with name `%s` as updated during AppConfig.__setattr__",
                self.name,
            )
            self.context.buffers.updated.update({self.name: self})

    def __str__(self) -> str:
        """Pretty print the app config fields"""
        fields = ", ".join(
            [
                "{key}={value}".format(  # pylint: disable=consider-using-f-string
                    key=key,
                    value=(
                        value
                        if key != "specification"
                        else {
                            "metadata": value.get(  # pylint: disable=no-member
                                "metadata"
                            )
                        }
                    ),
                )
                for key, value in self.__dict__.items()
            ]
        )
        return f"{self.__class__.__name__}({fields})"

    def __repr__(self) -> str:
        """Pretty print the kitem Fields"""
        return str(self)

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

        if isinstance(self.specification, str):
            try:
                with open(
                    self.specification, encoding=self.dsms.config.encoding
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
            self.context.buffers.updated.update({self.name: self})
        elif isinstance(self.specification, dict) and self.in_backend:
            spec = _get_app_specification(self.name)
            if (
                not yaml.safe_load(spec) == self.specification
                and self.name not in self.context.buffers.updated
            ):
                self.context.buffers.updated.update({self.name: self})
        elif (
            isinstance(self.specification, dict)
            and not self.in_backend
            and self.name not in self.context.buffers.updated
        ):
            self.context.buffers.updated.update({self.name: self})
        if self.expose_sdk_config:
            self.specification["spec"]["arguments"]["parameters"] += [
                {
                    "name": "request_timeout",
                    "value": self.dsms.config.request_timeout,
                },
                {"name": "ping", "value": self.dsms.config.ping_dsms},
                {"name": "host_url", "value": str(self.dsms.config.host_url)},
                {"name": "ssl_verify", "value": self.dsms.config.ssl_verify},
                {"name": "kitem_repo", "value": self.dsms.config.kitem_repo},
                {"name": "encoding", "value": self.dsms.config.encoding},
            ]
        return self

    @property
    def in_backend(self) -> bool:
        """Checks whether the app config already exists."""
        return _app_spec_exists(self.name)

    @property
    def context(cls) -> "Context":
        """Getter for Context"""
        from dsms import (  # isort:skip
            Context,
        )

        return Context

    @property
    def dsms(self) -> "DSMS":
        """DSMS context getter"""
        return self.context.dsms

    @dsms.setter
    def dsms(self, value: "DSMS") -> None:
        """DSMS context setter"""
        self.context.dsms = value

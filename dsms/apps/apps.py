"""DSMS apps models"""
import logging
import os
import urllib.parse
from typing import TYPE_CHECKING, Any, Dict, Union

import yaml

from pydantic import (  # isort:skip
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
)

from dsms.apps.utils import (  # isort:skip
    _app_exists,
)


from dsms.core.logging import handler  # isort:skip


logger = logging.getLogger(__name__)
logger.addHandler(handler)
logger.propagate = False

if TYPE_CHECKING:
    from dsms import DSMS, Context


class App(BaseModel):
    """KItem app list"""

    name: str = Field(..., description="File name of the app in the DSMS.")

    specification: Union[str, Dict[str, Any]] = Field(
        ...,
        description="File path for content of YAML Specification of the app",
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

        # initialize the app
        super().__init__(**kwargs)

        # add app to buffer
        if (
            not self.in_backend
            and self.name not in self.context.buffers.created
        ):
            logger.debug(
                "Marking App with name `%s` as created and updated during App initialization.",
                self.name,
            )
            self.context.buffers.created.update({self.name: self})
            self.context.buffers.updated.update({self.name: self})

        logger.debug("App initialization successful.")

    def __setattr__(self, name, value) -> None:
        """Add app to updated-buffer if an attribute is set"""
        super().__setattr__(name, value)
        logger.debug(
            "Setting property with key `%s` on KItem level: %s.", name, value
        )
        if self.name not in self.context.buffers.updated:
            logger.debug(
                "Setting App with name `%s` as updated during App.__setattr__",
                self.id,
            )
            self.context.buffers.updated.update({self.name: self})

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str) -> str:
        """Check whether the name of the app contains invalid characters."""
        new_value = urllib.parse.quote_plus(value)
        if not new_value == value:
            raise ValueError(f"Basename contains invalid characters: {value}")
        return value

    @field_validator("specification")
    @classmethod
    def validate_specification(cls, value: Union[str, Dict[str, Any]]) -> str:
        """Check whether the specification to be uploaded"""
        from dsms import Context

        if isinstance(value, str):
            try:
                if os.path.exists(value):
                    with open(
                        value, encoding=Context.dsms.config.encoding
                    ) as file:
                        value = yaml.safe_load(file.read())
                else:
                    value = yaml.safe_load(value)
            except Exception as error:
                raise RuntimeError(
                    "Invalid file path or YAML syntax."
                ) from error
        return value

    @property
    def in_backend(self) -> bool:
        """Checks whether the app already exists."""
        return _app_exists(self.name)

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

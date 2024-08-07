"""DSMS apps models"""

import logging
import urllib.parse
from typing import TYPE_CHECKING, Optional

from pydantic import (  # isort:skip
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
    model_validator,
)

from dsms.apps.utils import (  # isort:skip
    _get_app_specification,
    _get_available_apps,
)


from dsms.core.logging import handler  # isort:skip


logger = logging.getLogger(__name__)
logger.addHandler(handler)
logger.propagate = False

if TYPE_CHECKING:
    from typing import Any

    from dsms import DSMS, Context


class App(BaseModel):
    """KItem app list"""

    filename: Optional[str] = Field(
        "", description="File name of the app in the DSMS."
    )
    basename: str = Field(..., description="Base name of the app in the DSMS.")
    folder: Optional[str] = Field(
        "", description="Directory of the app in the DSMS."
    )

    specification: Optional[str] = Field(
        None,
        description="File path for content of YAML Specification of the app",
    )

    model_config = ConfigDict(
        extra="forbid",
        validate_assignment=True,
        validate_default=True,
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
            and self.basename not in self.context.buffers.created
        ):
            logger.debug(
                "Marking App with name `%s` as created and updated during App initialization.",
                self.basename,
            )
            self.context.buffers.created.update({self.basename: self})
            self.context.buffers.updated.update({self.basename: self})

        logger.debug("App initialization successful.")

    def __setattr__(self, name, value) -> None:
        """Add app to updated-buffer if an attribute is set"""
        super().__setattr__(name, value)
        logger.debug(
            "Setting property with key `%s` on KItem level: %s.", name, value
        )
        if self.basename not in self.context.buffers.updated:
            logger.debug(
                "Setting App with name `%s` as updated during App.__setattr__",
                self.id,
            )
            self.context.buffers.updated.update({self.basename: self})

    @field_validator("basename")
    @classmethod
    def validate_basename(cls, value: str) -> str:
        """Check whether the basename of the app contains invalid characters."""
        new_value = urllib.parse.quote_plus(value)
        if not new_value == value:
            raise ValueError(f"Basename contains invalid characters: {value}")

    @model_validator(mode="after")
    @classmethod
    def validate_app(cls, self: "App") -> "App":
        """Validate app definition."""
        if self.in_backend and not self.specification:
            self.specification = _get_app_specification(self.filename)
            logger.info(
                "App already exists in backend. Fetched the YAML specification."
            )
        return self

    @property
    def in_backend(self) -> bool:
        """Checks whether the app already exists."""
        return self.basename in [
            app.get("basename") for app in _get_available_apps()
        ]

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

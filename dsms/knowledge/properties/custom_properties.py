"""Custom properties of a KItem"""


from typing import TYPE_CHECKING, Any, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator

from .custom_datatype.numerical import NumericalDataType

if TYPE_CHECKING:
    from typing import Set, Union

    from dsms import Context


class CustomProperties(BaseModel):
    """Model for the custom properties of the KItem"""

    id: Optional[UUID] = Field(None, description="ID of the KItem")
    content: Any = Field({}, description="Constent of the custom kitem")
    kitem: Optional[Any] = Field(
        None, description="KItem related to the CustomProperties", exclude=True
    )

    model_config = ConfigDict(
        extra="forbid", exclude={"kitem", "id"}, validate_assignment=True
    )

    def __str__(self) -> str:
        """Pretty print the custom properties"""
        fields = ", ".join(
            [
                f"{key}={value}"
                for key, value in self.__dict__.items()
                if key not in self.exclude
            ]
        )
        return f"{self.__class__.__name__}({fields})"

    def __repr__(self) -> str:
        """Pretty print the custom properties"""
        return str(self)

    def __hash__(self) -> int:
        return hash(str(self))

    def add(self, content: "Union[dict, Any]") -> None:
        """Add data for custom properties"""
        if isinstance(content, type(None)):
            self.content = {}
        elif self.data_schema and isinstance(content, dict):
            self.content = self.data_schema(content)
        elif not self.data_schema and isinstance(content, dict):
            self.content = content
        elif self.data_schema:
            if isinstance(content, self.data_schema):
                self.content = content
            else:
                raise TypeError(
                    f"""Item `{content}` must be of type {self.data_schema} or {dict},
                    not `{type(content)}`."""
                )
        else:
            raise TypeError(
                f"""Item `{content}` must be of type {self.data_schema} or {dict},
                not `{type(content)}`."""
            )
        self._mark_as_updated()

    def _mark_as_updated(self) -> None:
        if self.kitem and self.id not in self.context.buffers.updated:
            self.context.buffers.updated.update({self.id: self.kitem})

    def delete(self) -> None:
        """Delete data for custom properties"""
        self.content = None
        self._mark_as_updated()

    def update(self, content: "Union[dict, Any]") -> None:
        """Update data for custom properties"""
        self.content = None
        self.add(content)

    def get(self) -> Any:
        """Get data for custom properties"""
        return self.content

    @model_validator(mode="after")
    @classmethod
    def validate_content(cls, self) -> "CustomProperties":
        """Validate the custom properties with respect to the KType of the KItem"""
        if self.kitem and isinstance(self.content, dict):
            # validate content with webform model
            if self.kitem.ktype.webform:
                self.content = self.kitem.ktype.webform(**self.content)
            # set name and property of the inidivdual properties
            if isinstance(self.content, dict):
                iterable = self.content
            else:
                iterable = self.content.dict()
            for name, subproperty in iterable.items():
                if isinstance(subproperty, NumericalDataType):
                    if not subproperty.name:
                        subproperty.name = name
                    if not subproperty.kitem_id:
                        subproperty.kitem_id = self.kitem.id
        return self

    @property
    def id(cls) -> Optional[UUID]:
        """Identifier of the KItem related to the CustomProperies"""
        if not cls.kitem:
            raise ValueError("KItem not defined yet.")
        return cls.kitem.id  # pylint: disable=E1101

    @property
    def data_schema(cls):
        """Data schema related to the ktype of the associated kitem."""
        if not cls.kitem:
            raise ValueError("KItem not defined yet.")
        return cls.kitem.ktype.webform  # pylint: disable=E1101

    @property
    def context(cls) -> "Context":
        """Getter for Context"""
        from dsms import (  # isort:skip
            Context,
        )

        return Context

    @property
    def exclude(cls) -> "Optional[Set[str]]":
        """Fields to be excluded from the JSON-schema"""
        return cls.model_config.get("exclude")

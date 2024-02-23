"""Custom properties of a KItem"""


from typing import TYPE_CHECKING, Any, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator

if TYPE_CHECKING:
    from typing import Set, Union

    from dsms import Context, KItem


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

    @model_validator(mode="before")
    @classmethod
    def validate_kitem(cls, data: Any) -> "KItem":
        """Validate the custom properties with respect to the KType of the KItem"""
        kitem = data.get("kitem")
        content = data.get("content")
        if kitem:
            data["id"] = kitem.id
            if kitem.ktype.data_schema:
                data["content"] = kitem.ktype.data_schema(**content)
        return data

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
        return cls.kitem.ktype.data_schema  # pylint: disable=E1101

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

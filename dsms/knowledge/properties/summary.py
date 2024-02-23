"""Custom properties of a KItem"""


from typing import TYPE_CHECKING, Any, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_serializer

if TYPE_CHECKING:
    from typing import Set

    from dsms import Context


class Summary(BaseModel):
    """Model for the custom properties of the KItem"""

    id: Optional[UUID] = Field(None, description="ID of the KItem")
    text: str = Field(..., description="Summary text of the KItem")
    kitem: Optional[Any] = Field(
        None, description="KItem related to the summary", exclude=True
    )

    model_config = ConfigDict(
        extra="forbid", exclude={"kitem", "id"}, validate_assignment=True
    )

    def __setattr__(self, name, value) -> None:
        """Add kitem to updated-buffer if an attribute is set"""
        super().__setattr__(name, value)
        self._mark_as_updated()

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

    def _mark_as_updated(self) -> None:
        if self.kitem and self.id not in self.context.buffers.updated:
            self.context.buffers.updated.update({self.id: self.kitem})

    @property
    def id(cls) -> Optional[UUID]:
        """Identifier of the KItem related to the CustomProperies"""
        if not cls.kitem:
            raise ValueError("KItem not defined yet.")
        return cls.kitem.id  # pylint: disable=E1101

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

    @model_serializer
    def serialize(self) -> str:
        """Serialize the summary model"""
        return self.text

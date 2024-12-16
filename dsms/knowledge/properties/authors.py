"""Author property of a KItem"""

from typing import TYPE_CHECKING, Any, Dict
from uuid import UUID

from pydantic import Field, model_serializer

from dsms.knowledge.properties.base import KItemProperty, KItemPropertyList
from dsms.knowledge.utils import print_model

if TYPE_CHECKING:
    from typing import Callable


class Author(KItemProperty):
    """Author of a KItem."""

    user_id: UUID = Field(
        ...,
        description="ID of the DSMS User",
    )

    # OVERRIDE
    @model_serializer
    def serialize_author(self) -> Dict[str, Any]:
        """Serialize author model"""
        return {
            key: str(value)
            for key, value in self.__dict__.items()
            if key != "id"
        }

    # OVERRIDE
    def __str__(self):
        return print_model(self, "author")


class AuthorsProperty(KItemPropertyList):
    """KItemPropertyList for authors"""

    # OVERRIDE
    @property
    def k_property_item(cls) -> "Callable":
        """Author data model"""
        return Author

    # OVERRIDE
    @property
    def k_property_helper(cls) -> None:
        """Not defined for Authors"""

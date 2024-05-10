"""Author KItemPropertyList"""

from typing import TYPE_CHECKING
from uuid import UUID

from pydantic import Field

from dsms.knowledge.properties.base import KItemProperty, KItemPropertyList

if TYPE_CHECKING:
    from typing import Callable


class Author(KItemProperty):
    """Author of a KItem."""

    user_id: UUID = Field(..., description="ID of the DSMS User")


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

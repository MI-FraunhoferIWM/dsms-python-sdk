"""Author KProperty"""

from typing import TYPE_CHECKING
from uuid import UUID

from pydantic import Field

from dsms.knowledge.properties.base import KProperty, KPropertyItem

if TYPE_CHECKING:
    from typing import Callable


class Author(KPropertyItem):
    """Author of a KItem."""

    user_id: UUID = Field(..., description="ID of the DSMS User")


class AuthorsProperty(KProperty):
    """KProperty for authors"""

    # OVERRIDE
    @property
    def k_property_item(cls) -> "Callable":
        """Author data model"""
        return Author

    # OVERRIDE
    def _add(self, item: Author) -> Author:
        """Side effect when an Author is added to the KProperty"""
        return item

    # OVERRIDE
    def _update(self, item: Author) -> Author:
        """Side effect when an Author is updated at the KProperty"""
        return item

    # OVERRIDE
    def _get(self, item: Author) -> Author:
        """Side effect when getting the Author for a specfic kitem"""
        return item

    # OVERRIDE
    def _delete(self, item: Author) -> None:
        """Side effect when deleting the Author of a KItem"""

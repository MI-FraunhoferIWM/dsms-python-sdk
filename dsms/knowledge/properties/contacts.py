"""DContacts KProperty"""


from typing import TYPE_CHECKING, Optional
from uuid import UUID

from pydantic import Field

from dsms.knowledge.properties.base import KProperty, KPropertyItem

if TYPE_CHECKING:
    from typing import Callable


class ContactInfo(KPropertyItem):
    """Contact info"""

    name: str = Field(..., description="Name of the contact person")
    email: str = Field(..., description="EMail of the contact person")
    user_id: Optional[UUID] = Field(
        None, description="User ID of the contact person"
    )


class ContactsProperty(KProperty):
    """KProperty for contacts"""

    # OVERRIDE
    @property
    def k_property_item(cls) -> "Callable":
        return ContactInfo

    # OVERRIDE
    @property
    def k_property_helper(cls) -> None:
        """Not defined for Contacts"""

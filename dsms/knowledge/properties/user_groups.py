"""UserGroup KProperty"""

from typing import TYPE_CHECKING

from pydantic import Field

from dsms.knowledge.properties.base import KProperty, KPropertyItem

if TYPE_CHECKING:
    from typing import Callable


class UserGroup(KPropertyItem):
    """Users groups related to a KItem."""

    name: str = Field(..., description="Name of the user group")
    group_id: str = Field(..., description="ID of the user group")


class UserGroupsProperty(KProperty):
    """KProperty for user_groups"""

    @property
    def k_property_item(cls) -> "Callable":
        """UserGroup data model"""
        return UserGroup

    @property
    def k_property_helper(cls) -> None:
        """Not defined for User groups"""

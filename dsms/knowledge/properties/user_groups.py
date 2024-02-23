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

    # OVERRIDE
    def _add(self, item: UserGroup) -> UserGroup:
        """Side effect when an UserGroup is added to the KProperty"""
        return item

    # OVERRIDE
    def _update(self, item: UserGroup) -> UserGroup:
        """Side effect when an UserGroup is updated at the KProperty"""
        return item

    # OVERRIDE
    def _get(self, item: UserGroup) -> UserGroup:
        """Side effect when getting the UserGroup for a specfic kitem"""
        return item

    # OVERRIDE
    def _delete(self, item: UserGroup) -> None:
        """Side effect when deleting the UserGroup of a KItem"""

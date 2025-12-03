"""DSMS User Groups Module."""

from enum import Enum
from typing import List, Optional

import yaml
from pydantic import BaseModel, Field

from dsms.core.session import Session


class PublicGroupType(str, Enum):
    """Enumeration for Public Group Types."""

    INTERNAL = "dsms:internally-public"
    EXTERNAL = "dsms:externally-public"


class User(BaseModel):
    """User Model"""

    id: str = Field(..., description="The unique identifier of the user.")
    username: str = Field(..., description="The username of the user.")


class Group(BaseModel):
    """User Group Model"""

    id: str = Field(..., description="The unique identifier of the group.")
    name: str = Field(..., description="The name of the group.")
    subgroups: Optional[List["Group"]] = Field(
        None, description="A list of subgroups."
    )


class GroupListBase(list):
    """Base class for GroupList with utility methods."""

    def __repr__(self) -> str:
        """String representation of the GroupList."""
        return str(self)

    def __str__(self):
        """Pretty print the LinkedKItemList"""
        from dsms.knowledge.utils import dump_model

        return yaml.dump(
            [
                dump_model(
                    connection,
                    exclude_extra=Session.dsms.config.hide_properties,
                )
                for connection in self
            ]
        )


class GroupList(list):
    """List of Groups with utility methods."""

    @property
    def flat(self) -> List[Group]:
        """Return a flat list of all groups and their subgroups."""
        flat_list = []

        def _flatten(groups: List[Group]):
            for group in groups:
                flat_list.append(
                    Group(**group.model_dump(exclude={"subgroups"}))
                )
                if group.subgroups:
                    _flatten(group.subgroups)

        _flatten(self)
        return GroupListBase(flat_list)


Group.model_rebuild()

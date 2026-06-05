"""DSMS User Groups Module."""

from typing import List, Optional

import yaml
from pydantic import BaseModel, Field

from dsms.core.session import Session


class User(BaseModel):
    """User Model"""

    id: str = Field(..., description="The unique identifier of the user.")
    username: str = Field(..., description="The username of the user.")
    firstName: Optional[str] = Field(
        None, description="First name of the user."
    )
    lastName: Optional[str] = Field(None, description="Last name of the user.")
    email: Optional[str] = Field(
        None, description="Email address of the user."
    )
    user_groups: Optional[List["BaseGroup"]] = Field(
        None, description="A list of groups the user belongs to."
    )

    def __repr__(self) -> str:
        """String representation of the GroupList."""
        return str(self)

    def __str__(self):
        """Pretty print the User"""
        from dsms.knowledge.utils import print_model

        return print_model(
            self,
            "user",
            exclude_extra=Session.dsms.config.hide_properties,
        )


class UserList(list):
    """List of Users with utility methods."""

    def __repr__(self) -> str:
        """String representation of the GroupList."""
        return str(self)

    def __str__(self):
        """Pretty print the UserList"""
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

    @property
    def by_id(self) -> dict[str, User]:
        """Return a dictionary of users indexed by their ID."""
        return {user.id: user for user in self}

    @property
    def by_username(self) -> dict[str, User]:
        """Return a dictionary of users indexed by their username."""
        return {user.username: user for user in self}

    @property
    def by_name(self) -> dict[str, User]:
        """Return a dictionary of users indexed by their username."""
        return self.by_username

    def __getitem__(self, user_id: str) -> User:
        """Get a user by ID"""

        return self.by_id[user_id]


class BaseGroup(BaseModel):
    """User Group Model"""

    id: str = Field(..., description="The unique identifier of the group.")
    name: str = Field(..., description="The name of the group.")


class Group(BaseGroup):
    """User Group Model with Subgroups"""

    subgroups: Optional[List["Group"]] = Field(
        None, description="A list of subgroups."
    )


class GroupListBase(list):
    """Base class for GroupList with utility methods."""

    def __repr__(self) -> str:
        """String representation of the GroupList."""
        return str(self)

    def __str__(self):
        """Pretty print the GroupList"""
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
                    BaseGroup(**group.model_dump(exclude={"subgroups"}))
                )
                if group.subgroups:
                    _flatten(group.subgroups)

        _flatten(self)
        return GroupListBase(flat_list)

    @property
    def by_id(self) -> dict[str, Group]:
        """Return a dictionary of groups indexed by their ID."""
        return {group.id: group for group in self.flat}

    @property
    def by_name(self) -> dict[str, Group]:
        """Return a dictionary of groups indexed by their name."""
        return {group.name: group for group in self.flat}


Group.model_rebuild()

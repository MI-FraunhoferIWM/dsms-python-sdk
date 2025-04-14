"""UserGroup property of a KItem"""

from pydantic import BaseModel, Field

from dsms.knowledge.utils import print_model


class UserGroup(BaseModel):
    """Users groups related to a KItem."""

    name: str = Field(
        ..., description="Name of the user group", max_length=100
    )
    group_id: str = Field(
        ..., description="ID of the user group", max_length=100
    )

    # OVERRIDE
    def __str__(self):
        return print_model(self, "user_group")

    # OVERRIDE
    def __repr__(self) -> str:
        return str(self)

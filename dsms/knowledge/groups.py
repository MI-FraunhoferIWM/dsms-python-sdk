"""DSMS User Groups Module."""

from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class Group(BaseModel):
    """User Group Model"""

    id: UUID = Field(..., description="The unique identifier of the group.")
    name: str = Field(..., description="The name of the group.")
    subgroups: Optional[List["Group"]] = Field(
        None, description="A list of subgroups."
    )


Group.model_rebuild()

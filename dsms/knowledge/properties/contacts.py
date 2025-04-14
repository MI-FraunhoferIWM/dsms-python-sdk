"""Contacts  property of a KItem"""


from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field, field_serializer

from dsms.knowledge.utils import print_model


class ContactInfo(BaseModel):
    """Contact info"""

    name: str = Field(..., description="Name of the contact person")
    email: str = Field(..., description="EMail of the contact person")
    user_id: Optional[UUID] = Field(
        None, description="User ID of the contact person"
    )

    @field_serializer("user_id")
    def serialize_user_id(self, value: UUID) -> str:
        """
        Serialize the user_id of the contact to a string.

        Args:
            value: the UUID of the user_id

        Returns:
            str: the serialized user_id
        """
        return str(value)

    # OVERRIDE
    def __str__(self) -> str:
        return print_model(self, "contact")

    def __repr__(self) -> str:
        return self.__str__()

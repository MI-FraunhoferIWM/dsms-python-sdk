"""Author property of a KItem"""

from uuid import UUID

from pydantic import BaseModel, Field, field_serializer

from dsms.knowledge.utils import print_model


class Author(BaseModel):
    """Author of a KItem."""

    user_id: UUID = Field(
        ...,
        description="ID of the DSMS User",
    )

    @field_serializer("user_id")
    def serialize_user_id(self, value: UUID) -> str:
        """
        Serialize the user_id to a string.

        Args:
            value (UUID): The UUID of the user_id to be serialized.

        Returns:
            str: The serialized user_id as a string.
        """

        return str(value)

    # OVERRIDE
    def __str__(self):
        return print_model(self, "author")

    # OVERRIDE
    def __repr__(self) -> str:
        return str(self)

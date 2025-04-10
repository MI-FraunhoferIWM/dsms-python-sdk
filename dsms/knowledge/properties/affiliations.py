"""Affiliation property of a KItem"""

from pydantic import BaseModel, Field

from dsms.knowledge.utils import print_model


class Affiliation(BaseModel):
    """Affiliation of a KItem."""

    name: str = Field(
        ..., description="Name of the affiliation", max_length=100
    )

    # OVERRIDE
    def __str__(self) -> str:
        return print_model(self, "affiliation")

    # OVERRIDE
    def __repr__(self) -> str:
        return str(self)

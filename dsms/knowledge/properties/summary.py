"""Summary of a KItem"""

from pydantic import BaseModel, Field, model_serializer

from dsms.knowledge.utils import print_model


class Summary(BaseModel):
    """Model for the custom properties of the KItem"""

    text: str = Field(..., description="Summary text of the KItem")

    # OVERIDE
    def __str__(self):
        return print_model(self, "summary")

    # OVERIDE
    def __repr__(self) -> str:
        """Pretty print the custom properties"""
        return str(self)

    def __hash__(self) -> int:
        return hash(str(self))

    @model_serializer
    def serialize(self) -> str:
        """Serialize the summary model"""
        return self.text

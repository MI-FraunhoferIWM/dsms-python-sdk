"""ExternalLink property of a KItem"""

from typing import Union

from pydantic import AnyUrl, BaseModel, Field, field_validator

from dsms.knowledge.utils import print_model


class ExternalLink(BaseModel):
    """External link of a KItem."""

    label: str = Field(
        ..., description="Label of the external link", max_length=50
    )
    url: Union[str, AnyUrl] = Field(
        ..., description="URL of the external link"
    )

    # OVERRIDE
    def __str__(self):
        return print_model(self, "external_link")

    # OVERRIDE
    def __repr__(self) -> str:
        return str(self)

    @field_validator("url")
    @classmethod
    def validate_url(cls, value: Union[str, AnyUrl]) -> AnyUrl:
        """
        Validate and convert the URL to a string.

        This method is a model validator that runs after the model is initialized.
        It ensures that the `url` field of the `ExternalLink` is a string.
        If it is not, it attempts to convert it to a string.

        Args:
            value (Union[str, AnyUrl]): The value to be validated and converted.

        Returns:
            AnyUrl: The validated and potentially modified URL.
        """
        if isinstance(value, AnyUrl):
            value = str(value)
        return value

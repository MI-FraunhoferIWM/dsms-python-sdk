"""ExternalLink property of a KItem"""

from typing import TYPE_CHECKING, Union

from pydantic import AnyUrl, Field, field_validator

from dsms.knowledge.properties.base import KItemProperty, KItemPropertyList
from dsms.knowledge.utils import print_model

if TYPE_CHECKING:
    from typing import Callable


class ExternalLink(KItemProperty):
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


class ExternalLinksProperty(KItemPropertyList):
    """KItemPropertyList for external links"""

    # OVERRIDE
    @property
    def k_property_item(self) -> "Callable":
        return ExternalLink

    # OVERRIDE
    @property
    def k_property_helper(self) -> None:
        """Not defined for External links"""

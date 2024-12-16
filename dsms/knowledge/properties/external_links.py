"""ExternalLink property of a KItem"""

from typing import TYPE_CHECKING

from pydantic import AnyUrl, Field

from dsms.knowledge.properties.base import KItemProperty, KItemPropertyList
from dsms.knowledge.utils import print_model

if TYPE_CHECKING:
    from typing import Callable


class ExternalLink(KItemProperty):
    """External link of a KItem."""

    label: str = Field(
        ..., description="Label of the external link", max_length=50
    )
    url: AnyUrl = Field(..., description="URL of the external link")

    # OVERRIDE
    def __str__(self):
        return print_model(self, "external_link")


class ExternalLinksProperty(KItemPropertyList):
    """KItemPropertyList for external links"""

    # OVERRIDE
    @property
    def k_property_item(cls) -> "Callable":
        return ExternalLink

    # OVERRIDE
    @property
    def k_property_helper(cls) -> None:
        """Not defined for External links"""

"""ExternalLink KProperty"""

from typing import TYPE_CHECKING

from pydantic import AnyUrl, Field

from dsms.knowledge.properties.base import KProperty, KPropertyItem

if TYPE_CHECKING:
    from typing import Callable


class ExternalLink(KPropertyItem):
    """External link of a KItem."""

    label: str = Field(..., description="Label of the external link")
    url: AnyUrl = Field(..., description="URL of the external link")


class ExternalLinksProperty(KProperty):
    """KProperty for external links"""

    # OVERRIDE
    @property
    def k_property_item(cls) -> "Callable":
        return ExternalLink

    # OVERRIDE
    @property
    def k_property_helper(cls) -> None:
        """Not defined for External links"""

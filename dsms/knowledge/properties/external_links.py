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
    def _add(self, item: ExternalLink) -> ExternalLink:
        """Side effect when an ExternalLink is added to the KProperty"""
        return item

    # OVERRIDE
    def _update(self, item: ExternalLink) -> ExternalLink:
        """Side effect when an ExternalLink is updated at the KProperty"""
        return item

    # OVERRIDE
    def _get(self, item: ExternalLink) -> ExternalLink:
        """Side effect when getting the ExternalLink for a specfic kitem"""
        return item

    # OVERRIDE
    def _delete(self, item: ExternalLink) -> None:
        """Side effect when deleting the ExternalLink of a KItem"""

"""Affiliation KProperty"""

from typing import TYPE_CHECKING

from pydantic import Field

from dsms.knowledge.properties.base import KProperty, KPropertyItem

if TYPE_CHECKING:
    from typing import Callable


class Affiliation(KPropertyItem):
    """Affiliation of a KItem."""

    name: str = Field(..., description="Name of the affiliation")


class AffiliationsProperty(KProperty):
    """Affiliations property"""

    # OVERRIDE
    @property
    def k_property_item(cls) -> "Callable":
        return Affiliation

    # OVERRIDE
    def _add(self, item: Affiliation) -> Affiliation:
        """Side effect when an affiliation is added to the KProperty"""
        return item

    # OVERRIDE
    def _update(self, item: Affiliation) -> Affiliation:
        """Side effect when an affiliation is updated at the KProperty"""
        return item

    # OVERRIDE
    def _get(self, item: Affiliation) -> Affiliation:
        """Side effect when getting the affiliation for a specfic kitem"""
        return item

    # OVERRIDE
    def _delete(self, item: Affiliation) -> None:
        """Side effect when deleting the affiliation of a KItem"""

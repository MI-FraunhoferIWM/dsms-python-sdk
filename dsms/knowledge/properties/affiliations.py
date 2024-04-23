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

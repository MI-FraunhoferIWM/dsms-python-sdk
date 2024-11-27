"""Affiliation property of a KItem"""

from typing import TYPE_CHECKING

from pydantic import Field

from dsms.knowledge.properties.base import KItemProperty, KItemPropertyList
from dsms.knowledge.properties.utils import _str_to_dict

if TYPE_CHECKING:
    from typing import Callable


class Affiliation(KItemProperty):
    """Affiliation of a KItem."""

    name: str = Field(
        ..., description="Name of the affiliation", max_length=100
    )


class AffiliationsProperty(KItemPropertyList):
    """Affiliations property"""

    # OVERRIDE
    @property
    def k_property_item(cls) -> "Callable":
        return Affiliation

    @property
    def k_property_helper(cls) -> "Callable":
        """Affiliation property helper"""
        return _str_to_dict

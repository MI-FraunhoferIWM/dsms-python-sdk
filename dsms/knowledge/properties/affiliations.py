"""Affiliation property of a KItem"""

from typing import TYPE_CHECKING

from pydantic import Field

from dsms.knowledge.properties.base import KItemProperty, KItemPropertyList
from dsms.knowledge.properties.utils import _str_to_dict
from dsms.knowledge.utils import print_model

if TYPE_CHECKING:
    from typing import Callable


class Affiliation(KItemProperty):
    """Affiliation of a KItem."""

    name: str = Field(
        ..., description="Name of the affiliation", max_length=100
    )

    # OVERRIDE
    def __str__(self) -> str:
        return print_model(self, "affiliation")


class AffiliationsProperty(KItemPropertyList):
    """Affiliations property"""

    # OVERRIDE
    @property
    def k_property_item(self) -> "Callable":
        return Affiliation

    @property
    def k_property_helper(self) -> "Callable":
        """Affiliation property helper"""
        return _str_to_dict

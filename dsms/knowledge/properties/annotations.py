"""Annotation property of a KItem"""

from typing import TYPE_CHECKING, Optional

from pydantic import Field

from dsms.knowledge.properties.base import KItemProperty, KItemPropertyList
from dsms.knowledge.utils import _make_annotation_schema

if TYPE_CHECKING:
    from typing import Any, Callable, Dict


class Annotation(KItemProperty):
    """KItem annotation model"""

    iri: str = Field(..., description="IRI of the annotation")
    name: str = Field(..., description="Name of the annotation")
    namespace: str = Field(..., description="Namespace of the annotation")
    description: Optional[str] = Field(
        None, description="Description of the annotation"
    )


class AnnotationsProperty(KItemPropertyList):
    """KItemPropertyList for annotations"""

    # OVERRIDE
    @property
    def k_property_item(cls) -> "Callable":
        """Annotation data model"""
        return Annotation

    @property
    def k_property_helper(cls) -> None:
        """Not defined for Affiliations"""
        return _make_annotation_schema

    @property
    def by_iri(cls) -> "Dict[str, Any]":
        """Return dict of annotations per IRI"""
        return {annotation.iri for annotation in cls}

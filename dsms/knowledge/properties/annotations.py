"""Annotation property of a KItem"""

from typing import TYPE_CHECKING

from pydantic import Field

from dsms.knowledge.properties.base import KItemProperty, KItemPropertyList
from dsms.knowledge.utils import _make_annotation_schema

if TYPE_CHECKING:
    from typing import Any, Callable, Dict


class Annotation(KItemProperty):
    """KItem annotation model"""

    iri: str = Field(..., description="IRI of the annotation", max_length=200)
    label: str = Field(
        ..., description="Label of the annotation", max_length=100
    )
    namespace: str = Field(
        ..., description="Namespace of the annotation", max_length=100
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
        return {annotation.iri: annotation for annotation in cls}

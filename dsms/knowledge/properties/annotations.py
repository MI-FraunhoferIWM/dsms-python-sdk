"""Annotations KProperty"""

from typing import TYPE_CHECKING

from pydantic import Field

from dsms.knowledge.properties.base import KProperty, KPropertyItem
from dsms.knowledge.utils import _make_annotation_schema

if TYPE_CHECKING:
    from typing import Any, Callable, Dict


class Annotation(KPropertyItem):
    """KItem annotation model"""

    iri: str = Field(..., description="IRI of the annotation")
    name: str = Field(..., description="Name of the annotation")
    namespace: str = Field(..., description="Namespace of the annotation")


class AnnotationsProperty(KProperty):
    """KProperty for annotations"""

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

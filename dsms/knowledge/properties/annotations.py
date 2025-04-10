"""Annotation property of a KItem"""

from typing import TYPE_CHECKING

from pydantic import BaseModel, Field

from dsms.knowledge.utils import print_model

if TYPE_CHECKING:
    from typing import Any, Dict


class Annotation(BaseModel):
    """KItem annotation model"""

    iri: str = Field(..., description="IRI of the annotation", max_length=200)
    label: str = Field(
        ..., description="Label of the annotation", max_length=100
    )
    namespace: str = Field(
        ..., description="Namespace of the annotation", max_length=100
    )

    # OVERRIDE
    def __str__(self) -> str:
        return print_model(self, "annotation")

    # OVERRIDE
    def __repr__(self) -> str:
        return str(self)


class AnnotationList(list):
    """KItemPropertyList for Annotations"""

    @property
    def by_iri(self) -> "Dict[str, Any]":
        """Return dict of annotations per IRI"""
        return {annotation.iri: annotation for annotation in self}

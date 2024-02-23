"""Annotations KProperty"""

from typing import TYPE_CHECKING

from pydantic import Field

from dsms.knowledge.properties.base import KProperty, KPropertyItem

if TYPE_CHECKING:
    from typing import Callable


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

    # OVERRIDE
    def _add(self, item: Annotation) -> Annotation:
        """Side effect when an Annotation is added to the KProperty"""
        return item

    # OVERRIDE
    def _update(self, item: Annotation) -> Annotation:
        """Side effect when an Annotation is updated at the KProperty"""
        return item

    # OVERRIDE
    def _delete(self, item: Annotation) -> None:
        """Side effect when deleting the Annotation of a KItem"""

    # OVERRIDE
    def _get(self, item: Annotation) -> Annotation:
        """Side effect when getting the Annotation for a specfic kitem"""
        return item

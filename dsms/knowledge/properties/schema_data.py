"""KItem Schema Data property model"""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class KItemSchemaData(BaseModel):
    """Holds the semantic schema data associated with a KItem.

    Each entry maps a schema ID (e.g. an ontology class IRI) to a free-form
    content dict that stores the instance data for that schema.
    """

    schema_id: str = Field(
        ..., description="Schema identifier (e.g. an ontology class IRI)."
    )
    content: Optional[Dict[str, Any]] = Field(
        None, description="Instance data for the schema."
    )


class KItemSchemaDataList(List[KItemSchemaData]):
    """Typed list of KItemSchemaData entries with lookup by schema_id."""

    @property
    def by_schema_id(self) -> "Dict[str, KItemSchemaData]":
        """Return a dict keyed by schema_id."""
        return {entry.schema_id: entry for entry in self}

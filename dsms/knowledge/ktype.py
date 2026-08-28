"""KItem types"""

import logging
from datetime import datetime
from typing import TYPE_CHECKING, Any, Dict, List, Literal, Optional, Union
from uuid import UUID

from pydantic import BaseModel, Field, field_validator

from dsms.core.logging import handler
from dsms.core.session import Session
from dsms.knowledge.utils import _refresh_ktype, print_ktype, print_model
from dsms.knowledge.webform import BaseWebformModel

if TYPE_CHECKING:
    from dsms import DSMS


logger = logging.getLogger(__name__)
logger.addHandler(handler)
logger.propagate = False


class KTypeMapping(BaseWebformModel):
    """KType mapping for process schema specification"""

    dst_ktype_id: str = Field(
        ..., description="The ID of the destination K-type"
    )
    relation_iri: str = Field(..., description="The IRI of the relation")
    relation_name: str = Field(..., description="The name of the relation")


class ProcessSchemaSpec(BaseWebformModel):
    """Process schema specification"""

    id: Optional[Union[str, UUID]] = Field(
        None, description="ID of the process schema spec"
    )
    label: str = Field(..., description="The label of the process schema spec")
    is_child: bool = Field(
        False, description="Indicates if it is a child element"
    )
    mappings: List[KTypeMapping] = Field(
        [], description="List of associated KTypeMappings"
    )
    children: List[Optional["ProcessSchemaSpec"]] = Field(
        [], description="Nested child ProcessSchemaSpecs"
    )
    required: bool = Field(
        False, description="Whether this step is mandatory"
    )
    cardinality: Literal["one", "many"] = Field(
        "one", description="'one' = at most one KItem per step; 'many' = unlimited KItems per step"
    )

    @field_validator("id")
    @classmethod
    def _validate_uuid(cls, value: Union[str, UUID]) -> str:
        return str(value)


class ProcessSchema(BaseModel):
    """Process Schema of the KType"""

    id: Optional[Union[str, UUID]] = Field(
        None, description="ID of the process schema"
    )
    name: str = Field(..., description="Name of the process schema")
    spec: List[ProcessSchemaSpec] = Field(
        ..., description="Schema of the process schema"
    )
    created_at: Optional[datetime] = Field(
        None, description="Time and date when the process schema was created."
    )
    updated_at: Optional[datetime] = Field(
        None, description="Time and date when the process schema was updated."
    )
    def refresh(self) -> None:
        """Refresh the process schema"""
        new = self.session.dsms.process_schemas.get(self.id)
        if not new:
            return
        for key, value in new.model_dump().items():
            logger.debug(
                "Set updated property `%s` for ProcessSchema with id `%s` after commiting: %s",
                key,
                self.id,
                value,
            )
            setattr(self, key, value)

    @property
    def dsms(self) -> "DSMS":
        """DSMS session getter"""
        return self.session.dsms

    @property
    def session(self) -> "Session":
        """Getter for Session"""
        return Session

    def __hash__(self) -> int:
        return hash(str(self))

    def __repr__(self) -> str:
        """Print the KType"""
        return str(self)

    def __str__(self) -> str:
        """Print the KType"""
        return print_model(self, "process_schema")

    @field_validator("id")
    @classmethod
    def _validate_uuid(cls, value: Union[str, UUID]) -> str:
        return str(value)


class KType(BaseModel):
    """Knowledge type of the knowledge item."""

    id: Union[UUID, str] = Field(
        ..., description="ID of the KType.", max_length=50
    )
    name: Optional[str] = Field(
        None, description="Human readable name of the KType.", max_length=50
    )
    custom_properties: Optional[Dict[str, Any]] = Field(
        None, description="Custom properties spec (camelCase dict) for this KType."
    )
    process_schema_id: Optional[str] = Field(
        None,
        description="ID of the process schema that is used to create a form for this KType.",
    )
    process_schema: Optional[ProcessSchema] = Field(
        None, description="Process schema of the KType."
    )
    created_at: Optional[Union[str, datetime]] = Field(
        None, description="Time and date when the KType was created."
    )
    updated_at: Optional[Union[str, datetime]] = Field(
        None, description="Time and date when the KType was updated."
    )

    def __hash__(self) -> int:
        return hash(str(self))

    def __repr__(self) -> str:
        """Print the KType"""
        return str(self)

    def __str__(self) -> str:
        """Print the KType"""
        return print_ktype(self)

    def refresh(self) -> None:
        """Refresh the KType"""
        _refresh_ktype(self)

    @property
    def dsms(self) -> "DSMS":
        """DSMS session getter"""
        return self.session.dsms

    @property
    def session(self) -> "Session":
        """Getter for Session"""
        return Session


# ---------------------------------------------------------------------------
# KType v2 — semantic-spec sub-models
# ---------------------------------------------------------------------------


class OntologyClassSpec(BaseModel):
    """A single ontology class associated with a KType."""

    iri: str = Field(..., description="IRI of the ontology class.")
    label: str = Field(..., description="Human-readable label.")
    ontology: str = Field(..., description="Ontology the class belongs to.")


class SemanticSchemaRef(BaseModel):
    """Reference to a semantic schema linked to a KType."""

    id: str = Field(..., description="Schema identifier.")
    version: str = Field(..., description="Schema version string.")
    url: str = Field(..., description="URL to the schema definition.")


class RelationSpec(BaseModel):
    """A typed relation defined on a KType."""

    id: str = Field(..., description="Relation identifier.")
    label: str = Field(..., description="Human-readable label.")
    description: Optional[str] = Field(
        None, description="Optional description."
    )
    iri: str = Field(..., description="IRI of the relation property.")
    target_k_types: List[str] = Field(
        [], description="KType IDs that are valid targets for this relation."
    )
    cardinality: str = Field(
        "0..n", description="Cardinality string, e.g. '0..n'."
    )
    required: bool = Field(
        False, description="Whether the relation is required."
    )


class KTypeSpec(BaseModel):
    """Semantic specification record for a v2 KType (ktype_spec table)."""

    ktype_id: str = Field(..., description="KType ID this spec belongs to.")
    format_version: Optional[str] = Field(
        None, description="Spec format version, e.g. '0.1'."
    )
    spec_id: Optional[str] = Field(
        None, description="$id field from the spec YAML."
    )
    version: Optional[str] = Field(
        None, description="Semver string, e.g. '1.0.0'."
    )
    description: Optional[str] = Field(None)
    abstract: Optional[bool] = Field(
        None,
        description="If True the KType cannot be instantiated (no KItems allowed).",
    )
    context: Optional[bool] = Field(
        None, description="If True the KType can act as a context anchor."
    )
    context_member_types: Optional[List[str]] = Field(
        None,
        description="KType IDs allowed as members of a context of this type.",
    )
    synonyms: Optional[List[str]] = Field(None)
    extends: Optional[Union[str, List[str]]] = Field(
        None, description="Parent KType ID(s) for inheritance."
    )
    ontology_classes: Optional[List[OntologyClassSpec]] = Field(
        None, description="Ontology classes defined directly on this KType."
    )
    resolved_ontology_classes: Optional[List[OntologyClassSpec]] = Field(
        None, description="Ontology classes including inherited entries."
    )
    semantic_schemas: Optional[List[SemanticSchemaRef]] = Field(
        None,
        description="Semantic schema references defined directly on this KType.",
    )
    resolved_semantic_schemas: Optional[List[SemanticSchemaRef]] = Field(
        None,
        description="Semantic schema references including inherited entries.",
    )
    relations: Optional[List[RelationSpec]] = Field(None)
    custom_properties: Optional[Dict[str, Any]] = Field(
        None, description="Custom properties spec dict (camelCase)."
    )
    tags: Optional[List[str]] = Field(None)
    source_url: Optional[str] = Field(
        None, description="GitHub URL if the spec was imported."
    )
    has_stash: bool = Field(
        False, description="Whether a pre-import stash exists for this KType."
    )
    stashed_spec_version: Optional[str] = Field(
        None, description="Version string from the stash, if any."
    )
    created_at: Optional[datetime] = Field(None)
    updated_at: Optional[datetime] = Field(None)


class KTypeV2(KType):
    """KType returned by the v2 knowledge-type-service endpoints.

    Extends the base KType with an optional semantic spec.
    """

    spec: Optional[KTypeSpec] = Field(
        None,
        description="Semantic specification of this KType. None for v1-only KTypes.",
    )


# ---------------------------------------------------------------------------
# KType v2 — request models
# ---------------------------------------------------------------------------


class CreateKTypeRequest(BaseModel):
    """Request body for POST /api/knowledge-type/ — create or upgrade a KType."""

    id: str = Field(
        ...,
        description="KType ID (slug, e.g. 'my-ktype').",
        min_length=2,
        max_length=60,
        pattern=r"^[a-z][a-z0-9-]*$",
    )
    name: str = Field(..., min_length=2, max_length=100)
    format_version: str = Field("0.1")
    version: str = Field("1.0.0")
    description: Optional[str] = Field(None)
    abstract: bool = Field(False)
    context: bool = Field(False)
    context_member_types: Optional[List[str]] = Field(None)
    synonyms: Optional[List[str]] = Field(None)
    extends: Optional[Union[str, List[str]]] = Field(None)
    ontology_classes: Optional[List[OntologyClassSpec]] = Field(None)
    semantic_schemas: Optional[List[SemanticSchemaRef]] = Field(None)
    relations: Optional[List[RelationSpec]] = Field(None)
    custom_properties: Optional[Dict[str, Any]] = Field(None)
    tags: Optional[List[str]] = Field(None)


class ImportFromUrlRequest(BaseModel):
    """Request body for POST /api/knowledge-type/import — import a spec from a GitHub URL."""

    url: str = Field(..., description="URL to the raw ktype.yaml on GitHub.")


class KTypeSpecPayload(BaseModel):
    """Request body for PUT /api/knowledge-type/{ktype_id} — partial spec update."""

    name: Optional[str] = Field(None, min_length=2, max_length=100)
    version: Optional[str] = Field(None)
    description: Optional[str] = Field(None)
    abstract: Optional[bool] = Field(None)
    context: Optional[bool] = Field(None)
    context_member_types: Optional[List[str]] = Field(None)
    synonyms: Optional[List[str]] = Field(None)
    extends: Optional[Union[str, List[str]]] = Field(None)
    ontology_classes: Optional[List[OntologyClassSpec]] = Field(None)
    semantic_schemas: Optional[List[SemanticSchemaRef]] = Field(None)
    relations: Optional[List[RelationSpec]] = Field(None)
    custom_properties: Optional[Dict[str, Any]] = Field(None)
    tags: Optional[List[str]] = Field(None)


# ---------------------------------------------------------------------------
# KType v2 — response models
# ---------------------------------------------------------------------------


class RemoteKTypeSummary(BaseModel):
    """Summary of a KType available in the remote GitHub repository."""

    id: str
    name: str
    remote_version: str
    url: str
    status: str = Field(
        ...,
        description="One of: 'not_imported', 'up_to_date', 'update_available'.",
    )
    db_version: Optional[str] = Field(None)


class RemoteKTypeVersion(BaseModel):
    """A tagged version of a KType in the remote repository."""

    tag: str
    version: str
    url: str


class RemoteSchemaVersionInfo(BaseModel):
    """Version entry for a remote semantic schema."""

    version: str
    url: str


class RemoteSchemaInfo(BaseModel):
    """A semantic schema available in the remote repository."""

    id: str
    versions: List[RemoteSchemaVersionInfo] = Field([])


class SpecDiffField(BaseModel):
    """One changed field in a remote-diff result."""

    field: str
    local: Any
    remote: Any


class RemoteDiffOut(BaseModel):
    """Result of comparing a local KType spec against the latest remote version."""

    remote_version: str
    remote_url: str
    changed_fields: List[SpecDiffField] = Field([])
    identical: bool

"""Full Knowledge Item implementation of the DSMS"""

import logging
import warnings
from datetime import date, datetime
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Union
from urllib.parse import urljoin

import pandas as pd
from rdflib import Graph

from pydantic import (  # isort:skip
    BaseModel,
    AliasChoices,
    Field,
    ValidationInfo,
    field_validator,
    field_serializer,
    model_validator,
)

from dsms.core.logging import handler  # isort:skip

from dsms.core.session import Session  # isort:skip

from dsms.knowledge.compacted import (  # isort:skip
    KItemBaseModel,
    KItemCompactedModel,
)

from dsms.knowledge.properties import (  # isort:skip
    Affiliation,
    Annotation,
    AnnotationList,
    App,
    AppList,
    Avatar,
    Attachment,
    AttachmentList,
    Author,
    ContactInfo,
    ExternalLink,
    DataFrameContainer,
    Column,
    KItemRelationshipModel,
    KItemSchemaData,
    LinkedKItemsList,
    Summary,
    KItemAccessProperties,
)

from dsms.knowledge.ktype import KType  # isort:skip

from dsms.knowledge.utils import (  # isort:skip
    _inspect_dataframe,
    _make_annotation_schema,
    _refresh_kitem,
    _transform_custom_properties_schema,
    print_model,
    _map_data_type_to_widget,
)

from dsms.knowledge.sparql_interface.utils import _get_subgraph  # isort:skip

from dsms.knowledge.webform import (  # isort:skip
    Entry,
    Input,
    KItemCustomPropertiesModel,
    KnowledgeItemReference,
    WebformSelectOption,
    WebformSelectOptionEntry,
    Widget,
)

if TYPE_CHECKING:
    from dsms.core.dsms import DSMS

logger = logging.getLogger(__name__)
logger.addHandler(handler)
logger.propagate = False

DATETIME_FRMT = "%Y-%m-%dT%H:%M:%S.%f"


class KItem(KItemCompactedModel):
    """
    Knowledge Item of the DSMS.

    Attributes:
        name (str):
            Human readable name of the KItem
        id (Optional[UUID,str]):
            ID of the KItem. Defaults to a new UUID if not provided.
        ktype_id (Union[Enum, str]):
            Type ID of the KItem.
        slug (Optional[str]):
            Slug of the KItem. Minimum length: 4.
        annotations (List[Annotation]):
            Annotations of the KItem.
        attachments (List[Union[Attachment, str]]):
            File attachments of the DSMS.
        linked_kitems (List[Union[KItemRelationshipModel, "KItem"]]):
            KItems linked to the current KItem.
        affiliations (List[Affiliation]):
            Affiliations related to a KItem.
        authors (List[Union[Author, str]]):
            Authorship of the KItem.
        avatar_exists (Optional[bool]):
            Whether the KItem holds an avatar or not.
        contacts (List[ContactInfo]):
            Contact information related to the KItem.
        created_at (Optional[Union[str, datetime]]):
            Time and date when the KItem was created.
        updated_at (Optional[Union[str, datetime]]):
            Time and date when the KItem was updated.
        external_links (List[ExternalLink]):
            External links related to the KItem.
        apps (List[App]): Apps related to the KItem.
        summary (Optional[Union[str, Summary]]):
            Human readable summary text of the KItem.
        access_properties (Optional[KItemAccessProperties]):
                Access control configuration for the KItem.
        custom_properties (Optional[Any]):
            Custom properties associated with the KItem.
        dataframe (Optional[Union[List[Column], pd.DataFrame, Dict[str, Union[List, Dict]]]]):
            DataFrame interface.
        contexts (Optional[List[Union["KItem", KItemBaseModel, KItemCompactedModel]]])
            Context KItems related to the KItem.
    """

    # public

    annotations: List[Union[str, Annotation]] = Field(
        [], description="Annotations of the KItem"
    )
    attachments: List[Union[Attachment, str]] = Field(
        [],
        description="File attachements of the DSMS",
    )
    linked_kitems: List[Union[KItemRelationshipModel, "KItem"]] = Field(
        [],
        description="KItems linked to the current KItem.",
    )
    affiliations: List[Affiliation] = Field(
        [],
        description="Affiliations related to a KItem.",
    )
    authors: List[Union[Author, str]] = Field(
        [],
        description="Authorship of the KItem. Deprecated: no longer populated by the backend.",
        deprecated=True,
    )
    contacts: List[ContactInfo] = Field(
        [],
        description="Whether the KItem holds any contact information.",
    )
    created_at: Optional[Union[str, datetime]] = Field(
        None, description="Time and date when the KItem was created."
    )
    updated_at: Optional[Union[str, datetime]] = Field(
        None, description="Time and date when the KItem was updated."
    )
    external_links: List[ExternalLink] = Field(
        [],
        description="External links related to the KItem",
    )
    apps: List[App] = Field(
        [],
        description="Apps related to the KItem.",
        alias=AliasChoices("kitem_apps", "apps"),
    )
    summary: Optional[Union[str, Summary]] = Field(
        None, description="Human readable summary text of the KItem."
    )
    custom_properties: Optional[Union[KItemCustomPropertiesModel]] = Field(
        None, description="Custom properties associated to the KItem"
    )

    dataframe: Optional[
        Union[List[Column], pd.DataFrame, Dict[str, Union[List, Dict]]]
    ] = Field(None, description="DataFrame interface.")

    rdf_exists: bool = Field(
        False,
        description=(
            "Whether the KItem holds an RDF Graph or not. "
            "Deprecated: no longer populated by the backend."
        ),
        deprecated=True,
    )

    avatar: Optional[Avatar] = Field(
        default_factory=Avatar, description="KItem avatar interface"
    )

    access_properties: Optional[KItemAccessProperties] = Field(
        None, description="Access properties of the KItem"
    )

    contexts: List[Union["KItem", KItemCompactedModel, KItemBaseModel]] = (
        Field(
            [],
            description="Contextualized KItems related to this one.",
        )
    )

    schema_data: Optional[List[KItemSchemaData]] = Field(
        None,
        description="Semantic schema data entries associated with this KItem.",
    )

    def __init__(self, **kwargs: "Any") -> None:
        """Initialize the KItem"""

        logger.debug("Initialize KItem with model data: %s", kwargs)

        # set dsms instance if not already done
        if not self.dsms:
            raise ValueError(
                "DSMS instance not set. Please call DSMS() before initializing a KItem."
            )

        # initialize the kitem
        super().__init__(**kwargs)

        if str(self.id) not in self.dsms.session.kitems:
            self.dsms.session.kitems[str(self.id)] = self

        logger.debug("KItem initialization successful.")

    def __str__(self) -> str:
        """Pretty print the kitem fields"""
        return print_model(
            self, "kitem", exclude_extra=self.dsms.config.hide_properties
        )

    def __repr__(self) -> str:
        """Pretty print the kitem Fields"""
        return str(self)

    def __hash__(self) -> int:
        return hash(str(self))

    @field_validator("annotations", mode="before")
    @classmethod
    def validate_annotations_before(
        cls, value: List[Union[str, Annotation]]
    ) -> List[Annotation]:
        """Validate annotations Field"""
        return [
            (
                Annotation(**_make_annotation_schema(annotation))
                if isinstance(annotation, str)
                else annotation
            )
            for annotation in value
        ]

    @field_validator("annotations", mode="after")
    @classmethod
    def validate_annotations_after(
        cls, value: List[Annotation]
    ) -> AnnotationList:
        """Validate annotations Field"""
        return AnnotationList(value)

    @field_validator("attachments", mode="before")
    @classmethod
    def validate_attachments_before(
        cls, value: List[Union[str, Attachment]]
    ) -> List[Attachment]:
        """Validate attachments Field"""
        return [
            (
                Attachment(name=attachment)
                if isinstance(attachment, str)
                else attachment
            )
            for attachment in value
        ]

    @field_validator("attachments", mode="after")
    @classmethod
    def validate_attachments_after(
        cls, value: List[Attachment], info: ValidationInfo
    ) -> AttachmentList:
        """Validate attachments Field"""
        kitem_id = info.data["id"]
        if value:
            for attachment in value:
                attachment.id = kitem_id
        return AttachmentList(value)

    @field_validator("apps", mode="after")
    @classmethod
    def validate_apps(cls, value: List[App], info: ValidationInfo) -> AppList:
        """Validate apps Field"""
        kitem_id = info.data["id"]
        if value:
            for app in value:
                app.id = kitem_id
        return AppList(value)

    @field_validator("avatar", mode="after")
    @classmethod
    def validate_avatar(cls, value: Avatar, info: ValidationInfo) -> Avatar:
        """
        Validate avatar Field
        """
        kitem_id = info.data.get("id")
        if value:
            value.id = kitem_id
        return value

    @field_validator("linked_kitems", mode="before")
    @classmethod
    def validate_linked_kitems_list(
        cls,
        value: "List[Union[KItemRelationshipModel, KItem]]",
    ) -> List[KItemRelationshipModel]:
        """Validate each single kitem to be linked"""
        linked_kitems = []
        logger.debug("Found KItem to link: %s", value)

        for item in value:
            if isinstance(item, dict):
                item = KItemRelationshipModel(**item)
            elif isinstance(item, BaseModel) and not isinstance(item, cls):
                item = KItemRelationshipModel(**item.model_dump())
            elif isinstance(item, cls):
                warnings.warn(
                    f"Found a {type(item)} to be linked instead of an {KItemRelationshipModel}."
                    " Will link it with the default relationship 'dcterms:haspart'."
                )
                item = KItemRelationshipModel(kitem=item, label="Has Part")
            else:
                raise TypeError(
                    "Expected either a {KItemRelationshipModel} or a KItem to be linked."
                )
            linked_kitems.append(item)
        return linked_kitems

    @field_validator("linked_kitems", mode="after")
    @classmethod
    def validate_linked_kitems(
        cls,
        value: List[KItemRelationshipModel],
    ) -> LinkedKItemsList:
        """Validate the list out of linked KItems"""
        return LinkedKItemsList(value)

    @field_validator("created_at")
    @classmethod
    def validate_created(cls, value: str) -> Any:
        """Convert the str for `created_at` in to a `datetime`-object"""

        if isinstance(value, str):
            value = datetime.strptime(value, DATETIME_FRMT)
        return value

    @field_validator("updated_at")
    @classmethod
    def validate_updated(cls, value: str) -> Any:
        """Convert the str for `created_at` in to a `datetime`-object"""

        if isinstance(value, str):
            value = datetime.strptime(value, DATETIME_FRMT)
        return value

    @field_validator("summary")
    @classmethod
    def validate_summary(cls, value: Union[str, Summary]) -> Summary:
        """Check whether the summary is a string or the dedicated model"""
        if isinstance(value, str):
            value = Summary(text=value)
        return value

    @field_validator("dataframe")
    @classmethod
    def validate_dataframe(
        cls,
        value: Optional[
            Union[List[Column], pd.DataFrame, Dict[str, Dict[Any, Any]]]
        ],  # pylint: disable=unused-argument
        info: ValidationInfo,
    ) -> DataFrameContainer:
        """Get DataFrame container if it exists."""
        kitem_id = info.data.get("id")
        if isinstance(value, (pd.DataFrame, dict)):
            if isinstance(value, pd.DataFrame):
                dataframe = value.copy(deep=True)
            else:
                dataframe = pd.DataFrame.from_dict(value)
        else:
            columns = _inspect_dataframe(Session.dsms, kitem_id)
            logger.debug("Found columns: %s", columns)
            if columns:
                dataframe = DataFrameContainer(
                    [Column(id=kitem_id, **column) for column in columns]
                )
            else:
                dataframe = None
        return dataframe

    @field_validator("custom_properties", mode="before")
    @classmethod
    def validate_custom_properties(
        cls,
        value: Optional[Union[KItemCustomPropertiesModel, Dict[str, Any]]],
        info: ValidationInfo,
    ) -> "Optional[KItemCustomPropertiesModel]":
        """Validate custom properties"""

        kitem_id = info.data["id"]
        ktype = info.data["ktype"]

        logger.debug("Received custom properties: %s", value)

        if isinstance(value, dict):
            logger.debug(
                "Converting custom properties to KItemCustomPropertiesModel"
            )
            value = value.get("content") or value
            if not isinstance(value, dict):
                raise TypeError(
                    "Custom properties must be either a dictionary or a "
                    "KItemCustomPropertiesModel. Not a "
                    f"{type(value)}: {value}"
                )
            if not value.get("sections"):
                warnings.warn(
                    """A flat dictionary was provided for custom properties.
                    Will be transformed into `KItemCustomPropertiesModel`."""
                )
                value = _transform_custom_properties_schema(
                    value, ktype.custom_properties
                )
            value = KItemCustomPropertiesModel(**value)
        elif not isinstance(value, (KItemCustomPropertiesModel, type(None))):
            raise TypeError(
                "Custom properties must be either a dictionary or a "
                "KItemCustomPropertiesModel. Not a "
                f"{type(value)}: {value}"
            )
        if value:
            if len(value.sections) == 0:
                warnings.warn(
                    "No sections were found in the custom properties. "
                    "Will be set to None."
                )
                value = None
            for section in value.sections:
                for entry in section.entries:
                    entry.kitem_id = kitem_id
                    cls.validate_custom_property_entry(entry, ktype)
        return value

    @field_validator("schema_data", mode="before")
    @classmethod
    def _coerce_schema_data(
        cls,
        value: "Optional[Any]",
    ) -> "Optional[Any]":
        """Accept a plain dict ``{schema_id: simplified_input}`` as shorthand."""
        if isinstance(value, dict):
            return [
                {"schema_id": sid, "content": {"__simplified__": data}}
                for sid, data in value.items()
            ]
        return value

    @model_validator(mode="after")
    def _resolve_schema_data_shorthands(self) -> "KItem":
        """Immediately resolve any ``{schema_id: simplified_input}`` shorthands.

        After all field validators have run, the DSMS session is available via
        :attr:`dsms`.  Any ``schema_data`` entry whose content carries the
        ``__simplified__`` sentinel is transformed to OO-LD here, so that
        ``schema_data`` always contains valid OO-LD by the time the caller
        receives the constructed object.
        """
        if not self.schema_data:
            return self
        pending = [
            (entry.schema_id, entry.content["__simplified__"])
            for entry in self.schema_data
            if isinstance(entry.content, dict)
            and "__simplified__" in entry.content
        ]
        for schema_id, input_data in pending:
            self.populate_schema(schema_id, input_data)
        return self

    @field_validator("contexts")
    def _validate_contexts(
        cls,
        value: Optional[
            List[Union["KItem", KItemBaseModel, KItemCompactedModel]]
        ],
    ) -> List[Optional[KItemCompactedModel]]:
        """
        Ensure that all items in the contexts list are instances of the `KItemCompactModel`.
        Accepted class instances such as `KItem` or `KItemBaseModel` will be transformed into
        an instance of `KItemCompactedModel`. If any item is not an instance of either class,
        raise a TypeError.
        Args:
            value (Optional[List[KItem, KItemBaseModel, KItemCompactedModel]]):
                The list of items to validate.
        Returns:
            List[KItemCompactedModel]: The validated list of items.
        Raises:
            TypeError: If any item in the contexts list is not an instance of either class.
        """

        if value is not None:
            new_list = []
            for item in value:
                if isinstance(  # pylint: disable=isinstance-second-argument-not-valid-type
                    item,
                    (cls, KItemBaseModel),
                ):
                    new_list += [KItemCompactedModel(**item.model_dump())]
                elif isinstance(item, KItemCompactedModel):
                    new_list += [item]
                else:
                    raise TypeError(f"Invalid item in contexts list: {item}")
            value = new_list
        return value

    @classmethod
    def validate_custom_property_entry(
        cls, entry: "Entry", ktype: "KType"
    ) -> "Entry":
        """
        Validate the custom property entries within a KItem.

        This method checks if the entry's configuration aligns with the defined
        webform specification for the corresponding knowledge type. It validates
        the entry type, default values, select options, and ensures the value
        conforms to the specified data type and constraints. Warnings or errors
        are raised if discrepancies are found, such as missing input specifications,
        invalid data types, or required values not being set.

        Args:
            entry (Entry): The custom property entry to validate.

        Returns:
            Entry: The validated entry with updated type and value information.

        Raises:
            ValueError: If the entry's configuration does not match the webform
                        specification or if the entry's value is invalid.
        """

        spec: list = []
        if ktype.custom_properties:  # pylint: disable=no-member
            for section in ktype.custom_properties.get("sections", []):  # pylint: disable=no-member
                for inp in section.get("inputs", []):
                    if inp.get("id") == entry.id:
                        spec.append(inp)

        logger.debug("Entry label: %s", entry.label)
        logger.debug("Entry value: %s", entry.value)

        # in this case we assume that custom_properties was defined for
        # the knowledge type for this specific entry
        if spec:
            logger.debug("Found input spec for entry: %s", entry.label)
            if len(spec) == 0:
                raise ValueError(
                    f"Could not find input spec for entry {entry.label}"
                )
            if len(spec) > 1:
                raise ValueError(
                    f"Found multiple input specs for entry {entry.label}"
                )
            spec = spec.pop()
            entry.type = spec.get("widget")
            default_value = None
            select_options = []
            range_options = None
            knowledge_type = None
            is_list = False
            dtype = None
            logger.debug("Widget type from spec: %s", entry.type)
        # in this case we assume that a webform was not defined
        # but the user explicitly set the widget type
        # this might be e.g. the case when a kitem without a webform
        # is pulled from the remote backend
        elif entry.type and not spec:
            logger.debug("Did not find input spec for entry: %s", entry.label)
            logger.debug("Using user-provided widget type: %s", entry.type)
            default_value = None
            select_options = []
            knowledge_type = None
            is_list = None
            dtype = None
        # in this case we assume that a webform was not defined
        # and the user did not explicitly set the widget type
        # this might be e.g. the case when a new kitem is instanciated
        # in the session by a flat dict (e.g. {"foo": "bar"})
        else:
            logger.debug("Did not find input spec for entry: %s", entry.label)
            entry.type, is_list, dtype = _map_data_type_to_widget(entry.value)
            logger.debug("Guessed widget type: %s", entry.type)
            default_value = None
            knowledge_type = None
            select_options = []

        logger.debug("Entry is_list: %s", is_list)
        if dtype:
            logger.debug("Guessed data type: %s", dtype)

        choices = {
            choice.label: choice.model_dump() for choice in select_options
        }
        logger.debug("Entry choices: %s", choices)

        # if the widget not is guessed from the data type,
        # check if widget is mapped to the correct data type
        if not dtype:
            logger.debug("Guessing data type from widget type")
            if entry.type in (
                Widget.TEXT.value,
                Widget.FILE.value,
                Widget.TEXTAREA.value,
            ):
                dtype = str
            elif entry.type in (Widget.NUMBER.value, Widget.SLIDER.value):
                dtype = (int, float)
            elif entry.type == Widget.CHECKBOX.value:
                dtype = bool
            elif entry.type == Widget.DATE.value:
                dtype = (str, date)
            elif entry.type == Widget.DATETIME.value:
                dtype = (str, datetime)
            elif entry.type in (
                Widget.SELECT.value,
                Widget.RADIO.value,
                Widget.MULTI_SELECT.value,
            ):
                if entry.type == Widget.MULTI_SELECT.value:
                    is_list = True
                dtype = WebformSelectOption
            elif entry.type == Widget.KNOWLEDGE_ITEM.value:
                dtype = (type(cls), KnowledgeItemReference, dict)
                is_list = True
            else:
                raise ValueError(
                    f"Widget type is not mapped to a data type: {entry.type}"
                )

            logger.debug("Guessed data type: %s", dtype)

        # check if value is set
        if entry.value is None and default_value is not None:
            logger.debug(
                "Value is not set, setting default value: %s", default_value
            )
            entry.value = default_value

        # check whether strict validation is enabled
        if Session.dsms.config.strict_validation:
            # special case for webform select options
            if (
                entry.type
                in (
                    Widget.SELECT.value,
                    Widget.RADIO.value,
                    Widget.MULTI_SELECT.value,
                )
                and entry.value is not None
            ):
                if not select_options:
                    raise ValueError(
                        f"Widget of type `{entry.type}` does not have select options."
                    )
                error_message = """Value `{}` is not a valid select option.
                Valid options are: """ + str(list(choices.keys())) + "\n"
                if isinstance(entry.value, str):
                    if entry.value not in choices:
                        raise ValueError(error_message.format(entry.value))
                    entry.value = WebformSelectOptionEntry(
                        **choices[entry.value], value=entry.value
                    )
                elif isinstance(entry.value, dict):
                    entry.value = WebformSelectOptionEntry(**entry.value)
                    if entry.value.label not in choices:
                        raise ValueError(
                            error_message.format(entry.value.label)
                        )

                elif isinstance(entry.value, list):
                    chosen = []
                    is_updated = False
                    for val in entry.value:
                        if isinstance(val, str):
                            if val not in choices:
                                raise ValueError(error_message.format(val))
                            val = WebformSelectOptionEntry(
                                **choices[val], value=val
                            )
                            is_updated = True
                        elif isinstance(val, dict):
                            val = WebformSelectOptionEntry(**val)
                            is_updated = True
                            if val.label not in choices:
                                raise ValueError(
                                    error_message.format(val.label)
                                )
                        elif not isinstance(val, WebformSelectOptionEntry):
                            raise ValueError(error_message.format(val))
                        chosen.append(val)
                    if is_updated:
                        entry.value = chosen
                elif not isinstance(entry.value, WebformSelectOptionEntry):
                    raise ValueError(error_message.format(entry.value))
                logger.debug("Value is set to: %s", entry.value)

            # check if value is of correct type
            error_message = "Value of type {} is invalid."
            if is_list is True:
                error_message += f"""
                Widget of type ´{entry.type}` is requiring a value of type:
                `List[{dtype}]`.
                """
                if entry.value is not None:
                    if not isinstance(entry.value, list):
                        raise ValueError(
                            error_message.format(type(entry.value), dtype)
                        )
                    for val in entry.value:
                        if not isinstance(val, dtype):
                            raise ValueError(
                                error_message.format(type(val), dtype)
                            )
            elif is_list is False:
                error_message += f"""
                Widget of type ´{entry.type}` is requiring a value of type:
                `{dtype}`."""
                if entry.value is not None and not isinstance(
                    entry.value, dtype
                ):
                    raise ValueError(
                        error_message.format(type(entry.value), dtype)
                    )
            else:
                warnings.warn(
                    f"No webform was defined for entry `{entry.label}`. "
                    "Cannot check if value is of correct type."
                )

            # check if value is required
            logger.debug("Checking if value is required")
            if (
                entry.value is None
                and default_value is None
                and entry.required
            ):
                raise ValueError(f"Value for entry {entry.label} is required")

            # special case for knowledge item
            if (
                entry.value is not None
                and entry.type == Widget.KNOWLEDGE_ITEM.value
            ):
                logger.debug("Checking if value is a valid knowledge item")
                kitems = []
                is_updated = False
                if not isinstance(entry.value, list):
                    raise ValueError(
                        f"""Value for entry `{entry.label}` for widget of type `knowledge item`
                        is not a list. Got {type(entry.value)}."""
                    )
                for val in entry.value:
                    if isinstance(val, dict):
                        val = KnowledgeItemReference(**val)
                        is_updated = True
                    if not isinstance(val, KnowledgeItemReference):
                        val = KnowledgeItemReference(
                            id=val.id,
                            name=val.name,
                            ktype_id=val.ktype_id,
                            slug=val.slug,
                        )
                        is_updated = True
                    if (
                        knowledge_type is not None
                        and val.ktype_id not in knowledge_type
                    ):
                        raise ValueError(
                            f"Knowledge item `{val.name}` is not of type {knowledge_type}."
                        )
                    kitems.append(val)
                if is_updated:
                    entry.value = kitems
        else:
            warnings.warn("""
                Strict validation is disabled.
                Will not strictly type check the custom properties.
                This also will take place when values are re-assigned.
                """)

        return entry

    @field_serializer("custom_properties")
    def _serialize_custom_properties(
        self, custom_properties: Optional[Any]
    ) -> Dict[str, Any]:
        if custom_properties is not None:
            serialized = {
                "content": custom_properties.model_dump(by_alias=True)
            }
        else:
            serialized = None
        return serialized

    @property
    def dsms(self) -> "DSMS":
        """DSMS session getter"""
        return self.session.dsms

    @property
    def subgraph(self) -> Optional[Graph]:
        """Getter for Subgraph"""
        return _get_subgraph(
            self.dsms, self.id, self.dsms.config.kitem_repo, is_kitem_id=True
        )

    @property
    def session(self) -> "Session":
        """Getter for Session"""
        return Session

    @property
    def url(self) -> str:
        """URL of the KItem"""
        return urljoin(
            str(self.session.dsms.config.host_url),
            f"knowledge/{self.ktype_id}/{self.slug}",
        )

    def is_a(self, to_be_compared: KType) -> bool:
        """Check the KType of the KItem"""
        return self.ktype.id == to_be_compared.id  # pylint: disable=no-member

    def refresh(self) -> None:
        """Refresh the KItem"""
        _refresh_kitem(self)

    def populate_schema(
        self, schema_id: str, input_data: "Dict[str, Any]"
    ) -> "KItem":
        """Populate a semantic schema instance on this KItem.

        Looks up *schema_id* in the k-type spec's ``resolved_semantic_schemas``
        list, fetches the schema's ``transform.simplified.jsonata`` file (if it
        exists), applies the transform to *input_data* to produce an OO-LD
        document, and stores the result in :attr:`schema_data`.

        For schemas **with** a ``transform.simplified.jsonata``, pass the
        schema's simplified input format in *input_data* (e.g. ``test_name``,
        ``specimen_iri``, ``results`` for ``characterization/tensile-test/TTO``).

        For schemas **without** a transform (e.g. ``dataset/generic/DCAT``),
        pass OO-LD directly.

        Call :meth:`DSMS.add` and :meth:`DSMS.commit` afterwards to persist
        the schema data to the platform.

        Args:
            schema_id: Schema identifier exactly matching the ``id`` field in
                the k-type spec's ``semantic_schemas`` list, e.g.
                ``"characterization/tensile-test/TTO"``.
            input_data: Simplified input dict (schemas with transform) or OO-LD
                dict (schemas without transform).

        Returns:
            ``self`` to allow method chaining.

        Raises:
            ValueError: If *schema_id* is not listed in the k-type spec, or if
                the k-type has no v2 spec.
            RuntimeError: If the schema cannot be fetched or the transform fails.
        """
        from dsms.knowledge.semantics import schema_to_oold

        ktype_v2 = self.dsms.get_v2_ktype(str(self.ktype_id))
        if not ktype_v2 or not ktype_v2.spec:
            raise ValueError(
                f"K-type '{self.ktype_id}' has no v2 spec. "
                "Import or create the k-type spec before calling populate_schema()."
            )

        schemas = (
            ktype_v2.spec.resolved_semantic_schemas
            or ktype_v2.spec.semantic_schemas
            or []
        )
        schema_ref = next((s for s in schemas if s.id == schema_id), None)
        if schema_ref is None:
            valid = [s.id for s in schemas]
            raise ValueError(
                f"Schema ID '{schema_id}' is not listed in the k-type spec for "
                f"'{self.ktype_id}'. Available schema IDs: {valid}"
            )

        oold_doc = schema_to_oold(schema_ref.url, input_data)

        new_entry = KItemSchemaData(schema_id=schema_id, content=oold_doc)

        if self.schema_data is None:
            self.schema_data = [new_entry]
        else:
            existing_ids = [sd.schema_id for sd in self.schema_data]
            if schema_id in existing_ids:
                idx = existing_ids.index(schema_id)
                self.schema_data = list(self.schema_data)
                self.schema_data[idx] = new_entry
            else:
                self.schema_data = list(self.schema_data) + [new_entry]

        return self

"""Knowledge Item implementation of the DSMS"""

import logging
import warnings
from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Union
from urllib.parse import urljoin
from uuid import UUID, uuid4

import pandas as pd
from rdflib import Graph

from pydantic import (  # isort:skip
    BaseModel,
    AliasChoices,
    ConfigDict,
    Field,
    ValidationInfo,
    field_validator,
    field_serializer,
)

from dsms.core.logging import handler  # isort:skip

from dsms.core.session import Session  # isort:skip

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
    LinkedKItem,
    LinkedKItemsList,
    Summary,
    UserGroup,
)

from dsms.knowledge.ktype import KType  # isort:skip

from dsms.knowledge.utils import (  # isort:skip
    _slugify,
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


class KItemCompactedModel(BaseModel):
    """
    KItem compacted model for the search-endpoint."""

    name: str
    id: UUID
    ktype_id: str
    slug: str

    def __str__(self) -> str:
        """Pretty print the kitem fields"""
        return print_model(self, "kitem")

    def __repr__(self) -> str:
        """Pretty print the kitem Fields"""
        return str(self)


class KItem(BaseModel):
    """
    Knowledge Item of the DSMS.

    Attributes:
        name (str):
            Human readable name of the KContext.dsms.
        id (Optional[UUID]):
            ID of the KItem. Defaults to a new UUID if not provided.
        ktype_id (Union[Enum, str]):
            Type ID of the KItem.
        slug (Optional[str]):
            Slug of the KContext.dsms. Minimum length: 4.
        annotations (List[Annotation]):
            Annotations of the KItem.
        attachments (List[Union[Attachment, str]]):
            File attachments of the DSMS.
        linked_kitems (List[Union[LinkedKItem, "KItem"]]):
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
        user_groups (List[UserGroup]):
                User groups able to access the KItem.
        custom_properties (Optional[Any]):
            Custom properties associated with the KItem.
        dataframe (Optional[Union[List[Column], pd.DataFrame, Dict[str, Union[List, Dict]]]]):
            DataFrame interface.
    """

    # public

    name: str = Field(
        ..., description="Human readable name of the KItem", max_length=300
    )
    id: Optional[UUID] = Field(
        default_factory=uuid4,
        description="ID of the KItem",
    )
    ktype_id: Union[Enum, str] = Field(..., description="Type ID of the KItem")
    ktype: Optional[Union[Enum, KType]] = Field(
        None, description="KType of the KItem", exclude=True
    )
    slug: Optional[str] = Field(
        None,
        description="Slug of the KItem",
        min_length=4,
        max_length=1000,
    )
    annotations: List[Union[str, Annotation]] = Field(
        [], description="Annotations of the KItem"
    )
    attachments: List[Union[Attachment, str]] = Field(
        [],
        description="File attachements of the DSMS",
    )
    linked_kitems: List[Union[LinkedKItem, "KItem"]] = Field(
        [],
        description="KItems linked to the current KItem.",
    )
    affiliations: List[Affiliation] = Field(
        [],
        description="Affiliations related to a KItem.",
    )
    authors: List[Union[Author, str]] = Field(
        [], description="Authorship of the KItem."
    )
    avatar_exists: Optional[bool] = Field(
        False, description="Whether the KItem holds an avatar or not."
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
    user_groups: List[UserGroup] = Field(
        [],
        description="User groups able to access the KItem.",
    )
    custom_properties: Optional[Union[KItemCustomPropertiesModel]] = Field(
        None, description="Custom properties associated to the KItem"
    )

    dataframe: Optional[
        Union[List[Column], pd.DataFrame, Dict[str, Union[List, Dict]]]
    ] = Field(None, description="DataFrame interface.")

    rdf_exists: bool = Field(
        False, description="Whether the KItem holds an RDF Graph or not."
    )

    avatar: Optional[Avatar] = Field(
        default_factory=Avatar, description="KItem avatar interface"
    )

    model_config = ConfigDict(
        validate_assignment=True,
        validate_default=True,
        exclude={"ktype", "avatar"},
        arbitrary_types_allowed=True,
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
            Annotation(**_make_annotation_schema(annotation))
            if isinstance(annotation, str)
            else annotation
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
            Attachment(name=attachment)
            if isinstance(attachment, str)
            else attachment
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

    @field_validator("linked_kitems", mode="before")
    @classmethod
    def validate_linked_kitems_list(
        cls,
        value: "List[Union[LinkedKItem, KItem]]",
    ) -> List[LinkedKItem]:
        """Validate each single kitem to be linked"""
        linked_kitems = []
        logger.debug("Found KItem to link: %s", value)
        for item in value:
            if isinstance(item, dict):
                item = LinkedKItem(**item)
            elif isinstance(item, BaseModel):
                item = LinkedKItem(**item.model_dump())
            else:
                raise TypeError(
                    "Expected either a LinkedKItem or a KItem to be linked."
                )
            linked_kitems.append(item)
        return linked_kitems

    @field_validator("linked_kitems", mode="after")
    @classmethod
    def validate_linked_kitems(
        cls,
        value: List[LinkedKItem],
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

    @field_validator("ktype_id")
    @classmethod
    def validate_ktype_id(cls, value: Union[str, Enum]) -> KType:
        """Validate the ktype id of the KItem"""

        if isinstance(value, str):
            ktype = Session.ktypes.get(value)
            if not ktype:
                raise TypeError(
                    f"KType for `ktype_id={value}` does not exist."
                )
            value = ktype
        if not hasattr(value, "id"):
            raise TypeError(
                "Not a valid KType. Provided Enum does not have an `id`."
            )

        return value.id

    @field_validator("ktype")
    @classmethod
    def validate_ktype(
        cls, value: Optional[Union[KType, Enum]], info: ValidationInfo
    ) -> KType:
        """Validate the ktype of the KItem"""

        ktype_id = info.data.get("ktype_id")

        if not value:
            value = Session.ktypes.get(ktype_id)
            if not value:
                raise TypeError(
                    f"KType for `ktype_id={ktype_id}` does not exist."
                )
        if not hasattr(value, "id"):
            raise TypeError(
                "Not a valid KType. Provided Enum does not have an `id`."
            )

        if value.id != ktype_id:
            raise TypeError(
                f"KType for `ktype_id={ktype_id}` does not match "
                f"the provided `ktype`."
            )

        return value

    @field_validator("slug")
    @classmethod
    def validate_slug(cls, value: str, info: ValidationInfo) -> str:
        """Validate slug"""

        kitem_id = info.data["id"]
        name = info.data["name"]

        if not value:
            value = _slugify(name)
            if len(value) < 4:
                raise ValueError(
                    "Slug length must have a minimum length of 4."
                )
            if Session.dsms.config.individual_slugs:
                value += f"-{str(kitem_id).split('-', maxsplit=1)[0]}"
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
                    value, ktype.webform
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

        spec: "List[Input]" = []
        if ktype.webform:  # pylint: disable=no-member
            for section in ktype.webform.sections:  # pylint: disable=no-member
                for inp in section.inputs:
                    if inp.id == entry.id:
                        spec.append(inp)

        logger.debug("Entry label: %s", entry.label)
        logger.debug("Entry value: %s", entry.value)

        # in this case we assume that a webform was defined for
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
            entry.type = spec.widget
            default_value = spec.value
            select_options = spec.select_options
            range_options = spec.range_options
            knowledge_type = spec.knowledge_type
            if range_options:
                is_list = range_options.range
            else:
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
        } or None
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
                error_message = (
                    """Value `{}` is not a valid select option.
                Valid options are: """
                    + str(list(choices.keys()))
                    + "\n"
                )
                if not select_options:
                    raise ValueError(
                        f"Widget of type `{entry.type}` does not have select options."
                    )
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
            warnings.warn(
                """
                Strict validation is disabled.
                Will not strictly type check the custom properties.
                This also will take place when values are re-assigned.
                """
            )

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

"""Knowledge Item implementation of the DSMS"""

import json
import logging
from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Union
from urllib.parse import urljoin
from uuid import UUID, uuid4

import pandas as pd
from rdflib import Graph

from pydantic import (  # isort:skip
    BaseModel,
    ConfigDict,
    Field,
    ValidationInfo,
    field_validator,
    model_validator,
)

from dsms.core.logging import handler  # isort:skip

from dsms.knowledge.properties import (  # isort:skip
    Affiliation,
    AffiliationsProperty,
    Annotation,
    AnnotationsProperty,
    App,
    AppsProperty,
    Avatar,
    Attachment,
    AttachmentsProperty,
    Author,
    AuthorsProperty,
    ContactInfo,
    ContactsProperty,
    ExternalLink,
    ExternalLinksProperty,
    KItemPropertyList,
    DataFrameContainer,
    Column,
    LinkedKItem,
    LinkedKItemsProperty,
    Summary,
    UserGroup,
    UserGroupsProperty,
)

from dsms.knowledge.ktype import KType  # isort:skip

from dsms.knowledge.utils import (  # isort:skip
    _kitem_exists,
    _get_kitem,
    _slug_is_available,
    _slugify,
    _inspect_dataframe,
    _make_annotation_schema,
    _refresh_kitem,
)

from dsms.knowledge.sparql_interface.utils import _get_subgraph  # isort:skip

if TYPE_CHECKING:
    from dsms import Context
    from dsms.core.dsms import DSMS

logger = logging.getLogger(__name__)
logger.addHandler(handler)
logger.propagate = False


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
        kitem_apps (List[App]): Apps related to the KItem.
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
    in_backend: bool = Field(
        False,
        description="Whether the KItem was already created in the backend.",
    )
    slug: Optional[str] = Field(
        None,
        description="Slug of the KContext.dsms",
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
    kitem_apps: List[App] = Field([], description="Apps related to the KItem.")
    summary: Optional[Union[str, Summary]] = Field(
        None, description="Human readable summary text of the KItem."
    )
    user_groups: List[UserGroup] = Field(
        [],
        description="User groups able to access the KItem.",
    )
    custom_properties: Optional[Any] = Field(
        None, description="Custom properties associated to the KItem"
    )
    ktype: Optional[KType] = Field(
        None, description="KType of the KItem", exclude=True
    )

    dataframe: Optional[
        Union[List[Column], pd.DataFrame, Dict[str, Union[List, Dict]]]
    ] = Field(None, description="DataFrame interface.")

    rdf_exists: bool = Field(
        False, description="Whether the KItem holds an RDF Graph or not."
    )

    avatar: Optional[Union[Avatar, Dict]] = Field(
        default_factory=Avatar, description="KItem avatar interface"
    )

    access_url: Optional[str] = Field(
        None, description="Access URL of the KItem"
    )

    context_id: Optional[Union[UUID, str]] = Field(
        None, description="Context ID of the KItem"
    )

    model_config = ConfigDict(
        extra="forbid",
        validate_assignment=True,
        validate_default=True,
        exclude={"ktype", "avatar"},
        arbitrary_types_allowed=True,
    )

    def __init__(self, **kwargs: "Any") -> None:
        """Initialize the KItem"""
        from dsms import DSMS

        logger.debug("Initialize KItem with model data: %s", kwargs)

        # set dsms instance if not already done
        if not self.dsms:
            self.dsms = DSMS()

        # initialize the kitem
        super().__init__(**kwargs)

        # add kitem to buffer
        if not self.in_backend and self.id not in self.context.buffers.created:
            logger.debug(
                "Marking KItem with ID `%s` as created and updated during KItem initialization.",
                self.id,
            )
            self.context.buffers.created.update({self.id: self})
            self.context.buffers.updated.update({self.id: self})

        self._set_kitem_for_properties()

        logger.debug("KItem initialization successful.")

    def __setattr__(self, name, value) -> None:
        """Add kitem to updated-buffer if an attribute is set"""
        super().__setattr__(name, value)
        logger.debug(
            "Setting property with key `%s` on KItem level: %s.", name, value
        )
        self._set_kitem_for_properties()

        if (
            self.id not in self.context.buffers.updated
            and not name.startswith("_")
        ):
            logger.debug(
                "Setting KItem with ID `%s` as updated during KItem.__setattr__",
                self.id,
            )
            self.context.buffers.updated.update({self.id: self})

    def __str__(self) -> str:
        """Pretty print the kitem fields"""
        fields = ", \n".join(
            [
                f"\n\t{key} = {value}"
                for key, value in self.__dict__.items()
                if (
                    key not in self.model_config["exclude"]
                    and key not in self.dsms.config.hide_properties
                )
            ]
        )
        return f"{self.__class__.__name__}(\n{fields}\n)"

    def __repr__(self) -> str:
        """Pretty print the kitem Fields"""
        return str(self)

    def __hash__(self) -> int:
        return hash(str(self))

    @field_validator("affiliations", mode="before")
    @classmethod
    def validate_affiliations_before(
        cls, value: List[Union[str, Affiliation]]
    ) -> List[Affiliation]:
        """Validate affiliations Field"""
        return [
            Affiliation(name=affiliation)
            if isinstance(affiliation, str)
            else affiliation
            for affiliation in value
        ]

    @field_validator("affiliations", mode="after")
    @classmethod
    def validate_affiliation_after(
        cls, value: List[Affiliation]
    ) -> AffiliationsProperty:
        """Validate affiliations Field"""
        return AffiliationsProperty(value)

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
    ) -> AnnotationsProperty:
        """Validate annotations Field"""
        return AnnotationsProperty(value)

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
        cls, value: List[Attachment]
    ) -> AttachmentsProperty:
        """Validate attachments Field"""
        return AttachmentsProperty(value)

    @field_validator("kitem_apps", mode="after")
    @classmethod
    def validate_apps(cls, value: List[App]) -> AppsProperty:
        """Validate apps Field"""
        return AppsProperty(value)

    @field_validator("authors")
    @classmethod
    def validate_authors(cls, value: List[Author]) -> AuthorsProperty:
        """Validate authors Field"""
        return AuthorsProperty(
            [
                Author(user_id=author) if isinstance(author, str) else author
                for author in value
            ]
        )

    @field_validator("contacts", mode="after")
    @classmethod
    def validate_contacts(cls, value: List[ContactInfo]) -> ContactsProperty:
        """Validate contacts Field"""
        return ContactsProperty(value)

    @field_validator("external_links", mode="after")
    @classmethod
    def validate_external_links(
        cls, value: List[ExternalLink]
    ) -> ExternalLinksProperty:
        """Validate external links Field"""
        return ExternalLinksProperty(value)

    @field_validator("linked_kitems", mode="before")
    @classmethod
    def validate_linked_kitems_list(
        cls, value: "List[Union[Dict, KItem, Any]]", info: ValidationInfo
    ) -> List[LinkedKItem]:
        """Validate each single kitem to be linked"""
        src_id = info.data.get("id")
        linked_kitems = []
        for item in value:
            if isinstance(item, dict):
                dest_id = item.get("id")
                if not dest_id:
                    raise ValueError("Linked KItem is missing `id`")
                linked_model = _get_kitem(dest_id, as_json=True)
            elif isinstance(item, KItem):
                dest_id = item.id
                linked_model = item.model_dump()
            else:
                try:
                    dest_id = getattr(item, "id")
                    linked_model = _get_kitem(dest_id, as_json=True)
                except AttributeError as error:
                    raise AttributeError(
                        f"Linked KItem `{item}` has no attribute `id`."
                    ) from error
            if str(src_id) == str(dest_id):
                raise ValueError(
                    f"Cannot link KItem with ID `{src_id}` to itself!"
                )
            linked_kitems.append(LinkedKItem(**linked_model))
        return linked_kitems

    @field_validator("linked_kitems", mode="after")
    @classmethod
    def validate_linked_kitems(
        cls,
        value: List[LinkedKItem],
    ) -> LinkedKItemsProperty:
        """Validate the list out of linked KItems"""
        return LinkedKItemsProperty(value)

    @field_validator("user_groups", mode="after")
    @classmethod
    def validate_user_groups(
        cls, value: List[UserGroup]
    ) -> UserGroupsProperty:
        """Validate user groups Field"""
        return UserGroupsProperty(value)

    @field_validator("created_at")
    @classmethod
    def validate_created(cls, value: str) -> Any:
        """Convert the str for `created_at` in to a `datetime`-object"""
        from dsms import Context

        if isinstance(value, str):
            value = datetime.strptime(
                value, Context.dsms.config.datetime_format
            )
        return value

    @field_validator("updated_at")
    @classmethod
    def validate_updated(cls, value: str) -> Any:
        """Convert the str for `created_at` in to a `datetime`-object"""
        from dsms import Context

        if isinstance(value, str):
            value = datetime.strptime(
                value, Context.dsms.config.datetime_format
            )
        return value

    @field_validator("ktype")
    @classmethod
    def validate_ktype(cls, value: KType, info: ValidationInfo) -> KType:
        """Validate the data attribute of the KItem"""
        from dsms import Context

        if not value:
            ktype_id = info.data.get("ktype_id")
            if not isinstance(ktype_id, str):
                value = Context.ktypes.get(ktype_id.value)
            else:
                value = Context.ktypes.get(ktype_id)

            if not value:
                raise TypeError(
                    f"KType for `ktype_id={ktype_id}` does not exist."
                )
        return value

    @field_validator("in_backend")
    @classmethod
    def validate_in_backend(cls, value: bool, info: ValidationInfo) -> bool:
        """Checks whether the kitem already exists"""
        kitem_id = info.data["id"]
        if not value:
            value = _kitem_exists(kitem_id)
        return value

    @field_validator("slug")
    @classmethod
    def validate_slug(cls, value: str, info: ValidationInfo) -> str:
        """Validate slug"""
        from dsms import Context

        ktype_id = info.data["ktype_id"]
        kitem_id = info.data.get("id")
        kitem_exists = info.data.get("in_backend")
        if not isinstance(kitem_exists, bool):
            kitem_exists = cls.in_backend

        if not isinstance(ktype_id, str):
            ktype = ktype_id.value
        else:
            ktype = ktype_id
        name = info.data.get("name")

        if not value:
            value = _slugify(name)
            if len(value) < 4:
                raise ValueError(
                    "Slug length must have a minimum length of 4."
                )
            if Context.dsms.config.individual_slugs:
                value += f"-{str(kitem_id).split('-', maxsplit=1)[0]}"
        if not kitem_exists and not _slug_is_available(ktype, value):
            raise ValueError(f"Slug for `{value}` is already taken.")
        return value

    @field_validator("summary")
    @classmethod
    def validate_summary(cls, value: Union[str, Summary]) -> Summary:
        """Check whether the summary is a string or the dedicated model"""
        if isinstance(value, str):
            value = Summary(kitem=cls, text=value)
        return value

    @field_validator("avatar", mode="before")
    @classmethod
    def validate_avatar(cls, value: "Union[Dict, Avatar]") -> Avatar:
        """Validate avatar"""
        if isinstance(value, dict):
            value = Avatar(kitem=cls, **value)
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
            columns = _inspect_dataframe(kitem_id)
            if columns:
                dataframe = DataFrameContainer(
                    [Column(**column) for column in columns]
                )
            else:
                dataframe = None
        return dataframe

    @model_validator(mode="after")
    @classmethod
    def validate_custom_properties(cls, self) -> "KItem":
        """Validate the custom properties with respect to the KType of the KItem"""
        if not isinstance(
            self.custom_properties, (BaseModel, dict, type(None))
        ):
            raise TypeError(
                f"""Custom properties must be one of the following types:
                  {(BaseModel, dict, type(None))}. Not {type(self.custom_properties)}"""
            )
        # validate content with webform model
        if self.ktype.webform and isinstance(self.custom_properties, dict):
            content = (
                self.custom_properties.get("content") or self.custom_properties
            )
            if isinstance(content, str):
                try:
                    content = json.loads(content)
                except Exception as error:
                    raise TypeError(
                        f"Invalid type: {type(content)}"
                    ) from error
            was_in_buffer = self.id in self.context.buffers.updated
            self.custom_properties = self.ktype.webform(**content)
            # fix: find a better way to prehebit that properties are
            # set in the buffer
            if not was_in_buffer:
                self.context.buffers.updated.pop(self.id)
        # set kitem id for custom properties
        if isinstance(self.custom_properties, BaseModel):
            self.custom_properties.kitem = self
        return self

    def _set_kitem_for_properties(self) -> None:
        """Set kitem for CustomProperties and KProperties in order to
        remain the context for the buffer if any of these properties is changed.
        """
        for prop in self.__dict__.values():
            if (
                isinstance(prop, (KItemPropertyList, Summary, Avatar))
                and not prop.kitem
            ):
                logger.debug(
                    "Setting kitem with ID `%s` for property `%s` on KItem level",
                    self.id,
                    type(prop),
                )
                prop.kitem = self

    @property
    def dsms(cls) -> "DSMS":
        """DSMS context getter"""
        return cls.context.dsms

    @dsms.setter
    def dsms(cls, value: "DSMS") -> None:
        """DSMS context setter"""
        cls.context.dsms = value

    @property
    def subgraph(cls) -> Optional[Graph]:
        """Getter for Subgraph"""
        return _get_subgraph(
            cls.id, cls.dsms.config.kitem_repo, is_kitem_id=True
        )

    @property
    def context(cls) -> "Context":
        """Getter for Context"""
        from dsms import (  # isort:skip
            Context,
        )

        return Context

    @property
    def url(cls) -> str:
        """URL of the KItem"""
        return cls.access_url or urljoin(
            str(cls.context.dsms.config.host_url),
            f"knowledge/{cls._get_ktype_as_str()}/{cls.slug}",
        )

    def is_a(self, to_be_compared: KType) -> bool:
        """Check the KType of the KItem"""
        return (
            self.ktype_id == to_be_compared.value  # pylint: disable=no-member
        )

    def refresh(self) -> None:
        """Refresh the KItem"""
        _refresh_kitem(self)

    def _get_ktype_as_str(self) -> str:
        if isinstance(self.ktype_id, str):
            ktype = self.ktype_id
        elif isinstance(self.ktype_id, Enum):
            ktype = self.ktype_id.value  # pylint: disable=no-member
        else:
            raise TypeError(f"Datatype for KType is unknown: {type(ktype)}")
        return ktype

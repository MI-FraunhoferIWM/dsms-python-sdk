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
    ConfigDict,
    Field,
    ValidationInfo,
    field_validator,
    model_validator,
    field_serializer,
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
    _transform_custom_properties_schema,
    print_model,
)

from dsms.knowledge.sparql_interface.utils import _get_subgraph  # isort:skip

from dsms.knowledge.webform import KItemCustomPropertiesModel  # isort:skip

if TYPE_CHECKING:
    from dsms import Session
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
    ktype: Optional[Union[Enum, KType]] = Field(
        None, description="KType of the KItem", exclude=True
    )
    in_backend: bool = Field(
        False,
        description="Whether the KItem was already created in the backend.",
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

    dataframe: Optional[
        Union[List[Column], pd.DataFrame, Dict[str, Union[List, Dict]]]
    ] = Field(None, description="DataFrame interface.")

    rdf_exists: bool = Field(
        False, description="Whether the KItem holds an RDF Graph or not."
    )

    avatar: Optional[Union[Avatar, Dict]] = Field(
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
        from dsms import DSMS

        logger.debug("Initialize KItem with model data: %s", kwargs)

        # set dsms instance if not already done
        if not self.dsms:
            self.dsms = DSMS()

        # initialize the kitem
        super().__init__(**kwargs)

        # add kitem to buffer
        if not self.in_backend and self.id not in self.session.buffers.created:
            logger.debug(
                "Marking KItem with ID `%s` as created and updated during KItem initialization.",
                self.id,
            )
            self.session.buffers.created.update({self.id: self})
            self.session.buffers.updated.update({self.id: self})

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
            self.id not in self.session.buffers.updated
            and not name.startswith("_")
        ):
            logger.debug(
                "Setting KItem with ID `%s` as updated during KItem.__setattr__",
                self.id,
            )
            self.session.buffers.updated.update({self.id: self})

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
        from dsms import Session

        if isinstance(value, str):
            value = datetime.strptime(
                value, Session.dsms.config.datetime_format
            )
        return value

    @field_validator("updated_at")
    @classmethod
    def validate_updated(cls, value: str) -> Any:
        """Convert the str for `created_at` in to a `datetime`-object"""
        from dsms import Session

        if isinstance(value, str):
            value = datetime.strptime(
                value, Session.dsms.config.datetime_format
            )
        return value

    @field_validator("ktype_id")
    @classmethod
    def validate_ktype_id(cls, value: Union[str, Enum]) -> KType:
        """Validate the ktype id of the KItem"""
        from dsms import Session

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
        from dsms import Session

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
        from dsms import Session

        ktype_id = info.data["ktype_id"]
        kitem_id = info.data["id"]
        name = info.data["name"]
        kitem_exists = info.data.get("in_backend")
        if not isinstance(kitem_exists, bool):
            kitem_exists = cls.in_backend

        if not value:
            value = _slugify(name)
            if len(value) < 4:
                raise ValueError(
                    "Slug length must have a minimum length of 4."
                )
            if Session.dsms.config.individual_slugs:
                value += f"-{str(kitem_id).split('-', maxsplit=1)[0]}"
        if not kitem_exists and not _slug_is_available(ktype_id, value):
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
    def validate_custom_properties(cls, self: "KItem") -> "KItem":
        """Validate custom properties"""

        if isinstance(self.custom_properties, dict):
            value = (
                self.custom_properties.get("content") or self.custom_properties
            )

            if not value.get("sections"):
                value = _transform_custom_properties_schema(
                    value, self.ktype.webform
                )
                warnings.warn(
                    """A flat dictionary was provided for custom properties.
                    Will be transformed into `KItemCustomPropertiesModel`."""
                )
            was_in_buffer = self.id in self.session.buffers.updated
            self.custom_properties = KItemCustomPropertiesModel(
                **value, kitem=self
            )
            if not was_in_buffer:
                self.session.buffers.updated.pop(self.id)
        elif not isinstance(
            self.custom_properties, (KItemCustomPropertiesModel, type(None))
        ):
            raise TypeError(
                "Custom properties must be either a dictionary or a "
                "KItemCustomPropertiesModel. Not a "
                f"{type(self.custom_properties)}: {self.custom_properties}"
            )
        return self

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

    def _set_kitem_for_properties(self) -> None:
        """Set kitem for CustomProperties and KProperties in order to
        remain the session for the buffer if any of these properties is changed.
        """
        for prop in self.__dict__.values():
            if (
                isinstance(
                    prop,
                    (
                        KItemPropertyList,
                        Summary,
                        Avatar,
                        KItemCustomPropertiesModel,
                    ),
                )
                and not prop.kitem
            ):
                logger.debug(
                    "Setting kitem with ID `%s` for property `%s` on KItem level",
                    self.id,
                    type(prop),
                )
                prop.kitem = self

    @property
    def dsms(self) -> "DSMS":
        """DSMS session getter"""
        return self.session.dsms

    @dsms.setter
    def dsms(self, value: "DSMS") -> None:
        """DSMS session setter"""
        self.session.dsms = value

    @property
    def subgraph(self) -> Optional[Graph]:
        """Getter for Subgraph"""
        return _get_subgraph(
            self.id, self.dsms.config.kitem_repo, is_kitem_id=True
        )

    @property
    def session(self) -> "Session":
        """Getter for Session"""
        from dsms import (  # isort:skip
            Session,
        )

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

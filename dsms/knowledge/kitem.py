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
    _slug_is_available,
    _slugify,
    _inspect_dataframe,
    _make_annotation_schema,
    _refresh_kitem,
    _transform_custom_properties_schema,
    print_model,
    _kitem_exists,
)

from dsms.knowledge.sparql_interface.utils import _get_subgraph  # isort:skip

from dsms.knowledge.webform import KItemCustomPropertiesModel  # isort:skip

if TYPE_CHECKING:
    from dsms.core.dsms import DSMS

logger = logging.getLogger(__name__)
logger.addHandler(handler)
logger.propagate = False

DATETIME_FRMT = "%Y-%m-%dT%H:%M:%S.%f"


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

    @field_validator("kitem_apps", mode="after")
    @classmethod
    def validate_apps(cls, value: List[App], info: ValidationInfo) -> AppList:
        """Validate apps Field"""
        kitem_id = info.data["id"]
        if value:
            for app in value:
                app.id = kitem_id
        return AppList(value)

    @field_validator("linked_kitems")
    @classmethod
    def validate_linked_kitems_list(
        cls,
        value: "List[Union[Dict, KItem, Any]]",
    ) -> List[LinkedKItem]:
        """Validate each single kitem to be linked"""
        linked_kitems = []
        for item in value:
            if isinstance(item, KItem):
                item = LinkedKItem(**item.model_dump())
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

        ktype_id = info.data["ktype_id"]
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
        if not _kitem_exists(
            Session.dsms, kitem_id
        ) and not _slug_is_available(Session.dsms, ktype_id, value):
            raise ValueError(f"Slug for `{value}` is already taken.")
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
                warnings.warn(
                    """A flat dictionary was provided for custom properties.
                    Will be transformed into `KItemCustomPropertiesModel`."""
                )
            self.custom_properties = KItemCustomPropertiesModel(
                **_transform_custom_properties_schema(
                    self, value, self.ktype.webform
                )
            )
        elif not isinstance(
            self.custom_properties, (KItemCustomPropertiesModel, type(None))
        ):
            raise TypeError(
                "Custom properties must be either a dictionary or a "
                "KItemCustomPropertiesModel. Not a "
                f"{type(self.custom_properties)}: {self.custom_properties}"
            )
        if self.custom_properties:
            for section in self.custom_properties.sections:
                for entry in section.entries:
                    entry.kitem = self
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

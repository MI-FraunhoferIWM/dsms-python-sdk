"""Knowledge Item implementation of the DSMS"""

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
)


from dsms.knowledge.properties import (  # isort:skip
    Affiliation,
    AffiliationsProperty,
    Annotation,
    AnnotationsProperty,
    App,
    AppsProperty,
    Attachment,
    AttachmentsProperty,
    Author,
    AuthorsProperty,
    ContactInfo,
    ContactsProperty,
    CustomProperties,
    ExternalLink,
    ExternalLinksProperty,
    KProperty,
    HDF5Container,
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
    _slug_is_available,
    _slugify,
    _inspect_hdf5,
)

from dsms.knowledge.sparql_interface.utils import _get_subgraph  # isort:skip

if TYPE_CHECKING:
    from dsms import Context
    from dsms.core.dsms import DSMS


class KItem(BaseModel):
    """Knowledge Item of the DSMS."""

    # public
    name: str = Field(
        ..., description="Human readable name of the KContext.dsms"
    )
    id: Optional[UUID] = Field(
        default_factory=uuid4,
        description="ID of the KItem",
    )
    ktype_id: Union[Enum, str] = Field(..., description="Type ID of the KItem")
    slug: Optional[str] = Field(
        None, description="Slug of the KContext.dsms", min_length=4
    )
    annotations: List[Annotation] = Field(
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
        {}, description="Custom properties associated to the KItem"
    )
    ktype: Optional[KType] = Field(
        None, description="KType of the KItem", exclude=True
    )

    hdf5: Optional[
        Union[List[Column], pd.DataFrame, Dict[str, Union[List, Dict]]]
    ] = Field(None, description="HDF5 interface.")

    model_config = ConfigDict(
        extra="forbid",
        validate_assignment=True,
        validate_default=True,
        exclude={"ktype"},
        arbitrary_types_allowed=True,
    )

    def __init__(self, **kwargs: "Any") -> None:
        """Initialize the KItem"""
        from dsms import DSMS

        # set dsms instance if not already done
        if not self.dsms:
            self.dsms = DSMS()

        # initalize the kitem
        super().__init__(**kwargs)

        # add kitem to buffer
        if (
            not _kitem_exists(self)
            and self.id not in self.context.buffers.created
        ):
            self.context.buffers.created.update({self.id: self})
            self.context.buffers.updated.update({self.id: self})

        self._set_kitem_for_properties()

    def __setattr__(self, name, value) -> None:
        """Add kitem to updated-buffer if an attribute is set"""
        super().__setattr__(name, value)
        self._set_kitem_for_properties()

        if (
            self.id not in self.context.buffers.updated
            and not name.startswith("_")
        ):
            self.context.buffers.updated.update({self.id: self})

    def __str__(self) -> str:
        """Pretty print the kitem fields"""
        fields = ", \n".join(
            [
                f"\n\t{key} = {value}"
                for key, value in self.__dict__.items()
                if key not in self.model_config["exclude"]
            ]
        )
        return f"{self.__class__.__name__}(\n{fields}\n)"

    def __repr__(self) -> str:
        """Pretty print the kitem Fields"""
        return str(self)

    def __hash__(self) -> int:
        return hash(str(self))

    @field_validator("affiliations")
    @classmethod
    def validate_affiliation(
        cls, value: List[Affiliation]
    ) -> AffiliationsProperty:
        """Validate affiliations Field"""
        return AffiliationsProperty(value)

    @field_validator("annotations")
    @classmethod
    def validate_annotations(
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

    @field_validator("kitem_apps")
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

    @field_validator("contacts")
    @classmethod
    def validate_contacts(cls, value: List[ContactInfo]) -> ContactsProperty:
        """Validate contacts Field"""
        return ContactsProperty(value)

    @field_validator("external_links")
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
        linked_kitems = []
        for item in value:
            if isinstance(item, dict):
                dest_id = item.get("id")
                if not dest_id:
                    raise ValueError("Linked KItem is missing `id`")
            elif isinstance(item, KItem):
                dest_id = item.id
            else:
                try:
                    dest_id = getattr(item, "id")
                except AttributeError as error:
                    raise AttributeError(
                        f"Linked KItem `{item}` has no attribute `id`."
                    ) from error
            linked_kitems.append(
                LinkedKItem(id=dest_id, source_id=info.data["id"])
            )
        return linked_kitems

    @field_validator("linked_kitems", mode="after")
    @classmethod
    def validate_linked_kitems(
        cls,
        value: List[LinkedKItem],
    ) -> LinkedKItemsProperty:
        """Validate the list out of linked KItems"""
        return LinkedKItemsProperty(value)

    @field_validator("user_groups")
    @classmethod
    def validate_user_groups(
        cls, value: List[UserGroup]
    ) -> UserGroupsProperty:
        """Validate user groups Field"""
        return UserGroupsProperty(value)

    @field_validator("custom_properties")
    @classmethod
    def validate_custom_properties(cls, value: Any) -> CustomProperties:
        """Validate custom properties Field"""
        if isinstance(value, dict) and "content" in value:
            value = CustomProperties(content=value["content"])
        elif isinstance(value, dict):
            value = CustomProperties(content=value)
        elif not isinstance(value, (CustomProperties, dict, type(None))):
            raise TypeError(
                f"""`custom_properties` must be of type {CustomProperties} or {dict},
                not {type(value)}."""
            )
        return value

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

        ktype_id = info.data.get("ktype_id")

        if not value:
            if not isinstance(ktype_id, str):
                value = Context.ktypes.get(ktype_id.value)
            else:
                value = Context.ktypes.get(ktype_id)

            if not value:
                raise TypeError(
                    f"KType for `ktype_id={ktype_id}` does not exist."
                )

        return value

    @field_validator("slug")
    @classmethod
    def validate_slug(cls, value: str, info: ValidationInfo) -> str:
        """Validate slug"""
        ktype_id = info.data["ktype_id"]
        name = info.data.get("name")
        kitem_id = info.data.get("id")
        if not value:
            value = _slugify(name)
        slugified = _slugify(value)
        if len(slugified) < 4:
            raise ValueError("Slug length must have a minimum length of 4.")
        if value != slugified:
            raise ValueError(
                f"`{value}` is not a valid slug. A valid variation would be `{slugified}`"
            )
        if not _kitem_exists(kitem_id) and not _slug_is_available(
            ktype_id.value, value
        ):
            raise ValueError(f"Slug for `{value}` is already taken.")
        return value

    @field_validator("summary")
    @classmethod
    def validate_summary(cls, value: Union[str, Summary]) -> Summary:
        """Check whether the summary is a string or the dedicated model"""
        if isinstance(value, str):
            value = Summary(kitem=cls, text=value)
        return value

    @field_validator("hdf5")
    @classmethod
    def validate_hdf5(
        cls,
        value: Union[
            List[Column], pd.DataFrame, Dict[str, Dict[Any, Any]]
        ],  # pylint: disable=unused-argument
        info: ValidationInfo,
    ) -> HDF5Container:
        """Get HDF5 container if it exists."""
        kitem_id = info.data.get("id")
        if isinstance(value, (pd.DataFrame, dict)):
            if isinstance(value, pd.DataFrame):
                hdf5 = value.copy(deep=True)
            elif isinstance(value, dict):
                hdf5 = pd.DataFrame.from_dict(value)
            else:
                raise TypeError(
                    f"Data must be of type {dict} or {pd.DataFrame}, not {type(value)}"
                )
        else:
            columns = _inspect_hdf5(kitem_id)
            if columns:
                hdf5 = HDF5Container([Column(**column) for column in columns])
            else:
                hdf5 = None
        return hdf5

    def _set_kitem_for_properties(self) -> None:
        """Set kitem for CustomProperties and KProperties in order to
        remain the context for the buffer if any of these properties is changed.
        """
        for prop in self.__dict__.values():
            if (
                isinstance(prop, (KProperty, CustomProperties, Summary))
                and not prop.kitem
            ):
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
        return urljoin(
            cls.context.dsms.config.host_url, f"{cls.ktype_id}/{cls.slug}"
        )

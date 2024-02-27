"""DSMS Propertys module"""

from dsms.knowledge.properties.affiliations import (  # isort:skip
    Affiliation,
    AffiliationsProperty,
)
from dsms.knowledge.properties.annotations import (  # isort:skip
    Annotation,
    AnnotationsProperty,
)
from dsms.knowledge.properties.apps import App, AppsProperty
from dsms.knowledge.properties.authors import Author, AuthorsProperty
from dsms.knowledge.properties.base import KProperty, KPropertyItem
from dsms.knowledge.properties.contacts import ContactInfo, ContactsProperty
from dsms.knowledge.properties.custom_properties import CustomProperties
from dsms.knowledge.properties.hdf5 import Column, HDF5Container
from dsms.knowledge.properties.summary import Summary
from dsms.knowledge.properties.user_groups import UserGroup, UserGroupsProperty

from dsms.knowledge.properties.attachments import (  # isort:skip
    Attachment,
    AttachmentsProperty,
)


from dsms.knowledge.properties.linked_kitems import (  # isort:skip
    LinkedKItem,
    LinkedKItemsProperty,
)

from dsms.knowledge.properties.external_links import (  # isort:skip
    ExternalLink,
    ExternalLinksProperty,
)


__all__ = [
    "Annotation",
    "AnnotationsProperty",
    "Attachment",
    "AttachmentsProperty",
    "Author",
    "AuthorsProperty",
    "CustomProperties",
    "LinkedKItem",
    "LinkedKItemsProperty",
    "ContactInfo",
    "ContactsProperty",
    "ExternalLinksProperty",
    "ExternalLink",
    "AppsProperty",
    "App",
    "AffiliationsProperty",
    "Affiliation",
    "UserGroupsProperty",
    "UserGroup",
    "Summary",
    "KProperty",
    "KPropertyItem",
    "HDF5Container",
    "Column",
]

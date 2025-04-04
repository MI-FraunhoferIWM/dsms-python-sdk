"""DSMS Propertys module"""

from dsms.knowledge.properties.affiliations import (  # isort:skip
    Affiliation,
)
from dsms.knowledge.properties.annotations import (  # isort:skip
    Annotation,
    AnnotationList,
)
from dsms.knowledge.properties.apps import App, AppList
from dsms.knowledge.properties.authors import Author
from dsms.knowledge.properties.contacts import ContactInfo
from dsms.knowledge.properties.dataframe import Column, DataFrameContainer
from dsms.knowledge.properties.summary import Summary
from dsms.knowledge.properties.user_groups import UserGroup

from dsms.knowledge.properties.attachments import (  # isort:skip
    Attachment,
    AttachmentList,
)


from dsms.knowledge.properties.linked_kitems import (  # isort:skip
    LinkedKItem,
    LinkedKItemsList,
)

from dsms.knowledge.properties.external_links import (  # isort:skip
    ExternalLink,
)

from dsms.knowledge.properties.avatar import Avatar  # isort:skip

__all__ = [
    "Annotation",
    "Attachment",
    "App",
    "AppList",
    "AnnotationList",
    "AttachmentList",
    "LinkedKItemsList",
    "Author",
    "Avatar",
    "LinkedKItem",
    "ContactInfo",
    "ExternalLink",
    "Affiliation",
    "UserGroup",
    "Summary",
    "DataFrameContainer",
    "Column",
]

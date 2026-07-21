"""DSMS Propertys module"""

from dsms.knowledge.properties.affiliations import (  # isort:skip
    Affiliation,
)
from dsms.knowledge.properties.annotations import (  # isort:skip
    Annotation,
    AnnotationList,
)
from dsms.knowledge.properties.access import KItemAccessProperties
from dsms.knowledge.properties.apps import App, AppList
from dsms.knowledge.properties.authors import Author
from dsms.knowledge.properties.contacts import ContactInfo
from dsms.knowledge.properties.dataframe import Column, DataFrameContainer
from dsms.knowledge.properties.summary import Summary

from dsms.knowledge.properties.attachments import (  # isort:skip
    Attachment,
    AttachmentList,
)


from dsms.knowledge.properties.linked_kitems import (  # isort:skip
    LinkedKItemsList,
    KItemRelationshipModel,
)

from dsms.knowledge.properties.external_links import (  # isort:skip
    ExternalLink,
)

from dsms.knowledge.properties.avatar import Avatar  # isort:skip
from dsms.knowledge.properties.schema_data import (  # isort:skip
    KItemSchemaData,
    KItemSchemaDataList,
)

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
    "ContactInfo",
    "ExternalLink",
    "Affiliation",
    "Summary",
    "DataFrameContainer",
    "Column",
    "KItemRelationshipModel",
    "KItemAccessProperties",
    "KItemSchemaData",
    "KItemSchemaDataList",
]

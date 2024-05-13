"""App  property of a KItem"""

from typing import TYPE_CHECKING, Any, Dict, List, Optional

from pydantic import BaseModel, Field, model_serializer

from dsms.knowledge.properties.base import KItemProperty, KItemPropertyList

if TYPE_CHECKING:
    from typing import Callable


class AdditionalProperties(BaseModel):
    """Additional properties of"""

    triggerUponUpload: bool = Field(
        False,
        description="Whether the app should be triggered when a file is uploaded",
    )
    triggerUponUploadFileExtensions: Optional[List[str]] = Field(
        None,
        description="File extensions for which the upload shall be triggered.",
    )

    def __str__(self) -> str:
        """Pretty print the KItemPropertyList"""
        values = ", ".join(
            [f"{key}: {value}" for key, value in self.__dict__.items()]
        )
        return f"{{{values}}}"

    def __repr__(self) -> str:
        """Pretty print the Apps"""
        return str(self)


class App(KItemProperty):
    """App of a KItem."""

    kitem_app_id: Optional[int] = Field(
        None, description="ID of the KItem App"
    )
    executable: str = Field(
        ..., description="Name of the executable related to the app"
    )
    title: Optional[str] = Field(None, description="Title of the appilcation")
    description: Optional[str] = Field(
        None, description="Description of the appilcation"
    )
    tags: Optional[dict] = Field(
        None, description="Tags related to the appilcation"
    )
    additional_properties: Optional[AdditionalProperties] = Field(
        None, description="Additional properties related to the appilcation"
    )

    # OVERRIDE
    @model_serializer
    def serialize_author(self) -> Dict[str, Any]:
        """Serialize author model"""
        return {
            key: value
            for key, value in self.__dict__.items()
            if key not in ["id", "kitem_app_id"]
        }

    def run(self, *args, **kwargs) -> None:
        """Run application"""
        raise NotImplementedError


class AppsProperty(KItemPropertyList):
    """KItemPropertyList for apps"""

    # OVERRIDE
    @property
    def k_property_item(cls) -> "Callable":
        """App data model"""
        return App

    @property
    def k_property_helper(cls) -> None:
        """Not defined for Apps"""

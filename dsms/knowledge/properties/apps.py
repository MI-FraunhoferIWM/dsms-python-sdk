"""App KProperty"""

from typing import TYPE_CHECKING, Optional

from pydantic import BaseModel, Field

from dsms.knowledge.properties.base import KProperty, KPropertyItem

if TYPE_CHECKING:
    from typing import Callable


class AdditionalProperties(BaseModel):
    """Additional properties of"""

    triggerUponUpload: bool = Field(
        False,
        description="Whether the app should be triggered when a file is uploaded",
    )
    triggerUponUploadFileExtensions: Optional[list[str]] = Field(
        None,
        description="File extensions for which the upload shall be triggered.",
    )


class App(KPropertyItem):
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

    def run(self, *args, **kwargs) -> None:
        """Run application"""
        raise NotImplementedError


class AppsProperty(KProperty):
    """KProperty for apps"""

    # OVERRIDE
    @property
    def k_property_item(cls) -> "Callable":
        """App data model"""
        return App

    # OVERRIDE
    def _add(self, item: App) -> App:
        """Side effect when an App is added to the KProperty"""
        return item

    # OVERRIDE
    def _update(self, item: App) -> App:
        """Side effect when an App is updated at the KProperty"""
        return item

    # OVERRIDE
    def _delete(self, item: App) -> None:
        """Side effect when deleting the App of a KItem"""

    # OVERRIDE
    def _get(self, item: App) -> App:
        """Side effect when getting the App for a specfic kitem"""
        return item

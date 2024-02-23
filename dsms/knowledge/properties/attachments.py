"""Attachment KProperty"""

from typing import TYPE_CHECKING

from pydantic import Field

from dsms.knowledge.properties.base import KProperty, KPropertyItem
from dsms.knowledge.utils import _get_attachment

if TYPE_CHECKING:
    from typing import Callable


class Attachment(KPropertyItem):
    """Attachment uploaded by a  certain user."""

    name: str = Field(..., description="File name of the attachment")

    def download(self) -> str:
        """Download attachment file"""
        return _get_attachment(self.id, self.name)


class AttachmentsProperty(KProperty):
    """KProperty for managing attachments."""

    # OVERRIDE
    @property
    def k_property_item(cls) -> "Callable":
        return Attachment

    # OVERRIDE
    def _add(self, item: Attachment) -> Attachment:
        """Side effect when an Attachment is added to the KProperty"""
        return item

    # OVERRIDE
    def _update(self, item: Attachment) -> Attachment:
        """Side effect when an Attachment is updated at the KProperty"""
        return item

    # OVERRIDE
    def _delete(self, item: Attachment) -> None:
        """Side effect when deleting the Attachment of a KItem"""

    # OVERRIDE
    def _get(self, item: Attachment) -> Attachment:
        """Side effect when getting the Attachment for a specfic kitem"""
        return item

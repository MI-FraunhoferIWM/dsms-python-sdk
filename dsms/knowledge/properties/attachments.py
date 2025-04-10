"""Attachment property of a KItem"""

from pathlib import Path
from typing import TYPE_CHECKING, Optional, Union
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from dsms.core.session import Session
from dsms.knowledge.utils import _get_attachment, print_model

if TYPE_CHECKING:
    from typing import List


class Attachment(BaseModel):
    """Attachment uploaded by a  certain user."""

    id: UUID = Field(
        None,
        description="ID of the attachment",
        exclude=True,
    )

    name: str = Field(
        ..., description="File name of the attachment", max_length=100
    )

    content: Optional[Union[str, bytes]] = Field(
        None, description="Content of the file", exclude=True
    )

    model_config = ConfigDict(
        exclude={"id", "content"},
        populate_by_name=True,
        from_attributes=True,
    )

    # OVERRIDE
    def __repr__(self) -> str:
        return str(self)

    # OVERRIDE
    def __str__(self) -> str:
        return print_model(self, "attachment", exclude_extra={"id"})

    def download(self, as_bytes: bool = False) -> "Union[str, bytes]":
        """Download attachment file"""
        if not self.content:
            content = _get_attachment(
                Session.dsms, self.id, self.name, as_bytes
            )
        else:
            content = self.content
        return content


class AttachmentList(list):
    """KItemPropertyList for managing attachments."""

    @property
    def by_name(self) -> "List[str]":
        "Return list of names of attachments"
        return {
            Path(attachment.name).stem
            + Path(attachment.name).suffix: attachment
            for attachment in self
        }

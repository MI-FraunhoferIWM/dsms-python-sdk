"""DSMS KItem Avatar"""

from typing import Optional, Union
from uuid import UUID

from PIL.Image import Image
from pydantic import BaseModel, ConfigDict, Field

from dsms.knowledge.utils import _get_avatar, _make_avatar, print_model


class Avatar(BaseModel):
    """DSMS KItem Avatar"""

    id: Optional[UUID] = Field(
        None,
        description="ID of the KItem",
    )
    file: Optional[Union[Image, str]] = Field(
        None,
        description="The file path to the image when setting a new avatar is set",
    )
    encode_qr: Optional[bool] = Field(
        False,
        description="""Whether the new avatar is supposed to include a qr.
        This can be combined with an image file.""",
    )

    model_config = ConfigDict(arbitrary_types_allowed=True)

    def download(self) -> "Image":
        """Download avatar as PIL Image"""
        return _get_avatar(self.id)

    def generate(self) -> "Image":
        """Generate avatar as PIL Image"""
        return _make_avatar(self.file, self.encode_qr)

    # OVERRIDE
    def __str__(self):
        return print_model(self, "avatar")

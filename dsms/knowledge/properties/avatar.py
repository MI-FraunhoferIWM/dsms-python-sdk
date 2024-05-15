"""DSMS KItem Avatar"""

from typing import Optional, Union

from PIL.Image import Image
from pydantic import ConfigDict, Field

from dsms.knowledge.properties.base import KItemProperty
from dsms.knowledge.utils import _get_avatar, _make_avatar


class Avatar(KItemProperty):
    """DSMS KItem Avatar"""

    file: Optional[Union[Image, str]] = Field(
        None,
        description="The file path to the image when setting a new avatar is set",
    )
    include_qr: Optional[bool] = Field(
        False,
        description="""Whether the new avatar is supposed to include a qr.
        This can be combined with an image file.""",
    )

    model_config = ConfigDict(arbitrary_types_allowed=True)

    def download(self) -> "Image":
        """Download avatar as PIL Image"""
        return _get_avatar(self.kitem)

    def generate(self) -> "Image":
        """Generate avatar as PIL Image"""
        return _make_avatar(self.kitem, self.file, self.include_qr)

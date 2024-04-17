"""DSMS search model"""

from typing import TYPE_CHECKING

from pydantic import BaseModel, Field

if TYPE_CHECKING:
    from dsms import KItem


class SearchResult(BaseModel):
    """DSMS search result"""

    hit: "KItem" = Field(..., description="KItem returned by the search")
    fuzzy: bool = Field(
        ..., description="Whether the KItem was found through a similarity hit"
    )

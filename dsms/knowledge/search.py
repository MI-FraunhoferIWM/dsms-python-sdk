"""DSMS search model"""

from typing import TYPE_CHECKING, List, Union

from pydantic import BaseModel, Field

if TYPE_CHECKING:
    from dsms import KItem


class KItemSearchResult(BaseModel):
    """DSMS search result"""

    kitem: "KItem" = Field(..., description="KItem returned by the search")
    fuzzy: Union[bool, float] = Field(
        ...,
        description="""Whether the KItem was found through a similarity hit.
        If not a bool, a float indicates the distance from search term""",
    )


class SearchResult(BaseModel):
    """DSMS search result"""

    hits: List[KItemSearchResult] = Field(
        ..., description="KItem hits returned by the search"
    )
    total_count: int = Field(..., description="Total number of hits")


class KItemListModel(BaseModel):
    """KItem list model returned by used id"""

    kitems: List["KItem"] = Field(
        ..., description="KItems returned when listed by user id"
    )
    total_count: int = Field(..., description="Total number of hits")

    def __str__(self):
        """Pretty print the KItemList"""
        return "\n".join(
            [str(item) for item in self.kitems]
            + [f"Total count: {self.total_count}"]
        )

    def __repr__(self):
        """Pretty print the KItemList"""
        return str(self)

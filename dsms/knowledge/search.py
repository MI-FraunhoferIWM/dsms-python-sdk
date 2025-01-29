"""DSMS search model"""

from typing import TYPE_CHECKING, Generator, List, Union

import oyaml as yaml
from pydantic import BaseModel, Field

from dsms.core.session import Session

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

    def __str__(self):
        """Pretty print the KItemSearchResult"""
        from dsms.knowledge.utils import dump_model

        return yaml.dump(
            {
                "kitem": dump_model(
                    self.kitem,
                    exclude_extra=Session.dsms.config.hide_properties,
                ),
                "fuzzy": self.fuzzy,
            }
        )

    def __repr__(self):
        """Pretty print the KItemSearchResult"""
        return str(self)


class SearchResult(BaseModel):
    """DSMS search result"""

    hits: List[KItemSearchResult] = Field(
        ..., description="KItem hits returned by the search"
    )
    total_count: int = Field(..., description="Total number of hits")

    def __getitem__(self, key: str) -> "KItemSearchResult":
        """Retrieve a KItemSearchResult from the search result by its index.

        Args:
            key (str): The index of the KItemSearchResult to retrieve.

        Returns:
            KItemSearchResult: The KItemSearchResult at the given index.
        """
        return self.hits[key]

    def __iter__(self) -> "Generator[KItemSearchResult]":
        """Iterate over the hits in the search result."""
        yield from self.hits

    def __str__(self):
        """Pretty print the KItemSearchResult"""
        from dsms.knowledge.utils import dump_model

        return yaml.dump(
            {
                "hits": [
                    {
                        "kitem": dump_model(
                            hit.kitem,
                            exclude_extra=Session.dsms.config.hide_properties,
                        ),
                        "fuzzy": hit.fuzzy,
                    }
                    for hit in self.hits
                ],
                "total_count": self.total_count,
            }
        )

    def __repr__(self):
        """Pretty print the KItemSearchResult"""
        return str(self)


class KItemListModel(BaseModel):
    """KItem list model returned by used id"""

    kitems: List["KItem"] = Field(
        ..., description="KItems returned when listed by user id"
    )
    total_count: int = Field(..., description="Total number of hits")

    def __getitem__(self, key: str) -> "KItem":
        """Retrieve a KItem from the list by its index.

        Args:
            key (str): The index of the KItem to retrieve.

        Returns:
            KItem: The KItem at the given index.

        Raises:
            IndexError: If the index is out of range.
        """
        return self.kitems[key]

    def __iter__(self) -> "Generator[KItem]":
        """Iterate over the KItems in the list."""
        yield from self.kitems

    def __str__(self):
        """Pretty print the KItemList"""
        from dsms.knowledge.utils import dump_model

        return yaml.dump(
            {
                "kitems": [
                    dump_model(
                        kitem,
                        exclude_extra=Session.dsms.config.hide_properties,
                    )
                    for kitem in self.kitems
                ],
                "total_count": self.total_count,
            }
        )

    def __repr__(self):
        """Pretty print the KItemList"""
        return str(self)

"""DSMS KItem Property utils"""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Dict


def _str_to_dict(name: str) -> "Dict[str, str]":
    return {"name": name}

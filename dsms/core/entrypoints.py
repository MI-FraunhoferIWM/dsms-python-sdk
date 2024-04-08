"""DSMS Module defining entrypoints"""
from enum import Enum
import sys
from importlib.metadata import entry_points
from typing import Callable, Dict, Iterable, Union

from dsms.core.attribute_dict import ImmutableDynamicAttributesDict
from dsms.core.entrypoints import DSMSEntrypoints


class DSMSEntrypoints(str, Enum):
    """Enum class defining DSMS entrypoints."""

    SPARQL = "dsms.sparql"



def _get_entrypoints(entrypoint_group: DSMSEntrypoints) -> Iterable:
    if not isinstance(entrypoint_group, DSMSEntrypoints):
        raise TypeError(
            f"""Positional argument for `entrypoint_group`
                         must be of type {DSMSEntrypoints}, not {type(entrypoint_group)}"""
        )
    package_entry_points = entry_points()
    if sys.version_info >= (3, 10):
        return package_entry_points.select(group=entrypoint_group.value)
    return package_entry_points.get(entrypoint_group.value, tuple())


def load_entrypoints(
    entrypoint_group: DSMSEntrypoints, names_only: bool = True
) -> Dict[str, Union[str, Callable]]:
    """Get dictionary for a specific group of available entry points."""
    return {
        entry_point.name: (
            entry_point.name if names_only else entry_point.load()
        )
        for entry_point in _get_entrypoints(entrypoint_group)
    }


def get_entrypoint(name: str, entrypoint_group: DSMSEntrypoints) -> Callable:
    """Load a specific class from an entrypoint."""
    plugins = load_entrypoints(entrypoint_group, names_only=False)
    if name not in plugins:
        raise AttributeError(name)
    return plugins[name]


def make_attribute_dict(
    entrypoint_group: DSMSEntrypoints,
    names_only: bool = True,
) -> ImmutableDynamicAttributesDict:
    """Make entrypoints for immutable dynamic attribute dict."""
    return ImmutableDynamicAttributesDict(
        **load_entrypoints(entrypoint_group, names_only=names_only)
    )


class Registry(ImmutableDynamicAttributesDict):
    """DSMS Registry for enums of types plugins, mappers, queries, etc.
    In order to avoid circular import, the kwargs `load` during initialization
    is set to `False`. If set to `True`, the values of the attributes resolve
    into callbables instead of strings with the names."""

    def __init__(self, load=False) -> None:
        data = {
            obj.name.lower(): make_attribute_dict(obj, names_only=not load)
            for obj in list(DSMSEntrypoints)
        }
        super().__init__(**data)

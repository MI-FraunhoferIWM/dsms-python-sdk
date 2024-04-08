"""DSMS module for immutable dynamic attribute dictionary."""
from typing import Any


class ImmutableDynamicAttributesDict:
    """Generic dictionary which sets items as
    attributes when assigned and stays immutable
    once instanciated."""

    _immutable = False

    @property
    def __dict__(cls):
        return cls._data

    def __init__(self, **kwargs: Any):
        self._data = {**kwargs}
        self._immutable = True

    def _check_immutable(self):
        if self._immutable:
            raise AttributeError(f"{self} is immutable.")

    def __setattr__(self, key, value):
        self._check_immutable()
        if key != "_data":
            self._data[key] = value
        super().__setattr__(key, value)

    def __getattr__(self, key):
        if key in self._data:
            return self._data[key]
        raise AttributeError(f"{self} has no attribute '{key}'")

    def __getitem__(self, key):
        return self._data.get(key, None)

    def __setitem__(self, key, value):
        self._check_immutable()
        self._data[key] = value

    def __delitem__(self, key):
        self._check_immutable()
        del self._data[key]

    def _get_items(self):
        return {
            key: (list(value) if not callable(value) else value)
            for key, value in self._data.items()
            if key != "_immutable"
        }

    def __iter__(self):
        data = self._get_items()
        yield from data.items()

    def get(self, key: Any) -> Any:
        """Get value for key."""
        return self[key]

    def __str__(self):
        items = ", ".join(
            f"{key}={value}"
            for key, value in self._data.items()
            if key != "_immutable"
        )
        return f"{self.__class__.__name__}({items})"


class LoaderResult(ImmutableDynamicAttributesDict):
    """Immutalbe Dynamic Attribute Dict for result from loaders"""

"""DSMS connection module"""

from typing import TYPE_CHECKING, Any, Dict, List

from dsms.apps.utils import _get_available_apps
from dsms.core.configuration import Configuration
from dsms.core.context import Context
from dsms.core.utils import _ping_dsms
from dsms.knowledge.sparql_interface import SparqlInterface
from dsms.knowledge.utils import _search

from dsms.knowledge.utils import (  # isort:skip
    _commit,
    _get_kitem,
    _get_kitem_list,
    _get_remote_ktypes,
)

if TYPE_CHECKING:
    from enum import Enum
    from typing import Optional

    from dsms.apps import App
    from dsms.core.context import Buffers
    from dsms.knowledge.kitem import KItem
    from dsms.knowledge.ktype import KType


class DSMS:
    """General class for connecting and interfacting with DSMS."""

    _context = Context

    def __init__(self, config: Configuration = None, **kwargs) -> None:
        """Initialize the DSMS object."""

        self._config = None
        self._context.dsms = self

        if config is not None and not kwargs:
            self.config = config
        elif config is None:
            self.config = Configuration(**kwargs)
        else:
            raise ValueError(
                """`config`-keyword is defined among others.
                The `config`-keyword is reserved for passing a config-object directly.
                Please specify kwargs for to be passed to the `Configuration`-object _OR_
                an instance of this `Configuration`-object directly."""
            )

        self._sparql_interface = SparqlInterface(self)
        self._ktypes = _get_remote_ktypes()

    def __getitem__(self, key: str) -> "KItem":
        """Get KItem from remote DSMS instance."""
        return _get_kitem(key)

    def __delitem__(self, kitem) -> None:
        """Stage an KItem for the deletion.
        WARNING: Changes only will take place after executing the `commit`-method
        """

        from dsms.knowledge.kitem import (  # isort:skip
            KItem,
        )

        if not isinstance(kitem, KItem):
            raise TypeError(
                f"Object must be of type {KItem}, not {type(kitem)}. "
            )
        kitem.context.buffers.deleted.update({kitem.id: kitem})

    def commit(self) -> None:
        """Commit and empty the buffers of the KItems to the DSMS backend."""
        _commit(self.buffers)
        self.buffers.created = {}
        self.buffers.updated = {}
        self.buffers.deleted = {}

    def search(
        self,
        query: "Optional[str]" = None,
        ktypes: "Optional[List[KType]]" = [],
        annotations: "Optional[List[str]]" = [],
        limit: int = 10,
        allow_fuzzy: "Optional[bool]" = True,
    ) -> "List[KItem]":
        """Search for KItems in the remote backend."""
        return _search(query, ktypes, annotations, limit, allow_fuzzy)

    @property
    def sparql_interface(cls) -> SparqlInterface:
        """Sparql interface of the DSMS instance."""
        return cls._sparql_interface

    @property
    def ktypes(cls) -> "Enum":
        """ "Enum of the KTypes defined in the DSMS instance."""
        return cls._ktypes

    @property
    def config(cls) -> Configuration:
        """Property returning the DSMS Configuration"""
        return cls._config

    @config.setter
    def config(self, value) -> None:
        """Property setter returning the DSMS Configuration"""
        if not isinstance(value, Configuration):
            raise TypeError(
                f"""The passed config-kwarg with value `{value}`
                is not of type `{Configuration}`, but of type {type(value)}."""
            )
        self._config = value
        verify_connection(self)

    @property
    def headers(cls) -> Dict[str, Any]:
        """Request headers for authorization"""
        if cls.config.token:
            header = {
                "Authorization": f"{cls.config.token.get_secret_value()}"
            }
        else:
            header = {}
        return header

    @property
    def kitems(cls) -> "List[KItem]":
        """KItems instanciated and available in the remote backend.
        WARNING: This will download _all_ KItems in the backend owned
        by the current user and may resolve into long response times.
        The default timeout for requests is defined under the
        `request_timeout`-attribute in the `Configuration`-class."""
        return _get_kitem_list()

    @property
    def apps(cls) -> "List[App]":
        """Return available KItem apps in the DSMS"""
        return _get_available_apps()

    @property
    def buffers(cls) -> "Buffers":
        """Return buffers of the DSMS session"""
        return cls._context.buffers

    @property
    def context(cls) -> "Context":
        """Return DSMS context"""
        return cls._context

    @classmethod
    def __get_pydantic_core_schema__(cls):
        """Get validator of the DSMS-object."""
        yield verify_connection


def verify_connection(dsms: DSMS) -> None:
    """Check if DSMS is valid."""
    if not isinstance(dsms, DSMS):
        raise TypeError(
            f"""The passed object for the dsms-connection
                is not of type {DSMS}."""
        )
    try:
        response = _ping_dsms()
        if not response.ok:
            raise ConnectionError(
                f"""Host with `{dsms.config.host_url}`
                gave a response with status code `{response.status_code}`"""
            )
    except Exception as excep:
        raise ConnectionError(
            f"Invalid DSMS instance: `{dsms.config.host_url}`"
        ) from excep
    return dsms

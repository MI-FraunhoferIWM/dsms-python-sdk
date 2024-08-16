"""DSMS connection module"""

import os
from typing import TYPE_CHECKING, Any, Dict, List

from dotenv import load_dotenv

from dsms.apps.utils import _get_available_apps_specs
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

    from dsms.apps import AppConfig
    from dsms.core.context import Buffers
    from dsms.knowledge.kitem import KItem
    from dsms.knowledge.ktype import KType
    from dsms.knowledge.search import SearchResult


class DSMS:
    """
    General class for connecting and interfacing with DSMS.

    This class provides methods to connect to and interact with a DSMS (Data
    Space Management System) instance. It abstracts away the complexities of
    establishing connections and executing queries.

    Args:
        config (Configuration, optional): An optional Configuration object
            containing connection details. If not provided, default
            configurations will be used.
        env (str, optional): An optional string representing the path to the env-file.
            This can be used to select environment-specific configurations. Defaults to None.
        **kwargs: Configurations can also be set as additional keyword arguments instead of
            passing the path to an env-file or the Configuration-object itself.

    """

    _context = Context

    def __init__(
        self,
        config: "Optional[Configuration]" = None,
        env: "Optional[str]" = None,
        **kwargs,
    ) -> None:
        """Initialize the DSMS object.
        Args:
            config (Configuration, optional): An optional Configuration object
                containing connection details. If not provided, default
                configurations will be used.
            env (str, optional): An optional string representing the path to the env-file.
                This can be used to select environment-specific configurations. Content
                of the env-file will be safely loaded using `python-dotenv`.
                Hence the env-variables will be pruned once the kernel is closed.
                Defaults to None.
            **kwargs: Configurations can also be set as additional keyword arguments instead of
                passing the path to an env-file or the Configuration-object itself.
        """

        self._config = None
        self._context.dsms = self

        if env:
            if not os.path.exists(env):
                raise OSError(f"File `{env}` does not exist")
            loaded = load_dotenv(env, verbose=True)
            if not loaded:
                raise RuntimeError(f"Not able to parse .env file: {env}")

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

    def __delitem__(self, obj) -> None:
        """Stage an KItem, KType or AppConfig for the deletion.
        WARNING: Changes only will take place after executing the `commit`-method
        """

        from dsms import KItem, AppConfig, KType  # isort:skip

        if isinstance(obj, KItem):
            self.context.buffers.deleted.update({obj.id: obj})
        elif isinstance(obj, AppConfig):
            self.context.buffers.deleted.update({obj.name: obj})
        elif isinstance(obj, KType):
            raise NotImplementedError("Deletion of KTypes not available yet.")
        else:
            raise TypeError(
                f"Object must be of type {KItem}, {AppConfig} or {KType}, not {type(obj)}. "
            )

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
    ) -> "List[SearchResult]":
        """Search for KItems in the remote backend."""
        return _search(query, ktypes, annotations, limit, allow_fuzzy)

    @property
    def sparql_interface(self) -> SparqlInterface:
        """Sparql interface of the DSMS instance."""
        return self._sparql_interface

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
        """KItems instantiated and available in the remote backend.
        WARNING: This will download _all_ KItems in the backend owned
        by the current user and may resolve into long response times.
        The default timeout for requests is defined under the
        `request_timeout`-attribute in the `Configuration`-class."""
        return _get_kitem_list()

    @property
    def app_configs(cls) -> "List[AppConfig]":
        """Return available app configs in the DSMS"""
        from dsms.apps import AppConfig

        return [
            AppConfig(**app_config)
            for app_config in _get_available_apps_specs()
        ]

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
    if dsms.config.ping_dsms:
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

"""DSMS connection module"""

import os
import warnings
from enum import Enum
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Union
from uuid import UUID

from dotenv import load_dotenv

from dsms.apps.config import AppConfig
from dsms.apps.utils import _get_available_apps_specs
from dsms.core.configuration import Configuration
from dsms.core.session import Session
from dsms.core.utils import _ping_backend
from dsms.knowledge.kitem import KItem
from dsms.knowledge.ktype import (
    CreateKTypeRequest,
    KType,
    KTypeSpec,
    KTypeSpecPayload,
    KTypeV2,
    ProcessSchema,
    RemoteDiffOut,
    RemoteKTypeSummary,
    RemoteKTypeVersion,
    RemoteSchemaInfo,
)
from dsms.knowledge.sparql_interface import SparqlInterface
from dsms.knowledge.utils import _search

from dsms.knowledge.utils import (  # isort:skip
    _add_group_member,
    _add_group_to_group,
    _commit,
    _create_group,
    _delete_group,
    _get_group_members,
    _get_group_subgroups,
    _get_kitem,
    _get_kitem_list,
    _get_ktypes_by_parent,
    _get_remote_ktypes,
    _get_process_schemas,
    _get_webform_schemas,
    _get_schema_data,
    _get_user_groups,
    _get_user_list,
    _remove_group_from_group,
    _remove_group_member,
    _update_group,
    _v2_create_ktype,
    _v2_delete_ktype,
    _v2_export_ktype,
    _v2_get_ktype,
    _v2_import_ktype,
    _v2_list_ktypes,
    _v2_list_remote_ktypes,
    _v2_list_remote_schemas,
    _v2_list_remote_versions,
    _v2_refresh_ktype,
    _v2_remote_diff,
    _v2_restore_stash,
    _v2_update_ktype,
    get_user_by_id,
)

if TYPE_CHECKING:
    from dsms.core.session import Buffers
    from dsms.knowledge.groups import Group, GroupList, User
    from dsms.knowledge.properties.schema_data import KItemSchemaData
    from dsms.knowledge.search import KItemListModel, SearchResult


warnings.simplefilter("always", DeprecationWarning)


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

    _session = Session

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
        self._ktypes = None
        self._user_groups = None
        self._users = None
        self._session.dsms = self

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
            raise ValueError("""`config`-keyword is defined among others.
                The `config`-keyword is reserved for passing a config-object directly.
                Please specify kwargs for to be passed to the `Configuration`-object _OR_
                an instance of this `Configuration`-object directly.""")

        from dsms.knowledge.groups.public import refresh_public_groups

        refresh_public_groups(self.config)

        self._sparql_interface = SparqlInterface(self)
        if self.config.auto_fetch_ktypes:
            _get_remote_ktypes(self)

    def __getitem__(self, key: str) -> "KItem":
        """Get KItem from remote DSMS instance."""
        return self._session.kitems.get(key) or _get_kitem(self, key)

    def __delitem__(self, obj) -> None:
        """Stage an KItem, KType or AppConfig for the deletion.
        WARNING: Changes only will take place after executing the `commit`-method
        """
        if isinstance(obj, (KItem, KType, ProcessSchema)) or (
            isinstance(obj, Enum)
            and isinstance(obj.value, (KType, ProcessSchema))
        ):
            self.buffers.deleted.update({str(obj.id): obj})
        elif isinstance(obj, AppConfig):
            self.buffers.deleted.update({str(obj.name): obj})
        else:
            raise TypeError(
                f"""Object must be of type {KItem}, {AppConfig}, {ProcessSchema} or {KType}.
                Not {type(obj)}. """
            )

    def delete(
        self,
        obj: Union[
            KItem,
            KType,
            AppConfig,
            ProcessSchema,
            List[Union[KItem, KType, AppConfig, ProcessSchema]],
        ],
    ) -> None:
        """Stage an KItem, KType or AppConfig for the deletion.
        WARNING: Changes only will take place after executing the `commit`-method
        """
        if isinstance(obj, list):
            for o in obj:
                self._del(o)
        else:
            self._del(obj)

    def _del(self, obj: Union[KItem, KType, AppConfig]):
        del self[obj]

    def add(
        self,
        obj: Union[
            KItem,
            KType,
            AppConfig,
            ProcessSchema,
            List[Union[KItem, KType, AppConfig, ProcessSchema]],
        ],
    ) -> None:
        """Stage an KItem, KType or AppConfig for the addition.
        WARNING: Changes only will take place after executing the `commit`-method

        Args:
            obj (Union[KItem, KType, AppConfig, List[Union[KItem, KType, AppConfig]]]):
                The object to be added.
        """
        if isinstance(obj, list):
            for o in obj:
                self._add(o)
        else:
            self._add(obj)

    def _add(self, obj: Union[KItem, KType, AppConfig]):
        if isinstance(obj, (KItem, KType)) or (
            isinstance(obj, Enum) and isinstance(obj.value, KType)
        ):
            self.buffers.added.update({str(obj.id): obj})
        elif isinstance(obj, AppConfig):
            self.buffers.added.update({str(obj.name): obj})
        else:
            raise TypeError(
                f"Object must be of type {KItem}, {AppConfig} or {KType}, not {type(obj)}. "
            )

    def commit(self) -> None:
        """Commit and empty the buffers of the KItems to the DSMS backend."""
        if len(self.buffers.added) == 0 and len(self.buffers.deleted) == 0:
            warnings.warn(
                "Nothing to commit. No changes have been made to the DSMS instance."
                "If you would like to add&/delete KItems, KTypes or AppConfigs,"
                "please use: `dsms.add(my_object)` or dsms.delete(my_object)`"
                "before running `dsms.commit()`."
            )
        _commit(self.buffers)
        self.buffers.clear()

    def search(
        self,
        query: "Optional[str]" = None,
        ktypes: "Optional[List[Union[Enum, KType]]]" = [],
        annotations: "Optional[List[str]]" = [],
        limit: int = 10,
        offset: int = 0,
        allow_fuzzy: "Optional[bool]" = True,
        compact: "Optional[bool]" = False,
        contexts: "Optional[List[str]]" = None,
        attachment_extensions: "Optional[List[str]]" = None,
    ) -> "List[SearchResult]":
        """Search for KItems in the remote backend."""
        return _search(
            self,
            query,
            ktypes,
            annotations,
            limit,
            offset,
            allow_fuzzy,
            compact,
            contexts,
            attachment_extensions,
        )

    @property
    def sparql_interface(self) -> SparqlInterface:
        """Sparql interface of the DSMS instance."""
        return self._sparql_interface

    @property
    def process_schemas(self) -> "Dict[UUID, ProcessSchema]":
        """Process schemas interface of the DSMS instance."""
        return _get_process_schemas(self)

    @property
    def webform_schemas(self) -> "Dict[UUID, ProcessSchema]":
        """Process schemas interface of the DSMS instance."""
        return _get_webform_schemas(self)

    @property
    def ktypes(self) -> "Enum":
        """Getter for the Enum of the KTypes defined in the DSMS instance."""
        if self._ktypes is None or self.config.always_refetch_ktypes:
            _get_remote_ktypes(self)
        return self._ktypes

    def refresh_ktypes(self) -> None:
        """Refresh the KTypes from the remote backend.

        This method should be called if the KTypes from the remote backend
        have been modified outside of this DSMS instance. It will update the
        local KType Enum with the new KTypes from the remote backend."""
        _get_remote_ktypes(self)

    @ktypes.setter
    def ktypes(self, value: "Enum") -> None:
        """Setter for the ktypes property of the DSMS instance.

        Args:
            value: the Enum object to be set as the ktypes property.
        """
        self._ktypes = value

    @property
    def config(self) -> Configuration:
        """Property returning the DSMS Configuration"""
        return self._config

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
    def headers(self) -> Dict[str, Any]:
        """Request headers for authorization"""
        if self.config.token:
            header = {
                "Authorization": f"{self.config.token.get_secret_value()}"
            }
        else:
            header = {}
        return header

    @property
    def kitems(self) -> "KItemListModel":
        """
        **DEPRECATED**

        Return the first 10 KItems from the remote backend.

        .. warning::
            This property is deprecated and only returns the 10 first kitems.
            Please use the `get_kitems`-method instead.

        Returns:
            KItemListModel: The first 10 KItems from the remote backend.
        """
        message = """`kitems`-property is deprecated and only returns the 10 first kitems.
        Please use the `get_kitems`-method instead."""
        warnings.warn(message, DeprecationWarning)
        return _get_kitem_list(self)

    def get_kitems(
        self,
        user_id: Optional[str] = None,
        limit=10,
        offset=0,
        name: Optional[str] = None,
    ) -> "KItemListModel":
        """
        Get all available KItems from the remote backend.

        Args:
            user_id (str, optional): Filter by user ID.
            limit (int): The amount of KItems to be returned. Defaults to 10.
            offset (int): The offset in the list of KItems. Defaults to 0.
            name (str, optional): Filter by KItem name.

        """
        return _get_kitem_list(
            self, user_id=user_id, limit=limit, offset=offset, name=name
        )

    @property
    def app_configs(self) -> "List[AppConfig]":
        """Return available app configs in the DSMS"""
        return [
            AppConfig(**app_config)
            for app_config in _get_available_apps_specs(self)
        ]

    @property
    def buffers(self) -> "Buffers":
        """Return buffers of the DSMS session"""
        return self._session.buffers

    @property
    def session(self) -> "Session":
        """Return DSMS session"""
        return self._session

    @property
    def user_groups(self) -> "List[Group]":
        """Return user groups, fetching from the backend on first access.

        Results are cached for the lifetime of this DSMS instance.
        Call refresh_user_groups() to force a re-fetch.
        """
        if self._user_groups is None:
            self._user_groups = _get_user_groups(self)
        return self._user_groups

    def refresh_user_groups(self) -> None:
        """Re-fetch user groups from the backend and update the local cache."""
        self._user_groups = _get_user_groups(self)

    @property
    def users(self) -> "List[User]":
        """Return all users, fetching from the backend on first access.

        Results are cached for the lifetime of this DSMS instance.
        Call refresh_users() to force a re-fetch.
        """
        if self._users is None:
            self._users = _get_user_list(self)
        return self._users

    def refresh_users(self) -> None:
        """Re-fetch users from the backend and update the local cache."""
        self._users = _get_user_list(self)

    def get_user(self, user_id: str) -> "User":
        """Fetch a single user by ID from the backend.

        Args:
            user_id: The unique identifier of the user.

        Returns:
            User object for the given ID.
        """
        return get_user_by_id(self, user_id)

    def get_group_members(self, group_id: str) -> "List[User]":
        """Fetch the members of a group (including subgroup members).

        Args:
            group_id: The unique identifier of the group.

        Returns:
            List of User objects belonging to the group.
        """
        return _get_group_members(self, group_id)

    def create_group(
        self,
        name: str,
        description: str = "",
        parent_id: Optional[str] = None,
    ) -> "Group":
        """Create a new group.

        Args:
            name: Name of the group.
            description: Optional description.
            parent_id: ID of the parent group. If None, creates a top-level group.

        Returns:
            The created Group object.
        """
        from dsms.knowledge.groups import Group  # noqa: F401

        group = _create_group(self, name, description, parent_id)
        self._user_groups = None  # invalidate cache
        return group

    def update_group(
        self,
        group_id: str,
        name: Optional[str] = None,
        description: Optional[str] = None,
    ) -> "Group":
        """Update the name or description of an existing group.

        Args:
            group_id: The unique identifier of the group.
            name: New name. Pass None to leave unchanged.
            description: New description. Pass None to leave unchanged.

        Returns:
            The updated Group object.
        """
        from dsms.knowledge.groups import Group  # noqa: F401

        group = _update_group(self, group_id, name, description)
        self._user_groups = None  # invalidate cache
        return group

    def delete_group(self, group_id: str) -> None:
        """Delete a group.

        Args:
            group_id: The unique identifier of the group to delete.
        """
        _delete_group(self, group_id)
        self._user_groups = None  # invalidate cache

    def add_group_member(self, group_id: str, user_id: str) -> None:
        """Add a user to a group.

        Args:
            group_id: The unique identifier of the group.
            user_id: The unique identifier of the user to add.
        """
        _add_group_member(self, group_id, user_id)

    def remove_group_member(self, group_id: str, user_id: str) -> None:
        """Remove a user from a group.
        Args:
            group_id: The unique identifier of the group.
            user_id: The unique identifier of the user to remove.
        """
        _remove_group_member(self, group_id, user_id)

    def get_group_subgroups(self, group_id: str) -> "GroupList":
        """Return the direct child groups of a group.

        Args:
            group_id: The unique identifier of the parent group.

        Returns:
            GroupList of direct child groups.
        """
        return _get_group_subgroups(self, group_id)

    def add_group_to_group(self, parent_id: str, child_id: str) -> None:
        """Link an existing group as a direct child of another group.

        The child group is moved in the hierarchy; its members and any of its
        own subgroups are preserved. Members of the child group are resolved
        recursively when listing the parent group's members.

        Args:
            parent_id: The unique identifier of the parent group.
            child_id: The unique identifier of the group to nest as a child.
        """
        _add_group_to_group(self, parent_id, child_id)
        self._user_groups = None

    def remove_group_from_group(self, parent_id: str, child_id: str) -> None:
        """Detach a child group from its parent and promote it back to top-level.

        Args:
            parent_id: The unique identifier of the parent group.
            child_id: The unique identifier of the child group to detach.
        """
        _remove_group_from_group(self, parent_id, child_id)
        self._user_groups = None

    def get_schema_data(self, kitem_id: str) -> "List[KItemSchemaData]":
        """Fetch all schema-data entries for a KItem from the remote backend.

        Args:
            kitem_id: The unique identifier of the KItem.

        Returns:
            List of KItemSchemaData entries.
        """
        from dsms.knowledge.properties.schema_data import KItemSchemaData

        return [
            KItemSchemaData(**entry)
            for entry in _get_schema_data(self, kitem_id)
        ]

    # ------------------------------------------------------------------
    # KType helpers
    # ------------------------------------------------------------------

    def get_ktypes_by_parent(self, parent_id: str) -> List[KType]:
        """Return KTypes whose extends chain contains parent_id."""
        return [KType(**kt) for kt in _get_ktypes_by_parent(self, parent_id)]

    # ------------------------------------------------------------------
    # KType v2 API
    # ------------------------------------------------------------------

    def get_v2_ktypes(self) -> List[KTypeV2]:
        """List all v2 KTypes (spec=None for v1-only types)."""
        return [KTypeV2(**kt) for kt in _v2_list_ktypes(self)]

    def get_v2_ktype(self, ktype_id: str) -> KTypeV2:
        """Fetch a single v2 KType by ID."""
        return KTypeV2(**_v2_get_ktype(self, ktype_id))

    def create_v2_ktype(self, request: CreateKTypeRequest) -> KTypeV2:
        """Create or upgrade a KType to v2."""
        return KTypeV2(
            **_v2_create_ktype(self, request.model_dump(exclude_none=True))
        )

    def import_v2_ktype(self, url: str) -> KTypeV2:
        """Import a KType spec from a GitHub URL."""
        return KTypeV2(**_v2_import_ktype(self, url))

    def update_v2_ktype(
        self, ktype_id: str, payload: KTypeSpecPayload
    ) -> KTypeV2:
        """Partially update a v2 KType spec."""
        return KTypeV2(
            **_v2_update_ktype(
                self, ktype_id, payload.model_dump(exclude_none=True)
            )
        )

    def delete_v2_ktype(self, ktype_id: str) -> None:
        """Delete a v2 KType (blocked if KItems exist)."""
        _v2_delete_ktype(self, ktype_id)

    def restore_v2_ktype_stash(self, ktype_id: str) -> KTypeV2:
        """Restore the pre-import stash for a v2 KType."""
        return KTypeV2(**_v2_restore_stash(self, ktype_id))

    def refresh_v2_ktype(self, ktype_id: str) -> KTypeV2:
        """Re-fetch a v2 KType spec from its stored source URL."""
        return KTypeV2(**_v2_refresh_ktype(self, ktype_id))

    def export_v2_ktype(self, ktype_id: str) -> str:
        """Download a v2 KType spec as YAML text."""
        return _v2_export_ktype(self, ktype_id)

    def get_v2_ktype_spec(self, ktype_id: str) -> Optional[KTypeSpec]:
        """Return the KTypeSpec for a v2 KType, or None if not a v2 type."""
        return self.get_v2_ktype(ktype_id).spec

    def list_remote_v2_ktypes(self) -> List[RemoteKTypeSummary]:
        """List KTypes available in the remote GitHub repository."""
        return [
            RemoteKTypeSummary(**kt) for kt in _v2_list_remote_ktypes(self)
        ]

    def list_remote_schemas(self) -> List[RemoteSchemaInfo]:
        """List semantic schemas available in the remote GitHub repository."""
        return [RemoteSchemaInfo(**s) for s in _v2_list_remote_schemas(self)]

    def list_remote_ktype_versions(
        self, ktype_id: str
    ) -> List[RemoteKTypeVersion]:
        """List all GitHub-tagged versions of a v2 KType."""
        return [
            RemoteKTypeVersion(**v)
            for v in _v2_list_remote_versions(self, ktype_id)
        ]

    def get_v2_ktype_remote_diff(self, ktype_id: str) -> RemoteDiffOut:
        """Compare the local v2 KType spec against the latest remote version."""
        return RemoteDiffOut(**_v2_remote_diff(self, ktype_id))

    @classmethod
    def __get_pydantic_core_schema__(cls):
        """Get validator of the DSMS-object."""
        yield verify_connection


def verify_connection(dsms: DSMS) -> None:
    """Check if DSMS is valid."""
    if not isinstance(dsms, DSMS):
        raise TypeError(f"""The passed object for the dsms-connection
                is not of type {DSMS}.""")
    if dsms.config.ping_backend:
        try:
            response = _ping_backend(dsms)
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

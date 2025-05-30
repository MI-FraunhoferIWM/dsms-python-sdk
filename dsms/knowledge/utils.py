"""DSMS knowledge utilities"""
import base64
import io
import logging
import random
import re
import string
import time
import warnings
from enum import Enum
from pathlib import Path
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Union
from uuid import UUID

import oyaml as yaml
import pandas as pd
import segno
from PIL import Image
from requests import Response

from dsms.core.logging import handler  # isort:skip

from dsms.core.utils import _name_to_camel, _perform_request  # isort:skip

from dsms.knowledge.search import SearchResult, KItemListModel  # isort:skip^

from dsms.core.session import Session  # isort:skip

if TYPE_CHECKING:
    from dsms import DSMS
    from dsms.apps import AppConfig
    from dsms.core.session import Buffers
    from dsms.knowledge import KItem, KType
    from dsms.knowledge.properties import Attachment

logger = logging.getLogger(__name__)
logger.addHandler(handler)
logger.propagate = False


def _is_number(value):
    try:
        float(value)
        return True
    except Exception:
        return False


def print_model(self, key, exclude_extra: set = set()) -> str:
    """Pretty print the ktype fields"""
    dumped = dump_model(self, exclude_extra)
    return yaml.dump({key: dumped})


def dump_model(self, exclude_extra: set = set()) -> Dict[str, Any]:
    """
    Dump the model fields into a dictionary format with optional exclusions.

    This method converts the model's fields into a dictionary while allowing
    specific fields to be excluded. UUID fields are converted to string
    representation.

    Args:
        exclude_extra (set): Additional fields to exclude from the dump.

    Returns:
        Dict[str, Any]: A dictionary of the model fields with specified exclusions.
    """
    exclude = self.model_config.get("exclude", set()) | exclude_extra
    dumped = self.model_dump(
        exclude_none=True,
        exclude_unset=True,
        exclude=exclude,
    )
    return {
        key: (str(value) if isinstance(value, UUID) else value)
        for key, value in dumped.items()
    }


def print_ktype(self) -> str:
    """Pretty print the ktype fields"""
    return print_model(self, "ktype")


def _get_remote_ktypes(dsms: "DSMS") -> Enum:
    """Get the KTypes from the remote backend"""
    from dsms import (  # isort:skip
        KType,
    )

    response = _perform_request(dsms, "api/knowledge-type/", "get")
    if not response.ok:
        raise ConnectionError(
            f"Something went wrong fetching the remote ktypes: {response.text}"
        )

    dsms.session.ktypes = {
        ktype["id"]: KType(**ktype) for ktype in response.json()
    }

    ktypes = Enum(
        "KTypes",
        {
            _name_to_camel(key): value
            for key, value in dsms.session.ktypes.items()
        },
    )

    def custom_getattr(self, name) -> None:
        """
        Custom getattr method for the Enum of KTypes.

        When a KType field is accessed, first check if the field is an attribute of the
        underlying KType object (self.value). If it is, return that.
        Otherwise, call the super method to access the Enum field.

        This is needed because the Enum object is not a KType object, but has all the same
        fields. This allows us to access the fields of the KType object as if it were an
        Enum.
        """
        if hasattr(self.value, name):
            return getattr(self.value, name)
        return super(ktypes, self).__getattr__(name)

    def custom_setattr(self, name, value) -> None:
        """
        Custom setattr method for the Enum of KTypes.

        When a KType field is set, first check if the field is an attribute of the
        underlying KType object (self.value). If it is, set that.
        Otherwise, call the super method to set the Enum field.

        This is needed because the Enum object is not a KType object, but has all the same
        fields. This allows us to set the fields of the KType object as if it were an
        Enum.
        """

        if hasattr(self.value, name):
            setattr(self.value, name, value)
        else:
            super(ktypes, self).__setattr__(name, value)

    # Attach methods to the dynamically created Enum class
    setattr(ktypes, "__getattr__", custom_getattr)
    setattr(ktypes, "__setattr__", custom_setattr)
    setattr(ktypes, "__str__", print_ktype)
    setattr(ktypes, "__repr__", print_ktype)

    logger.debug("Got the following ktypes from backend: `%s`.", list(ktypes))
    dsms.ktypes = ktypes


def _create_new_ktype(ktype: "KType") -> None:
    """Create a new KType in the remote backend"""
    body = {
        "name": ktype.name,
        "id": str(ktype.id),
    }
    logger.debug("Create new KType with body: %s", body)
    response = _perform_request(
        ktype.dsms, "api/knowledge-type/", "post", json=body
    )
    if not response.ok:
        raise ValueError(
            f"KType with id `{ktype.id}` could not be created in DSMS: {response.text}`"
        )


def _get_ktype(
    dsms: "DSMS",
    ktype_id: str,
    as_json=False,
    raise_error=True,
) -> "Union[KType, Dict[str, Any]]":
    """Get the KType for an instance with a certain ID from remote backend"""
    from dsms import KType

    ktype = None

    response = _perform_request(dsms, f"api/knowledge-type/{ktype_id}", "get")
    if response.status_code == 404 and raise_error:
        raise ValueError(
            f"""KType with the id `{ktype_id}` does not exist in
            DSMS-instance `{dsms.config.host_url}`"""
        )
    if not response.ok and raise_error:
        raise ValueError(
            f"""An error occured fetching the KType with id `{ktype_id}`:
            `{response.text}`"""
        )
    if response.ok:
        body = response.json()
        if as_json:
            ktype = body
        else:
            ktype = KType(**body)
    return ktype


def _update_ktype(dsms: "DSMS", ktype: "KType") -> Response:
    """Update a KType in the remote backend."""
    payload = ktype.model_dump(
        exclude_none=True,
        by_alias=True,
    )
    logger.debug("Update KType for `%s` with body: %s", ktype.id, payload)
    response = _perform_request(
        dsms, f"api/knowledge-type/{ktype.id}", "put", json=payload
    )
    if not response.ok:
        raise ValueError(
            f"KType with uuid `{ktype.id}` could not be updated in DSMS: {response.text}`"
        )
    return response


def _delete_ktype(ktype: "KType") -> None:
    """Delete a KType in the remote backend"""

    logger.debug("Delete KType with id: %s", ktype.id)
    response = _perform_request(
        ktype.dsms, f"api/knowledge-type/{ktype.id}", "delete"
    )
    if not response.ok:
        raise ValueError(
            f"KItem with uuid `{ktype.id}` could not be deleted from DSMS: `{response.text}`"
        )
    _get_remote_ktypes(ktype.dsms)


def _get_kitem_list(dsms: "DSMS", limit=10, offset=0) -> "KItemListModel":
    """Get all available KItems from the remote backend."""
    from dsms.knowledge.kitem import KItem  # isort:skip

    response = _perform_request(
        dsms,
        "api/knowledge/kitems",
        "get",
        params={
            "limit": limit,
            "offset": offset,
        },
    )
    if not response.ok:
        raise ValueError(
            f"Something went wrong fetching the available kitems: {response.text}"
        )
    payload = response.json()
    kitems = {
        "kitems": [KItem(**kitem) for kitem in payload["kitems"]],
        "total_count": payload["total_count"],
    }
    return KItemListModel(**kitems)


def _kitem_exists(dsms: "DSMS", kitem: Union[str, UUID, "KItem"]) -> bool:
    """Check whether the KItem exists in the remote backend"""
    if not isinstance(kitem, (str, UUID)):
        route = f"api/knowledge/kitems/{kitem.id}"
    else:
        route = f"api/knowledge/kitems/{kitem}"
    response = _perform_request(dsms, route, "get")
    return response.ok


def _get_kitem(
    dsms: "DSMS", uuid: Union[str, UUID], as_json=False, raise_error=True
) -> "Optional[Union[Dict[str, Any], KItem]]":
    """Get the KItem for a instance with a certain ID from remote backend"""
    from dsms import KItem

    kitem = None

    response = _perform_request(dsms, f"api/knowledge/kitems/{uuid}", "get")
    if response.status_code == 404 and raise_error:
        raise ValueError(
            f"""KItem with uuid `{uuid}` does not exist in
            DSMS-instance `{dsms.config.host_url}`"""
        )
    if not response.ok and raise_error:
        raise ValueError(
            f"""An error occured fetching the KItem with uuid `{uuid}`:
            `{response.text}`"""
        )
    if response.ok:
        payload = response.json()
        if as_json:
            kitem = payload
        else:
            kitem = KItem(**payload)
    return kitem


def _create_new_kitem(kitem: "KItem") -> "Dict[str, Any]":
    """Create a new KItem in the remote backend"""
    payload = {
        "name": kitem.name,
        "id": str(kitem.id),
        "slug": kitem.slug,
        "ktype_id": kitem.ktype.id,
    }
    logger.debug("Create new KItem with payload: %s", payload)
    response = _perform_request(
        kitem.dsms, "api/knowledge/kitems", "post", json=payload
    )
    if not response.ok:
        raise ValueError(
            f"KItem with uuid `{kitem.id}` could not be created in DSMS: {response.text}`"
        )
    return response.json()


def _update_kitem(new_kitem: "KItem", old_kitem: "Dict[str, Any]") -> Response:
    """Update a KItem in the remote backend."""
    differences = _get_kitems_diffs(old_kitem, new_kitem)
    payload = new_kitem.model_dump(
        exclude={
            "authors",
            "avatar",
            "annotations",
            "linked_kitems",
            "updated_at",
            "rdf_exists",
            "in_backend",
            "avatar_exists",
            "user_groups",
            "ktype_id",
            "attachments",
            "id",
            "apps",
            "created_at",
            "dataframe",
            "access_url",
        },
        exclude_defaults=True,
    )
    payload.update(
        **differences,
    )
    logger.debug(
        "Update KItem for `%s` with payload: %s", new_kitem.id, payload
    )
    response = _perform_request(
        new_kitem.dsms,
        f"api/knowledge/kitems/{new_kitem.id}",
        "put",
        json=payload,
    )
    if not response.ok:
        raise ValueError(
            f"KItem with uuid `{new_kitem.id}` could not be updated in DSMS: {response.text}`"
        )
    return response


def _delete_kitem(kitem: "KItem") -> None:
    """Delete a KItem in the remote backend"""
    logger.debug("Delete KItem with id: %s", kitem.id)
    response = _perform_request(
        kitem.dsms, f"api/knowledge/kitems/{kitem.id}", "delete"
    )
    if not response.ok:
        raise ValueError(
            f"KItem with uuid `{kitem.id}` could not be deleted from DSMS: `{response.text}`"
        )


def _update_attachments(
    new_kitem: "KItem", old_kitem: "Dict[str, Any]"
) -> None:
    """Update attachments of the KItem."""
    differences = _get_attachment_diffs(old_kitem, new_kitem)
    logger.debug(
        "Found differences in attachments for kitem with id `%s`: %s",
        new_kitem.id,
        differences,
    )
    for upload in differences["add"]:
        _upload_attachments(new_kitem, upload)
    for remove in differences["remove"]:
        _delete_attachments(new_kitem, remove)


def _upload_attachments(kitem: "KItem", attachment: "Attachment") -> None:
    """Upload the attachments of the KItem"""
    path = Path(attachment.name)

    if path.is_file() and not attachment.content:
        if not path.exists():
            raise FileNotFoundError(f"File {path} does not exist.")

        with open(path, mode="rb") as file:
            upload_file = {"dataFile": file}
            response = _perform_request(
                kitem.dsms,
                f"api/knowledge/attachments/{kitem.id}",
                "put",
                files=upload_file,
            )
        if not response.ok:
            raise RuntimeError(
                f"Could not upload attachment `{path}`: {response.text}"
            )
    elif not path.is_file() and attachment.content:
        if isinstance(attachment.content, str):
            file = io.StringIO(attachment.content)
        elif isinstance(attachment.content, bytes):
            file = io.BytesIO(attachment.content)
        else:
            raise TypeError(
                f"""Invalid content type of attachment with name
                `{attachment.name}`: {type(attachment.content)}"""
            )
        file.name = attachment.name
        upload_file = {"dataFile": file}
        response = _perform_request(
            kitem.dsms,
            f"api/knowledge/attachments/{kitem.id}",
            "put",
            files=upload_file,
        )
        if not response.ok:
            raise RuntimeError(
                f"Could not upload attachment `{path}`: {response.text}"
            )
    else:
        raise RuntimeError(
            f"""Invalid file path, attachment name or attachment content:
            name={attachment.name},content={attachment.content}"""
        )


def _delete_attachments(kitem: "KItem", file_name: str) -> None:
    """Delete attachment from KItem"""
    url = f"api/knowledge/attachments/{kitem.id}/{file_name}"
    response = _perform_request(kitem.dsms, url, "delete")
    if not response.ok:
        raise RuntimeError(
            f"Could not delete attachment `{file_name}`: {response.text}"
        )


def _get_attachment(
    dsms: "DSMS", kitem_id: "KItem", file_name: str, as_bytes: bool
) -> Union[str, bytes]:
    """Download attachment from KItem"""
    url = f"api/knowledge/attachments/{kitem_id}/{file_name}"
    response = _perform_request(dsms, url, "get")
    if not response.ok:
        raise RuntimeError(
            f"Download for attachment `{file_name}` was not successful: {response.text}"
        )
    if not as_bytes:
        content = response.text
    else:
        content = response.content
    return content


def _get_apps_diff(
    old_kitem: "Dict[str, Any]", new_kitem: "KItem"
) -> "Dict[str, List[Dict[str, Any]]]":
    """Get differences in kitem apps from previous KItem state"""
    differences = {}
    exclude = {"id", "kitem_app_id"}
    old_apps = [
        {key: value for key, value in old.items() if key not in exclude}
        for old in old_kitem.get("kitem_apps")
    ]
    new_apps = [new.model_dump() for new in new_kitem.apps]
    differences["kitem_apps_to_update"] = [
        attr for attr in new_apps if attr not in old_apps
    ]
    differences["kitem_apps_to_remove"] = [
        attr for attr in old_apps if attr not in new_apps
    ]
    logger.debug("Found differences in KItem apps: %s", differences)
    return differences


def _get_linked_diffs(
    old_kitem: "Dict[str, Any]", new_kitem: "KItem"
) -> "Dict[str, List[Dict[str, UUID]]]":
    """Get differences in linked kitem from previous KItem state"""
    differences = {}
    old_linked = [old.get("id") for old in old_kitem.get("linked_kitems")]
    new_linked = [str(new_kitem.id) for new_kitem in new_kitem.linked_kitems]
    differences["kitems_to_link"] = [
        {"id": attr} for attr in new_linked if attr not in old_linked
    ]
    differences["kitems_to_unlink"] = [
        {"id": attr} for attr in old_linked if attr not in new_linked
    ]
    logger.debug("Found differences in linked KItems: %s", differences)
    return differences


def _get_attachment_diffs(kitem_old: "Dict[str, Any]", kitem_new: "KItem"):
    """Check which attachments should be removed and which should be added."""
    old_attachments = [
        attachment.get("name")
        for attachment in kitem_old.get("attachments")
        if attachment.get("name")
    ]
    return {
        "remove": [
            attachment
            for attachment in old_attachments
            if attachment not in kitem_new.attachments.by_name
        ],
        "add": [
            attachment
            for name, attachment in kitem_new.attachments.by_name.items()
            if name not in old_attachments or attachment.content
        ],
    }


def _get_kitems_diffs(kitem_old: "Dict[str, Any]", kitem_new: "KItem"):
    """Get the differences in the attributes between two kitems"""
    differences = {}
    attributes = [
        ("annotations", ("annotations", "link", "unlink")),
        ("user_groups", ("user_groups", "add", "remove")),
    ]
    to_compare = kitem_new.model_dump(include={"annotations", "user_groups"})
    for name, terms in attributes:
        to_add_name = terms[0] + "_to_" + terms[1]
        to_remove_name = terms[0] + "_to_" + terms[2]
        old_attr = kitem_old.get(name)
        new_attr = to_compare.get(name)
        differences[to_add_name] = [
            attr for attr in new_attr if attr not in old_attr
        ]
        differences[to_remove_name] = [
            attr for attr in old_attr if attr not in new_attr
        ]
    logger.debug(
        "Found differences between new and old KItem: %s", differences
    )
    # linked kitems need special treatment since the linked target
    # kitems also might differ in their new properties in some cases.
    linked_kitems = _get_linked_diffs(kitem_old, kitem_new)
    # same holds for kitem apps
    apps = _get_apps_diff(kitem_old, kitem_new)
    # merge with previously found differences
    differences.update(**linked_kitems, **apps)
    return differences


def _commit(buffers: "Buffers") -> None:
    """Commit the buffers for the
    created, updated and deleted buffers"""
    from dsms import AppConfig, KItem, KType

    logger.debug("Committing KItems in buffers. Current buffers:")
    logger.debug("Current Addded-buffer: %s", buffers.added)
    logger.debug("Current Deleted-buffer: %s", buffers.deleted)
    had_ktypes = False
    for obj in buffers.added.values():
        if isinstance(obj, KItem):
            old_kitem = _get_kitem(
                obj.dsms, obj.id, as_json=True, raise_error=False
            )

            if not old_kitem and not _slug_is_available(
                obj.dsms, obj.ktype_id, obj.slug
            ):
                raise ValueError(f"Slug for `{obj.slug}` is already taken.")
            if not old_kitem:
                old_kitem = _create_new_kitem(obj)
            if isinstance(obj.dataframe, pd.DataFrame):
                logger.debug(
                    "New KItem data has `pd.DataFrame`. Will push as dataframe."
                )
                _update_dataframe(obj.dsms, obj.id, obj.dataframe)
                obj.dataframe = [
                    {"id": obj.id, **column}
                    for column in _inspect_dataframe(obj.dsms, obj.id)
                ]
            elif isinstance(obj.dataframe, type(None)) and _inspect_dataframe(
                obj.dsms, obj.id
            ):
                _delete_dataframe(obj.id)
            _update_kitem(obj, old_kitem)
            _update_attachments(obj, old_kitem)
            if obj.avatar.file or obj.avatar.encode_qr:
                _commit_avatar(obj)
        elif isinstance(obj, KType) or (
            isinstance(obj, Enum) and isinstance(obj.value, KType)
        ):
            old_ktype = _get_ktype(
                obj.dsms, obj.id, as_json=True, raise_error=False
            )
            if not old_ktype:
                _create_new_ktype(obj)
            _update_ktype(obj.dsms, obj)
            had_ktypes = True

        elif isinstance(obj, AppConfig):
            _create_or_update_app_spec(obj, overwrite=True)
        else:
            raise TypeError(
                f"Object `{obj}` of type {type(obj)} cannot be committed."
            )
        if Session.dsms.config.auto_refresh:
            obj.refresh()
    for obj in buffers.deleted.values():
        if isinstance(obj, KItem):
            _delete_dataframe(obj)
            _delete_kitem(obj)
        elif isinstance(obj, AppConfig):
            _delete_app_spec(obj)
        elif isinstance(obj, KType) or (
            isinstance(obj, Enum) and isinstance(obj.value, KType)
        ):
            _delete_ktype(obj)
            had_ktypes = True
        else:
            raise TypeError(
                f"Object `{obj}` of type {type(obj)} cannot be committed or deleted."
            )
    if Session.dsms.config.auto_refresh and had_ktypes:
        Session.dsms.refresh_ktypes()
    logger.debug("Committing successful, clearing buffers.")


def _refresh_kitem(kitem: "KItem") -> None:
    """Refresh the KItem"""
    # note: in order propperly refresh the same item, we need to fetch the data
    # from the backend and then revalidate it. However, this leads to the fact
    # that a new Python-variable would be created for the same KItem instance and the
    # old variable becomes obsolete. This is somewhat unintuitive for the user.
    # Hence, we just set the attributes of the validated new instance to the old instance
    # which is already in our memory. This is somewhat hacky since you will need to
    # validate twice. However, if the iterate over the `refreshed` instance directly,
    # the pydantic `AliasChoises` are not taken into consideration. Which means that
    # e.g. our field `apps` cannot be refreshed and we will receive an error, that
    # `kitem_apps` (how the field in the backend is called) is not part of the instance,
    # because the pydantic aliases are only regarded during the model instanciation, not
    # during attribute-assignment.
    refreshed = _get_kitem(kitem.dsms, kitem.id, as_json=True)
    validated = kitem.model_validate(refreshed)
    for key, value in validated:
        logger.debug(
            "Set updated property `%s` for KType with id `%s` after commiting: %s",
            key,
            kitem.id,
            value,
        )
        setattr(kitem, key, value)
    dataframe = _inspect_dataframe(kitem.dsms, kitem.id)
    if dataframe:
        kitem.dataframe = [{"id": kitem.id, **column} for column in dataframe]


def _refresh_ktype(ktype: "KType") -> None:
    """Refresh the KItem"""
    for key, value in _get_ktype(ktype.dsms, ktype.id, as_json=True).items():
        logger.debug(
            "Set updated property `%s` for KType with id `%s` after commiting: %s",
            key,
            ktype.id,
            value,
        )
        setattr(ktype, key, value)


def _split_iri(iri: str) -> List[str]:
    if "#" in iri:
        namspace, name = iri.rsplit("#", 1)
    else:
        namspace, name = iri.rsplit("/", 1)
    return namspace, name


def _make_annotation_schema(iri: str) -> Dict[str, Any]:
    namespace, label = _split_iri(iri)
    return {"namespace": namespace, "label": label, "iri": iri}


def _search(
    dsms: "DSMS",
    query: Optional[str] = None,
    ktypes: "Optional[List[Union[Enum, KType]]]" = [],
    annotations: "Optional[List[str]]" = [],
    limit: "Optional[int]" = 10,
    offset: "Optional[int]" = 0,
    allow_fuzzy: "Optional[bool]" = True,
    compact: "Optional[bool]" = False,
) -> "List[SearchResult]":
    """Search for KItems in the remote backend"""
    from dsms import KItem, KItemCompactedModel

    payload = {
        "search_term": query or "",
        "ktypes": [ktype.value.id for ktype in ktypes],
        "annotations": [_make_annotation_schema(iri) for iri in annotations],
        "limit": limit,
        "offset": offset,
        "compact": compact,
    }
    response = _perform_request(
        dsms,
        "api/knowledge/kitems/search",
        "post",
        json=payload,
        params={"allow_fuzzy": allow_fuzzy},
    )
    if not response.ok:
        raise RuntimeError(
            f"Search could not be executed successfully: {response.text}`"
        )
    try:
        dumped = response.json()
    except Exception as excep:
        raise RuntimeError(
            f"""Something went wrong while searching for KItems: {response.text}"""
        ) from excep
    return SearchResult(
        hits=[
            {
                "kitem": KItemCompactedModel(**item.get("kitem"))
                if compact
                else KItem(**item.get("kitem")),
                "fuzzy": item.get("fuzzy"),
            }
            for item in dumped.get("hits")
        ],
        total_count=dumped.get("total_count"),
    )


def _slugify(input_string: str, replacement: str = ""):
    """Turn any arbitrary string into a slug."""
    slug = re.sub(
        r"[^\w\s\-_]", replacement, input_string
    )  # Remove all non-word characters (everything except numbers and letters)
    slug = re.sub(r"\s+", "", slug)  # Replace all runs of whitespace
    slug = slug.lower()  # Convert the string to lowercase.
    return slug


def _slug_is_available(dsms: "DSMS", ktype_id: str, value: str) -> bool:
    """Check whether the id of a KItem is available in the DSMS or not"""
    response = _perform_request(
        dsms, f"api/knowledge/kitems/{ktype_id}/{value}", "head"
    )
    return response.status_code == 404


def _get_dataframe_column(
    dsms: "DSMS", kitem_id: str, column_id: int
) -> List[Any]:
    """Download the column of a dataframe container of a certain kitem"""

    response = _perform_request(
        dsms, f"api/knowledge/data/{kitem_id}/column-{column_id}", "get"
    )
    if not response.ok:
        message = f"""Something went wrong fetch column id `{column_id}`
        for kitem `{kitem_id}`: {response.text}"""
        raise ValueError(message)
    return response.json().get("array")


def _inspect_dataframe(
    dsms: "DSMS", kitem_id: str
) -> Optional[List[Dict[str, Any]]]:
    """Get column info for the dataframe container of a certain kitem"""
    response = _perform_request(dsms, f"api/knowledge/data/{kitem_id}", "get")
    if not response.ok and response.status_code == 404:
        dataframe = None
    elif not response.ok and response.status_code != 404:
        message = f"""Something went wrong fetching intospection
        for kitem `{kitem_id}`: {response.text}"""
        raise ValueError(message)
    else:
        dataframe = response.json()
    return dataframe


def _update_dataframe(dsms: "DSMS", kitem_id: str, data: pd.DataFrame):
    if data.empty:
        _delete_dataframe(kitem_id)
    else:
        buffer = io.BytesIO()
        data.to_json(buffer, indent=2)
        buffer.seek(0)
        response = _perform_request(
            dsms,
            f"api/knowledge/data/{kitem_id}",
            "put",
            files={"data": buffer},
        )
        if not response.ok:
            raise RuntimeError(
                f"Could not put dataframe into kitem with id `{kitem_id}`: {response.text}"
            )


def _delete_dataframe(kitem: "KItem") -> Response:
    logger.debug("Delete DataFrame for kitem with id `%s`.", kitem.id)
    return _perform_request(
        kitem.dsms, f"api/knowledge/data/{kitem.id}", "delete"
    )


def _commit_avatar(kitem) -> None:
    if kitem.avatar_exists:
        response = _perform_request(
            kitem.dsms, f"api/knowledge/avatar/{kitem.id}", "delete"
        )
        if not response.ok:
            message = (
                f"Something went wrong deleting the avatar: {response.text}"
            )
            raise RuntimeError(message)
    avatar = kitem.avatar.generate()
    buffer = io.BytesIO()
    avatar.save(buffer, "JPEG", quality=100)
    buffer.seek(0)
    encoded_image = base64.b64encode(buffer.getvalue())
    encoded_image_str = "data:image/jpeg;base64," + encoded_image.decode(
        "utf-8"
    )
    response = _perform_request(
        kitem.dsms,
        f"api/knowledge/avatar/{kitem.id}",
        "put",
        json={
            "croppedImage": encoded_image_str,
            "originalImage": encoded_image_str,
            "filename": kitem.name + ".jpeg",
        },
    )
    if not response.ok:
        raise RuntimeError(
            f"Something went wrong while updating the avatar: {response.text}"
        )


def _make_avatar(
    image: Optional[Union[str, Image.Image]] = None,
    encode_qr: Optional[str] = None,
) -> Image.Image:
    avatar = None
    if encode_qr:
        # this should be moved to the backend sooner or later
        qrcode = segno.make(encode_qr)
        if image:
            out = io.BytesIO()
            if isinstance(image, Image.Image):
                raise TypeError(
                    """When a QR Code is generated with an image as background,
                       its filepath must be a string"""
                )
            qrcode.to_artistic(
                background=image, target=out, scale=5, kind="jpeg", border=0
            )
            avatar = Image.open(out)
        else:
            avatar = qrcode.to_pil(scale=5, border=0)
    if image and not encode_qr:
        if isinstance(image, str):
            avatar = Image.open(image)
        else:
            avatar = image
    if not image and not encode_qr:
        raise RuntimeError(
            "Cannot generate avator. Neither `encode_qr` or `file` are specified."
        )
    return avatar


def _get_avatar(dsms: "DSMS", kitem_id: UUID) -> Image.Image:
    response = _perform_request(
        dsms, f"api/knowledge/avatar/{kitem_id}", "get"
    )
    buffer = io.BytesIO(response.content)
    return Image.open(buffer)


def _create_or_update_app_spec(app: "AppConfig", overwrite=False) -> None:
    """Create app specfication"""
    upload_file = {"def_file": io.StringIO(yaml.safe_dump(app.specification))}
    response = _perform_request(
        app.dsms,
        f"/api/knowledge/apps/argo/spec/{app.name}",
        "post",
        files=upload_file,
        params={"overwrite": overwrite},
    )
    if not response.ok:
        message = f"Something went wrong uploading app spec with name `{app.name}`: {response.text}"
        raise RuntimeError(message)
    return response.text


def _delete_app_spec(obj: "AppConfig") -> None:
    """Delete app specfication"""
    response = _perform_request(
        obj.dsms,
        f"/api/knowledge/apps/argo/spec/{obj.name}",
        "delete",
    )
    if not response.ok:
        message = f"Something went wrong deleting app spec with name `{obj.name}`: {response.text}"
        raise RuntimeError(message)
    return response.text


def _transform_custom_properties_schema(custom_properties: Any, webform: Any):
    if webform:
        copy_properties = custom_properties.copy()
        transformed_sections = {}
        for section_def in webform.sections:
            for input_def in section_def.inputs:
                if input_def.label in copy_properties:
                    if input_def.measurement_unit:
                        measurement_unit = (
                            input_def.measurement_unit.model_dump()
                        )
                    else:
                        measurement_unit = None
                    entry = {
                        "id": input_def.id,
                        "label": input_def.label,
                        "value": copy_properties.pop(input_def.label),
                        "measurement_unit": measurement_unit,
                        "type": input_def.widget,
                    }
                    section_name = section_def.name
                    if section_name not in transformed_sections:
                        section = {
                            "id": section_def.id,
                            "name": section_name,
                            "entries": [],
                        }
                        transformed_sections[section_name] = section
                    transformed_sections[section_name]["entries"].append(entry)
        if copy_properties:
            logger.info(
                "Some custom properties were not found in the webform: %s",
                copy_properties,
            )
            transformed_sections["General"] = _make_misc_section(
                copy_properties
            )
        response = {"sections": list(transformed_sections.values())}
    else:
        response = _transform_from_flat_schema(custom_properties)
    return response


def _transform_from_flat_schema(
    custom_properties: Dict[str, Any]
) -> Dict[str, Any]:
    return {"sections": [_make_misc_section(custom_properties)]}


def _make_misc_section(custom_properties: dict):
    """
    If the ktype_id is not found, return the custom_properties dictionary
    as is, wrapped in a section named "Misc".
    """
    section = {"id": generate_id(), "name": "Misc", "entries": []}
    for key, value in custom_properties.items():
        section["entries"].append(
            {
                "id": generate_id(),
                "label": key,
                "value": value,
            }
        )
    return section


def _map_data_type_to_widget(value):
    from dsms import KItem
    from dsms.knowledge.webform import KnowledgeItemReference, Widget

    widget = None
    is_list = isinstance(value, list)
    if isinstance(value, list):
        is_list = True
        types = []
        for val in value:
            dtype = type(val)
            if isinstance(val, str):
                types.append(Widget.MULTI_SELECT.value)
            if isinstance(val, (KItem, KnowledgeItemReference, dict)):
                types.append(Widget.KNOWLEDGE_ITEM.value)
            if isinstance(val, (int, float)):
                types.append(Widget.SLIDER.value)
        types = set(types)
        if len(types) > 1:
            raise ValueError(
                f"More than one widget type detected from data ({value}): {types} "
            )
        if len(types) == 0:
            warnings.warn(
                f"No widget type detected from data ({value}). Will set a default type: TEXT."
            )
            widget = Widget.TEXT.value
            dtype = str
        else:
            widget = types.pop()
    else:
        dtype = type(value)
        if isinstance(value, str):
            widget = Widget.TEXT.value
            dtype = type(value)
        elif isinstance(value, (int, float)):
            widget = Widget.NUMBER.value
        elif isinstance(value, bool):
            widget = Widget.CHECKBOX.value

        elif isinstance(value, (KItem, KnowledgeItemReference, dict)):
            raise ValueError(
                "KItems in the custom properties should be wrapped into a list."
            )
        else:
            raise ValueError(
                f"Unsupported data type: {type(value)}. Value: {value}"
            )
    return widget, is_list, dtype


def make_custom_properties_schema(metadata: List[Dict[str, Any]]) -> dict:
    """
    Convert a list of dictionaries representing metadata
    entries into a DSMS schema dict.

    The input should be a list of dictionaries,
    where each dictionary represents a metadata entry.
    The output is a dictionary in the DSMS schema,
    with a single section named "General",
    containing the given metadata entries.

    If the input is empty, the function will
    return an empty dictionary.

    :param metadata: The metadata list to convert.
    :return: A dictionary in the DSMS schema.
    """
    if metadata:
        for metadatum in metadata:
            metadatum["id"] = generate_id()
        metadata = {
            "sections": [
                {
                    "id": generate_id(),
                    "name": "General",
                    "entries": metadata,
                }
            ]
        }
    else:
        metadata = {}

    return metadata


def generate_id(prefix: str = "id") -> str:
    # Generate a unique part using time and random characters
    """
    Generates a unique id using a combination of the current time and 6 random characters.

    Args:
    prefix (str): The prefix to use for the generated id. Defaults to "id".

    Returns:
    str: The generated id.
    """
    unique_part = f"{int(time.time() * 1000)}"  # Milliseconds since epoch
    random_part = "".join(
        random.choices(string.ascii_lowercase + string.digits, k=6)  # nosec
    )
    # Combine prefix, unique part, and random part
    generated_id = f"{prefix}{unique_part}{random_part}"
    return generated_id

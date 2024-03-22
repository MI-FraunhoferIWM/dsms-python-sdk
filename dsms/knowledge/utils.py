"""DSMS knowledge utilities"""
import io
import json
import re
from enum import Enum
from pathlib import Path
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Union
from uuid import UUID

import pandas as pd
from pydantic import BaseModel, create_model
from requests import Response

from dsms.core.utils import _name_to_camel, _perform_request

if TYPE_CHECKING:
    from dsms.core.context import Buffers
    from dsms.knowledge import KItem, KType


def _parse_model(value: Dict[str, Any]) -> BaseModel:
    """Convert the dict with the model schema into a pydantic model."""
    title = value.get("title")
    properties = value.get("properties")
    if not title:
        raise KeyError("`data_schema` does not have any `title`.")
    if isinstance(properties, type(None)):
        raise KeyError("`data_schema` does not have any `properties`.")
    fields = {}
    for key, props in properties.items():
        dtype = props.get("type")
        default = props.get("default")
        if dtype == "string":
            dtype = str
        elif dtype == "integer":
            dtype = int
        elif dtype == "float":
            dtype = float
        elif dtype == "bool":
            dtype = bool
        elif dtype == "object":
            dtype = dict
        else:
            raise TypeError(f"Invalid `type={dtype}`")
        fields[key] = (dtype, ... if not default else default)
    return create_model(title, **fields)


def _get_remote_ktypes() -> Enum:
    """Get the KTypes from the remote backend"""
    from dsms import (  # isort:skip
        Context,
        KType,
    )

    response = _perform_request("api/knowledge-type/", "get")
    if not response.ok:
        raise ConnectionError(
            f"Something went wrong fetching the remote ktypes: {response.text}"
        )
    Context.ktypes = {ktype["id"]: KType(**ktype) for ktype in response.json()}

    return Enum("KTypes", {_name_to_camel(key): key for key in Context.ktypes})


def _get_kitem_list() -> "List[KItem]":
    """Get all available KItems from the remote backend."""
    from dsms.knowledge.kitem import (  # isort:skip
        KItem,
    )

    response = _perform_request("api/knowledge/kitems", "get")
    if not response.ok:
        raise ValueError(
            f"Something went wrong fetching the available kitems: {response.text}"
        )
    return [KItem(**kitem) for kitem in response.json()]


def _kitem_exists(kitem: Union[Any, str, UUID]) -> bool:
    """Check whether the KItem exists in the remote backend"""
    from dsms.knowledge.kitem import (  # isort:skip
        KItem,
    )

    if isinstance(kitem, KItem):
        route = f"api/knowledge/kitems/{kitem.id}"
    else:
        route = f"api/knowledge/kitems/{kitem}"
    response = _perform_request(route, "get")
    return response.ok


def _get_kitem(uuid: Union[str, UUID]) -> "KItem":
    """Get the KItem for a instance with a certain ID from remote backend"""
    from dsms import Context, KItem

    response = _perform_request(f"api/knowledge/kitems/{uuid}", "get")
    if response.status_code == 404:
        raise ValueError(
            f"""KItem with uuid `{uuid}` does not exist in
            DSMS-instance `{Context.dsms.config.host_url}`"""
        )
    if not response.ok:
        raise ValueError(
            f"""An error occured fetching the KItem with uuid `{uuid}`:
            `{response.text}`"""
        )
    return KItem(**response.json())


def _create_new_kitem(kitem: "KItem") -> None:
    """Create a new KItem in the remote backend"""
    payload = {
        "name": kitem.name,
        "id": str(kitem.id),
        "slug": kitem.slug,
        "ktype_id": kitem.ktype.id,
    }
    response = _perform_request("api/knowledge/kitems", "post", json=payload)
    if not response.ok:
        raise ValueError(
            f"KItem with uuid `{kitem.id}` could not be created in DSMS: {response.text}`"
        )


def _update_kitem(kitem: "KItem") -> Response:
    """Update a KItem in the remote backend."""
    old_kitem = _get_kitem(kitem.id)
    differences = _get_kitems_diffs(old_kitem, kitem)
    dumped = kitem.model_dump_json(
        exclude={
            "authors",
            "annotations",
            "linked_kitems",
            "updated_at",
            "avatar_exists",
            "user_groups",
            "ktype_id",
            "attachments",
            "id",
            "kitem_apps",
            "created_at",
            "external_links",
            "hdf5",
        },
        exclude_none=True,
    )
    payload = json.loads(dumped)
    payload.update(**differences)
    payload.update(
        external_links={
            link.label: str(link.url) for link in kitem.external_links
        }
    )
    response = _perform_request(
        f"api/knowledge/kitems/{kitem.id}", "put", json=payload
    )
    if not response.ok:
        raise ValueError(
            f"KItem with uuid `{kitem.id}` could not be updated in DSMS: {response.text}`"
        )
    for key, value in _get_kitem(kitem.id).__dict__.items():
        if key != "attachments":
            setattr(kitem, key, value)
    return response


def _delete_kitem(kitem: "KItem") -> None:
    """Delete a KItem in the remote backend"""
    response = _perform_request(f"api/knowledge/kitems/{kitem.id}", "delete")
    if not response.ok:
        raise ValueError(
            f"KItem with uuid `{kitem.id}` could not be deleted from DSMS: `{response.text}`"
        )


def _update_attachments(kitem: "KItem") -> None:
    """Update attachments of the KItem."""
    old_kitem = _get_kitem(kitem.id)
    differences = _get_attachment_diffs(old_kitem, kitem)
    for upload in differences["add"]:
        _upload_attachments(kitem, upload.name)
    for remove in differences["remove"]:
        _delete_attachments(kitem, remove.name)
    for key, value in _get_kitem(kitem.id).__dict__.items():
        setattr(kitem, key, value)


def _upload_attachments(kitem: "KItem", attachment: "str") -> None:
    """Upload the attachments of the KItem"""
    path = Path(attachment)

    if path.is_file():
        if not path.exists():
            raise FileNotFoundError(f"File {path} does not exist.")

        with open(path, mode="rb") as file:
            upload_file = {"dataFile": file}
            response = _perform_request(
                f"api/knowledge/attachments/{kitem.id}",
                "put",
                files=upload_file,
            )
        if not response.ok:
            raise RuntimeError(
                f"Could not upload attachment `{path}`: {response.text}"
            )


def _delete_attachments(kitem: "KItem", file_name: str) -> None:
    """Delete attachment from KItem"""
    url = f"api/knowledge/attachments/{kitem.id}/{file_name}"
    response = _perform_request(url, "delete")
    if not response.ok:
        raise RuntimeError(
            f"Could not delete attachment `{file_name}`: {response.text}"
        )


def _get_attachment(kitem_id: "KItem", file_name: str) -> str:
    """Download attachment from KItem"""
    url = f"api/knowledge/attachments/{kitem_id}/{file_name}"
    response = _perform_request(url, "get")
    if not response.ok:
        raise RuntimeError(
            f"Download for attachment `{file_name}` was not successful: {response.text}"
        )
    return response.text


def _get_attachment_diffs(kitem_old: "KItem", kitem_new: "KItem"):
    """Check which attachments should be removed and which should be added."""
    return {
        "remove": set(kitem_old.attachments) - set(kitem_new.attachments),
        "add": set(kitem_new.attachments) - set(kitem_old.attachments),
    }


def _get_kitems_diffs(kitem_old: "KItem", kitem_new: "KItem"):
    """Get the differences in the attributes between two kitems"""
    differences = {}
    attributes = [
        ("linked_kitems", ("kitems", "link", "unlink")),
        ("annotations", ("annotations", "link", "unlink")),
        ("kitem_apps", ("kitem_apps", "update", "remove")),
        ("user_groups", ("user_groups", "add", "remove")),
    ]
    for name, terms in attributes:
        to_add_name = terms[0] + "_to_" + terms[1]
        to_remove_name = terms[0] + "_to_" + terms[2]
        old_attr = getattr(kitem_old, name)
        new_attr = getattr(kitem_new, name)
        differences[to_add_name] = [
            json.loads(attr.model_dump_json())
            for attr in set(new_attr) - set(old_attr)
        ]
        differences[to_remove_name] = [
            json.loads(attr.model_dump_json())
            for attr in set(old_attr) - set(new_attr)
        ]
    return differences


def _commit(buffers: "Buffers") -> None:
    """Commit the buffers for the
    created, updated and deleted buffers"""
    _commit_created(buffers.created)
    _commit_updated(buffers.updated)
    _commit_deleted(buffers.deleted)


def _commit_created(buffer: "Dict[str, KItem]") -> dict:
    """Commit the buffer for the `created` buffers"""
    for kitem in buffer.values():
        exists = _kitem_exists(kitem)
        if not exists:
            _create_new_kitem(kitem)


def _commit_updated(buffer: "Dict[str, KItem]") -> None:
    """Commit the buffer for the `updated` buffers"""
    for kitem in buffer.values():
        if _kitem_exists(kitem):
            if isinstance(kitem.hdf5, pd.DataFrame):
                _update_hdf5(kitem.id, kitem.hdf5)
            elif isinstance(kitem.hdf5, type(None)) and _inspect_hdf5(
                kitem.id
            ):
                _delete_hdf5(kitem.id)
            _update_kitem(kitem)
            _update_attachments(kitem)


def _commit_deleted(buffer: "Dict[str, KItem]") -> None:
    """Commit the buffer for the `deleted` buffers"""
    for kitem in buffer.values():
        if _kitem_exists(kitem):
            _delete_hdf5(kitem.id)
            _delete_kitem(kitem)


def _search(
    query: Optional[str] = None,
    ktypes: "Optional[List[KType]]" = [],
    annotations: "Optional[List[str]]" = [],
    limit: "Optional[int]" = 10,
    allow_fuzzy: "Optional[bool]" = True,
) -> "List[KItem]":
    """Search for KItems in the remote backend"""
    from dsms import KItem  # isort:skip

    payload = {
        "search_term": query or "",
        "ktypes": [ktype.value for ktype in ktypes],
        "kitem_annotations": annotations,
        "limit": limit,
    }
    response = _perform_request(
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
    return [KItem(**item) for item in dumped]


def _slugify(input_string):
    """Turn any arbitrary string into a slug."""
    slug = re.sub(
        r"[^\w\s]", "", input_string
    )  # Remove all non-word characters (everything except numbers and letters)
    slug = re.sub(r"\s+", "", slug)  # Replace all runs of whitespace
    slug = slug.lower()  # Convert the string to lowercase.
    return slug


def _slug_is_available(ktype_id: Union[str, UUID], value: str) -> bool:
    """Check whether the id of a KItem is available in the DSMS or not"""
    response = _perform_request(
        f"api/knowledge/kitems/{ktype_id}/{value}", "head"
    )
    return response.status_code == 404


def _get_hdf5_column(kitem_id: str, column_id: int) -> List[Any]:
    """Download the column of a hdf5 container of a certain kitem"""
    response = _perform_request(
        f"api/knowledge/data_api/{kitem_id}/column-{column_id}", "get"
    )
    if not response.ok:
        message = f"""Something went wrong fetch column id `{column_id}`
        for kitem `{kitem_id}`: {response.text}"""
        raise ValueError(message)
    return response.json().get("array")


def _inspect_hdf5(kitem_id: str) -> Optional[List[Dict[str, Any]]]:
    """Get column info for the hdf5 container of a certain kitem"""
    response = _perform_request(f"api/knowledge/data_api/{kitem_id}", "get")
    if not response.ok and response.status_code == 404:
        hdf5 = None
    elif not response.ok and response.status_code != 404:
        message = f"""Something went wrong fetching intospection
        for kitem `{kitem_id}`: {response.text}"""
        raise ValueError(message)
    else:
        hdf5 = response.json()
    return hdf5


def _update_hdf5(kitem_id: str, data: pd.DataFrame):
    buffer = io.BytesIO()
    data.to_json(buffer, indent=2)
    buffer.seek(0)
    response = _perform_request(
        f"api/knowledge/data_api/{kitem_id}", "put", files={"data": buffer}
    )
    if not response.ok:
        raise RuntimeError(
            f"Could not put dataframe into kitem with id `{kitem_id}`: {response.text}"
        )


def _delete_hdf5(kitem_id: str) -> Response:
    return _perform_request(f"api/knowledge/data_api/{kitem_id}", "delete")

"""DSMS knowledge utilities"""
import io
import json
import re
import warnings
from enum import Enum
from pathlib import Path
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Union
from uuid import UUID

import pandas as pd
from requests import Response

from pydantic import (  # isort: skip
    BaseModel,
    ConfigDict,
    Field,
    create_model,
    model_validator,
)

from dsms.core.utils import _name_to_camel, _perform_request  # isort:skip

from dsms.knowledge.properties.custom_datatype import (  # isort:skip
    NumericalDataType,
)

from dsms.knowledge.search import SearchResult  # isort:skip

if TYPE_CHECKING:
    from dsms.core.context import Buffers
    from dsms.knowledge import KItem, KType


def _is_number(value):
    try:
        float(value)
        return True
    except Exception:
        return False


def _create_custom_properties_model(
    value: Optional[Dict[str, Any]]
) -> BaseModel:
    """Convert the dict with the model schema into a pydantic model."""
    from dsms import KItem

    fields = {}
    if isinstance(value, dict):
        for item in value.get("sections"):
            for form_input in item.get("inputs"):
                label = form_input.get("label")
                dtype = form_input.get("widget")
                default = form_input.get("defaultValue")
                slug = _slugify(label)
                if dtype in ("Text", "File", "Textarea", "Vocabulary term"):
                    dtype = Optional[str]
                elif dtype in ("Number", "Slider"):
                    dtype = Optional[NumericalDataType]
                elif dtype == "Checkbox":
                    dtype = Optional[bool]
                elif dtype in ("Select", "Radio"):
                    choices = Enum(
                        _name_to_camel(label) + "Choices",
                        {
                            _name_to_camel(choice["value"]): choice["value"]
                            for choice in form_input.get("choices")
                        },
                    )
                    dtype = Optional[choices]
                elif dtype == "Knowledge item":
                    warnings.warn(
                        "knowledge item not fully supported for KTypes yet."
                    )
                    dtype = Optional[str]

                fields[slug] = (dtype, default or None)
    fields["kitem"] = (
        Optional[KItem],
        Field(None, exclude=True),
    )

    config = ConfigDict(
        extra="allow", arbitrary_types_allowed=True, exclude={"kitem"}
    )
    validators = {
        "validate_model": model_validator(mode="before")(_validate_model)
    }
    model = create_model(
        "CustomPropertiesModel",
        __config__=config,
        __validators__=validators,
        **fields,
    )
    setattr(model, "__str__", _print_properties)
    setattr(model, "__repr__", _print_properties)
    setattr(model, "__setattr__", __setattr_property__)
    return model


def _print_properties(self: Any) -> str:
    fields = ", \n".join(
        [
            f"\t\t{key}: {value}"
            for key, value in self.model_dump().items()
            if key not in self.model_config["exclude"]
        ]
    )
    return f"{{\n{fields}\n\t}}"


def __setattr_property__(self, key, value) -> None:
    if _is_number(value):
        # convert to convertable numeric object
        value = _create_numerical_dtype(key, value, self.kitem)
        # mark as updated
    if key != "kitem" and self.kitem:
        self.kitem.context.buffers.updated.update({self.kitem.id: self.kitem})
    elif key == "kitem":
        # set kitem for convertable numeric datatype
        for prop in self.model_dump().values():
            if isinstance(prop, NumericalDataType) and not prop.kitem:
                prop.kitem = value
    # reassignment of extra fields does not work, seems to be a bug?
    # have this workaround:
    if key in self.__pydantic_extra__:
        self.__pydantic_extra__[key] = value
    super(BaseModel, self).__setattr__(key, value)


def _create_numerical_dtype(
    key: str, value: Union[int, float], kitem: "KItem"
) -> NumericalDataType:
    value = NumericalDataType(value)
    value.name = key
    value.kitem = kitem
    return value


def _validate_model(
    cls, values: Dict[str, Any]  # pylint: disable=unused-argument
) -> Dict[str, Any]:
    for key, value in values.items():
        if _is_number(value):
            values[key] = _create_numerical_dtype(
                key, value, values.get("kitem")
            )
    return values


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


def _get_kitem(
    uuid: Union[str, UUID], as_json=False
) -> "Union[KItem, Dict[str, Any]]":
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
    payload = response.json()
    if as_json:
        response = payload
    else:
        response = KItem(**payload)
    return response


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


def _update_kitem(new_kitem: "KItem", old_kitem: "Dict[str, Any]") -> Response:
    """Update a KItem in the remote backend."""
    to_compare = new_kitem.model_dump(
        include={"annotations", "linked_kitems", "user_groups", "kitem_apps"}
    )
    differences = _get_kitems_diffs(old_kitem, to_compare)
    dumped = new_kitem.model_dump_json(
        exclude={
            "authors",
            "annotations",
            "custom_properties",
            "linked_kitems",
            "updated_at",
            "rdf_exists",
            "in_backend",
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
    payload.update(
        external_links={
            link.label: str(link.url) for link in new_kitem.external_links
        },
        **differences,
    )
    if new_kitem.custom_properties:
        custom_properties = new_kitem.custom_properties.model_dump()
        payload.update(custom_properties={"content": custom_properties})
    response = _perform_request(
        f"api/knowledge/kitems/{new_kitem.id}", "put", json=payload
    )
    if not response.ok:
        raise ValueError(
            f"KItem with uuid `{new_kitem.id}` could not be updated in DSMS: {response.text}`"
        )
    return response


def _delete_kitem(kitem: "KItem") -> None:
    """Delete a KItem in the remote backend"""
    response = _perform_request(f"api/knowledge/kitems/{kitem.id}", "delete")
    if not response.ok:
        raise ValueError(
            f"KItem with uuid `{kitem.id}` could not be deleted from DSMS: `{response.text}`"
        )


def _update_attachments(
    new_kitem: "KItem", old_kitem: "Dict[str, Any]"
) -> None:
    """Update attachments of the KItem."""
    differences = _get_attachment_diffs(old_kitem, new_kitem)
    for upload in differences["add"]:
        _upload_attachments(new_kitem, upload)
    for remove in differences["remove"]:
        _delete_attachments(new_kitem, remove)


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


def _get_attachment_diffs(kitem_old: "Dict[str, Any]", kitem_new: "KItem"):
    """Check which attachments should be removed and which should be added."""
    return {
        "remove": [
            attachment
            for attachment in kitem_old.get("attachments")
            if attachment not in kitem_new.attachments.by_name
        ],
        "add": [
            attachment.name
            for name, attachment in kitem_new.attachments.by_name.items()
            if name not in kitem_old.get("attachments")
        ],
    }


def _get_kitems_diffs(
    kitem_old: "Dict[str, Any]", kitem_new: "Dict[str, Any]"
):
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
        old_attr = kitem_old.get(name)
        new_attr = kitem_new.get(name)
        differences[to_add_name] = [
            attr for attr in new_attr if new_attr not in old_attr
        ]
        differences[to_remove_name] = [
            attr for attr in old_attr if old_attr not in new_attr
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
        _create_new_kitem(kitem)


def _commit_updated(buffer: "Dict[str, KItem]") -> None:
    """Commit the buffer for the `updated` buffers"""
    for new_kitem in buffer.values():
        old_kitem = _get_kitem(new_kitem.id, as_json=True)
        if old_kitem:
            if isinstance(new_kitem.hdf5, pd.DataFrame):
                _update_hdf5(new_kitem.id, new_kitem.hdf5)
                new_kitem.hdf5 = _inspect_hdf5(new_kitem.id)
            elif isinstance(new_kitem.hdf5, type(None)) and _inspect_hdf5(
                new_kitem.id
            ):
                _delete_hdf5(new_kitem.id)
            _update_kitem(new_kitem, old_kitem)
            _update_attachments(new_kitem, old_kitem)
            new_kitem.in_backend = True
            for key, value in _get_kitem(new_kitem.id, as_json=True).items():
                setattr(new_kitem, key, value)


def _commit_deleted(buffer: "Dict[str, KItem]") -> None:
    """Commit the buffer for the `deleted` buffers"""
    for kitem in buffer.values():
        _delete_hdf5(kitem.id)
        _delete_kitem(kitem)


def _split_iri(iri: str) -> List[str]:
    if "#" in iri:
        namspace, name = iri.rsplit("#", 1)
    else:
        namspace, name = iri.rsplit("/", 1)
    return namspace, name


def _make_annotation_schema(iri: str) -> Dict[str, Any]:
    namespace, name = _split_iri(iri)
    return {"namespace": namespace, "name": name, "iri": iri}


def _search(
    query: Optional[str] = None,
    ktypes: "Optional[List[KType]]" = [],
    annotations: "Optional[List[str]]" = [],
    limit: "Optional[int]" = 10,
    allow_fuzzy: "Optional[bool]" = True,
) -> "List[SearchResult]":
    """Search for KItems in the remote backend"""
    from dsms import KItem

    payload = {
        "search_term": query or "",
        "ktypes": [ktype.value for ktype in ktypes],
        "annotations": [_make_annotation_schema(iri) for iri in annotations],
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
    return [
        SearchResult(hit=KItem(**item.get("hit")), fuzzy=item.get("fuzzy"))
        for item in dumped
    ]


def _slugify(input_string: str, replacement: str = ""):
    """Turn any arbitrary string into a slug."""
    slug = re.sub(
        r"[^\w\s\-_]", replacement, input_string
    )  # Remove all non-word characters (everything except numbers and letters)
    slug = re.sub(r"\s+", "", slug)  # Replace all runs of whitespace
    slug = slug.lower()  # Convert the string to lowercase.
    return slug


def _slug_is_available(ktype_id: Union[str, UUID], value: str) -> bool:
    """Check whether the id of a KItem is available in the DSMS or not"""
    response = _perform_request(
        f"api/knowledge/kitems/{ktype_id}/{value}", "head"
    )
    if response.status_code == 401:
        raise RuntimeError("The access token has expired")
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

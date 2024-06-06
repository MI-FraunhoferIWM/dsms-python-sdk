"""DSMS knowledge utilities"""
import base64
import io
import logging
import re
import warnings
from enum import Enum
from pathlib import Path
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Union
from uuid import UUID

import pandas as pd
import segno
from PIL import Image
from requests import Response

from pydantic import (  # isort: skip
    BaseModel,
    ConfigDict,
    Field,
    create_model,
    model_validator,
)

from dsms.core.logging import handler  # isort:skip

from dsms.core.utils import _name_to_camel, _perform_request  # isort:skip

from dsms.knowledge.properties.custom_datatype import (  # isort:skip
    NumericalDataType,
)

from dsms.knowledge.search import SearchResult  # isort:skip

if TYPE_CHECKING:
    from dsms.core.context import Buffers
    from dsms.knowledge import KItem, KType

logger = logging.getLogger(__name__)
logger.addHandler(handler)
logger.propagate = False


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
    logger.debug("Create custom properties model with fields: %s", fields)
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
    logger.debug(
        "Setting property for custom property with key `%s` with value `%s`.",
        key,
        value,
    )
    if _is_number(value):
        # convert to convertable numeric object
        value = _create_numerical_dtype(key, value, self.kitem)
        # mark as updated
    if key != "kitem" and self.kitem:
        logger.debug(
            "Setting related kitem for custom properties with id `%s` as updated",
            self.kitem.id,
        )
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

    ktypes = Enum(
        "KTypes", {_name_to_camel(key): key for key in Context.ktypes}
    )
    logger.debug("Got the following ktypes from backend: `%s`.", list(ktypes))
    return ktypes


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
    logger.debug("Create new KItem with payload: %s", payload)
    response = _perform_request("api/knowledge/kitems", "post", json=payload)
    if not response.ok:
        raise ValueError(
            f"KItem with uuid `{kitem.id}` could not be created in DSMS: {response.text}`"
        )


def _update_kitem(new_kitem: "KItem", old_kitem: "Dict[str, Any]") -> Response:
    """Update a KItem in the remote backend."""
    differences = _get_kitems_diffs(old_kitem, new_kitem)
    payload = new_kitem.model_dump(
        exclude={
            "authors",
            "avatar",
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
    payload.update(
        external_links={
            link.label: str(link.url) for link in new_kitem.external_links
        },
        **differences,
    )
    if new_kitem.custom_properties:
        custom_properties = new_kitem.custom_properties.model_dump()
        # # a smarted detection whether the custom properties were updated is needed
        # old_properties = old_kitem.get("custom_properties")
        # if isinstance(old_properties, dict):
        #     old_custom_properties = old_properties.get("content")
        # else:
        #     old_custom_properties = None
        # if custom_properties != old_custom_properties:
        #     payload.update(custom_properties={"content": custom_properties})
        payload.update(custom_properties={"content": custom_properties})
    logger.debug(
        "Update KItem for `%s` with payload: %s", new_kitem.id, payload
    )
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
    logger.debug("Delete KItem with id: %s", kitem.id)
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
    logger.debug(
        "Found differences in attachments for kitem with id `%s`: %s",
        new_kitem.id,
        differences,
    )
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


def _get_attachment(
    kitem_id: "KItem", file_name: str, as_bytes: bool
) -> Union[str, bytes]:
    """Download attachment from KItem"""
    url = f"api/knowledge/attachments/{kitem_id}/{file_name}"
    response = _perform_request(url, "get")
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
    new_apps = [new.model_dump() for new in new_kitem.kitem_apps]
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
    kitem_apps = _get_apps_diff(kitem_old, kitem_new)
    # merge with previously found differences
    differences.update(**linked_kitems, **kitem_apps)
    return differences


def _commit(buffers: "Buffers") -> None:
    """Commit the buffers for the
    created, updated and deleted buffers"""
    logger.debug("Committing KItems in buffers. Current buffers:")
    logger.debug("Current Created-buffer: %s", buffers.created)
    logger.debug("Current Updated-buffer: %s", buffers.updated)
    logger.debug("Current Deleted-buffer: %s", buffers.deleted)
    _commit_created(buffers.created)
    _commit_updated(buffers.updated)
    _commit_deleted(buffers.deleted)
    logger.debug("Committing successful, clearing buffers.")


def _commit_created(buffer: "Dict[str, KItem]") -> dict:
    """Commit the buffer for the `created` buffers"""
    for kitem in buffer.values():
        _create_new_kitem(kitem)


def _commit_updated(buffer: "Dict[str, KItem]") -> None:
    """Commit the buffer for the `updated` buffers"""
    for new_kitem in buffer.values():
        old_kitem = _get_kitem(new_kitem.id, as_json=True)
        logger.debug(
            "Fetched data from old KItem with id `%s`: %s",
            new_kitem.id,
            old_kitem,
        )
        if old_kitem:
            if isinstance(new_kitem.hdf5, pd.DataFrame):
                logger.debug(
                    "New KItem data has `pd.DataFrame`. Will push as hdf5."
                )
                _update_hdf5(new_kitem.id, new_kitem.hdf5)
                new_kitem.hdf5 = _inspect_hdf5(new_kitem.id)
            elif isinstance(new_kitem.hdf5, type(None)) and _inspect_hdf5(
                new_kitem.id
            ):
                _delete_hdf5(new_kitem.id)
            _update_kitem(new_kitem, old_kitem)
            _update_attachments(new_kitem, old_kitem)
            if new_kitem.avatar.file or new_kitem.avatar.include_qr:
                _commit_avatar(new_kitem)
            new_kitem.in_backend = True
            logger.debug(
                "Fetching updated KItem from remote backend: %s", new_kitem.id
            )
            for key, value in _get_kitem(new_kitem.id, as_json=True).items():
                logger.debug(
                    "Set updated property `%s` for KItem with id `%s` after commiting: %s",
                    key,
                    new_kitem.id,
                    value,
                )
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
    logger.debug("Delete HDF5 for kitem with id `%s`.", kitem_id)
    return _perform_request(f"api/knowledge/data_api/{kitem_id}", "delete")


def _commit_avatar(kitem) -> None:
    if kitem.avatar_exists:
        response = _perform_request(
            f"api/knowledge/avatar/{kitem.id}", "delete"
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
    kitem: "KItem", image: Optional[Union[str, Image.Image]], make_qr: bool
) -> Image.Image:
    avatar = None
    if make_qr:
        # this should be moved to the backend sooner or later
        qrcode = segno.make(kitem.url)
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
    if image and not make_qr:
        if isinstance(image, str):
            avatar = Image.open(image)
        else:
            avatar = image
    if not image and not make_qr:
        raise RuntimeError(
            "Cannot generate avator. Neither `include_qr` or `file` are specified."
        )
    return avatar


def _get_avatar(kitem: "KItem") -> Image.Image:
    response = _perform_request(f"api/knowledge/avatar/{kitem.id}", "get")
    buffer = io.BytesIO(response.content)
    return Image.open(buffer)

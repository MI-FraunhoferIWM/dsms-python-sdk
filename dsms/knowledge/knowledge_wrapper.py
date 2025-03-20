"""Wrapper for data conversion to and from different data formats"""

import base64
import io
import re
from typing import Any

import h5py
import numpy as np
from pydantic import BaseModel


def data_to_dict(data) -> Any:
    """Convert data to python dictionary"""

    data_dict = {}

    def handle_value(key, value):
        """Handles the values under different scenarios"""

        result = None  # Default value for result

        # Handle special cases based on 'key' and 'value'
        if not isinstance(
            value, (int, float, str, bytes, bool, type(None))
        ) and hasattr(value, "__dict__"):
            result = data_to_dict(value)

        elif key == "id":
            result = str(value)

        elif key == "summary":
            summary = getattr(data, "summary", None)
            result = summary.text if summary else None

        elif key == "dataframe":
            dataframe = getattr(data, "dataframe", None)
            if dataframe:
                result = dataframe.to_df().to_json()

        elif key == "file":
            avatar = getattr(data, "avatar", None)
            if avatar:
                image = avatar.download()
                image_bytes = io.BytesIO()
                image.save(image_bytes, format="PNG")
                image_bytes.seek(0)
                result = base64.b64encode(image_bytes.getvalue()).decode(
                    "utf-8"
                )

        elif key == "subgraph" and value is not None:
            result = value.serialize()

        elif key == "content":
            content = data.download().encode("utf-8")
            bytes_io = io.BytesIO(content) if content else None
            result = base64.b64encode(bytes_io.getvalue()).decode("utf-8")

        # Process the value for other cases (lists, dicts, models, etc.)
        if result is None:
            if isinstance(value, (int, float, str, bytes, bool, type(None))):
                result = str(value)
            elif isinstance(value, list):
                result = [handle_value(key, v) for v in value]
            elif isinstance(value, dict):
                result = {k: handle_value(k, v) for k, v in value.items()}
            elif isinstance(value, BaseModel):
                result = {
                    k: handle_value(k, v)
                    for k, v in value.model_dump().items()
                }
            elif isinstance(value, io.BytesIO):
                result = base64.b64encode(value.getvalue()).decode("utf-8")

        return result

    for k, v in data.model_dump().items():
        if k == "attachments":
            for attachment in getattr(data, "attachments"):
                data_dict.setdefault("attachments", []).append(
                    handle_value(k, attachment)
                )
            continue
        if k == "linked_kitems":
            for linked_kitem in getattr(data, "linked_kitems"):
                item = {}
                for key in ["id", "name", "slug", "ktype_id"]:
                    value = getattr(linked_kitem, key)
                    item[key] = str(value)
                data_dict.setdefault("linked_kitems", []).append(item)
            continue
        data_dict[k] = handle_value(k, v)

    return data_dict


def dict_to_hdf5(dict_data):
    """Converts data from a dictionary to HDF5"""
    byte_data = io.BytesIO()

    # Create an HDF5 file in memory
    with h5py.File(byte_data, "w") as f:
        # Recursively add dictionary contents
        def add_to_hdf5(data, group):
            for key, value in data.items():
                if isinstance(value, dict):
                    # Handle nested dictionaries recursively
                    subgroup = group.create_group(key)
                    add_to_hdf5(value, subgroup)
                elif isinstance(value, list):
                    # Handle lists, check if the list contains dictionaries
                    subgroup = group.create_group(key)
                    for idx, item in enumerate(value):
                        if isinstance(item, dict):
                            item_group = subgroup.create_group(f"item_{idx}")
                            add_to_hdf5(item, item_group)
                        else:
                            subgroup.create_dataset(f"item_{idx}", data=item)
                elif value is not None:
                    group.create_dataset(key, data=value)
                else:
                    group.create_dataset(key, data="")

        # Start adding data to the root group
        add_to_hdf5(dict_data, f)

    # Get the bytes data from the memory buffer
    byte_data.seek(0)
    return byte_data.read()


def hdf5_to_dict(hdf5_file: io.BytesIO) -> dict:
    """Convert an HDF5 file back into a Python dictionary."""

    def decode_if_bytes(value):
        """Decode bytes to string if needed."""

        if isinstance(value, bytes):
            return value.decode("utf-8")
        if isinstance(value, np.ndarray) and value.dtype.type is np.bytes_:
            return [elem.decode("utf-8") for elem in value.tolist()]
        return value

    def convert_numpy(obj):
        """Recursively convert numpy data types in dictionaries or lists to native Python types."""

        if isinstance(obj, np.generic):
            return obj.item()
        if isinstance(obj, dict):
            return {key: convert_numpy(value) for key, value in obj.items()}
        if isinstance(obj, list):
            return [convert_numpy(item) for item in obj]
        if isinstance(obj, tuple):
            return tuple(convert_numpy(item) for item in obj)
        if isinstance(obj, set):
            return {convert_numpy(item) for item in obj}
        return obj

    def read_group(group):
        """Recursively read HDF5 groups into a dictionary."""

        data_dict = {}
        grouped_items = {}

        # Read attributes
        for key, value in group.attrs.items():
            data_dict[key] = decode_if_bytes(value)

        # Read datasets
        for key, dataset in group.items():
            if isinstance(dataset, h5py.Dataset):
                data = dataset[()]

                # Convert binary data back to original format if needed
                if isinstance(data, np.ndarray) and data.dtype == np.uint8:
                    try:
                        value = (
                            data.tobytes().decode()
                        )  # Convert binary to string
                    except UnicodeDecodeError:
                        value = data.tobytes()  # Keep as raw bytes

                elif isinstance(data, np.ndarray):
                    value = decode_if_bytes(
                        data.tolist()
                    )  # Convert numpy arrays to lists

                else:
                    value = decode_if_bytes(data)

            elif isinstance(dataset, h5py.Group):
                value = read_group(dataset)  # Recursively read subgroups

            # If key matches 'item_X', group into a list
            if re.match(r"item_\d+", key):
                parent_key = dataset.parent.name.split("/")[
                    -1
                ]  # Get the parent key
                if parent_key not in grouped_items:
                    grouped_items[parent_key] = []
                grouped_items[parent_key].append(value)
            else:
                data_dict[key] = value

        # Merge grouped items back into the main dictionary
        data_dict.update(grouped_items)

        return convert_numpy(data_dict)

    # Open the HDF5 file and start reading
    with h5py.File(hdf5_file, "r") as hdf:
        return read_group(hdf)

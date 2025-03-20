"""Data Formats"""

from enum import Enum

class DataFormat(Enum):
    """Data formats"""
    
    JSON = "json"
    YAML = "yaml"
    HDF5 = "hdf5"
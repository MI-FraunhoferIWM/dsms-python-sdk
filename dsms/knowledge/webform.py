"""Webform model"""

from enum import Enum
from typing import Any, List, Optional

from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel

from dsms.knowledge.utils import id_generator


class Widget(Enum):
    """Enum for widgets"""

    TEXT = "Text"
    FILE = "File"
    TEXTAREA = "Textarea"
    VOCABULARY_TERM = "Vocabulary term"
    NUMBER = "Number"
    SLIDER = "Slider"
    CHECKBOX = "Checkbox"
    SELECT = "Select"
    RADIO = "Radio"
    KNOWLEDGE_ITEM = "Knowledge item"


class WebformSelectOption(BaseModel):
    """Choices in webform"""

    label: Optional[str] = Field(None)
    value: Optional[Any] = Field(None)
    disabled: Optional[bool] = Field(False)


class WebformMeasurementUnit(BaseModel):
    """Measurement unit"""

    label: Optional[Any] = Field(None)
    iri: Optional[str] = Field(None)
    symbol: Optional[str] = Field(None)
    namespace: Optional[str] = Field(None)


class WebformRangeOptions(BaseModel):
    """Range options"""

    min: Optional[int] = Field(0)
    max: Optional[int] = Field(0)
    step: Optional[int] = Field(0)
    range: Optional[bool] = Field(False)


class Input(BaseModel):
    """Input fields in the sections in webform"""

    model_config = ConfigDict(
        alias_generator=lambda field_name: to_camel(  # pylint: disable=W0108
            field_name
        )
    )

    id: Optional[str] = Field(default_factory=id_generator)
    label: Optional[str] = Field(None)
    widget: Optional[Widget] = Field(None)
    default_value: Optional[Any] = Field(None)
    required: Optional[bool] = Field(False)
    value: Optional[Any] = Field(None)
    hint: Optional[str] = Field(None)
    hidden: Optional[bool] = Field(False)
    ignore: Optional[bool] = Field(False)
    select_options: List[WebformSelectOption] = Field([])
    onKItemAdd: Optional[Any] = Field(None)
    measurement_unit: Optional[WebformMeasurementUnit] = Field(None)
    relation_mapping: Optional[str] = Field(None)
    relation_mapping_name: Optional[str] = Field(None)
    relation_mapping_type: Optional[str] = Field(None)
    class_mapping: Optional[str] = Field(None)
    multiple_selection: Optional[bool] = Field(False)
    mappingKitemId: List[str] = Field([])
    previouslyMappedKitemId: List[str] = Field([])
    knowledge_type: Optional[str] = Field(None)
    knowledge_service_url: Optional[str] = Field(None)
    vocabulary_service_url: Optional[str] = Field(None)
    range_options: Optional[WebformRangeOptions] = Field(None)


class Section(BaseModel):
    """Section in webform"""

    id: Optional[str] = Field(default_factory=id_generator)
    name: Optional[str] = Field(None)
    inputs: List[Input] = Field([])
    hidden: Optional[bool] = Field(False)


class Webform(BaseModel):
    """User defined webform for ktype"""

    model_config = ConfigDict(
        alias_generator=lambda field_name: to_camel(  # pylint: disable=W0108
            field_name
        )
    )
    semantics_enabled: Optional[bool] = Field(False)
    sections_enabled: Optional[bool] = Field(False)
    class_mapping: Optional[str] = Field(None)
    sections: List[Section] = Field([])

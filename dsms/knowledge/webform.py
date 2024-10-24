"""Webform model"""

from typing import Any, List, Optional

from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel


class WebformSelectOption(BaseModel):
    """Choices in webform"""

    label: Optional[str] = Field(None)
    value: Optional[Any] = Field(None)
    disabled: Optional[bool] = Field(False)


class Inputs(BaseModel):
    """Input fields in the sections in webform"""

    model_config = ConfigDict(
        alias_generator=lambda field_name: to_camel(  # pylint: disable=W0108
            field_name
        )
    )

    id: Optional[str] = Field(None)
    label: Optional[str] = Field(None)
    widget: Optional[str] = Field(None)
    default_value: Optional[Any] = Field(None)
    value: Optional[Any] = Field(None)
    choices: List[WebformSelectOption] = Field([])
    on_change: Optional[Any] = Field(None)
    check: Optional[Any] = Field(None)
    error: Optional[str] = Field(None)
    feedback: Optional[str] = Field(None)
    hint: Optional[str] = Field(None)
    measurement_unit: Optional[str] = Field(None)
    mapping: Optional[str] = Field(None)
    mapping_name: Optional[str] = Field(None)
    mapping_kitem_id: Optional[str] = Field(None)
    knowledge_type: Optional[str] = Field(None)
    knowledge_service_url: Optional[str] = Field(None)
    vocabulary_service_url: Optional[str] = Field(None)
    hidden: Optional[bool] = Field(False)
    ignore: Optional[bool] = Field(False)
    extra: dict = Field({})


class Sections(BaseModel):
    """Sections in webform"""

    id: Optional[str] = Field(None)
    name: Optional[str] = Field(None)
    inputs: List[Inputs] = Field([])
    hidden: Optional[bool] = Field(False)


class Webform(BaseModel):
    """User defined webform for ktype"""

    model_config = ConfigDict(
        alias_generator=lambda field_name: to_camel(  # pylint: disable=W0108
            field_name
        )
    )
    semantics_enabled: Optional[bool] = Field(False)
    rdf_type: Optional[str] = Field(None)
    sections: List[Sections] = Field([])

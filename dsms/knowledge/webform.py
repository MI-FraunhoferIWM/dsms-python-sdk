from typing import List, Any, Optional, Union
from uuid import UUID
from pydantic import BaseModel, Field

class Inputs(BaseModel):
    id: Union[UUID, str] = Field(None, description="")
    label: Optional[str] = Field(None, description="")
    widget: Optional[str] = Field(None, description="")
    default_value: Optional[str] = Field(None, description="")
    value: Optional[Any] = Field(None, description="")
    check: Optional[str] = Field(None, description="")
    error: Optional[str] = Field(None, description="")
    feedback: Optional[str] = Field(None, description="")
    hint: Optional[str] = Field(None, description="")
    measurement_unit: Optional[str] = Field(None, description="")
    mapping: Optional[str] = Field(None, description="")
    knowledge_type: Optional[str] = Field(None, description="")
    knowledge_service_url: Optional[str] = Field(None, description="")
    vocabulary_service_url: Optional[str] = Field(None, description="")
    hidden: Optional[bool] = Field(False, description="")
    ignore: Optional[bool] = Field(False, description="")
    extra: dict = Field({}, description="")
    
class Sections(BaseModel):
    id:  Union[UUID, str] = Field(None, description="")
    name: Optional[str] = Field(None, description="")
    inputs: List[Inputs] = Field([], description="")
    hidden: Optional[bool] = Field(False, description="")


class Webform(BaseModel):
    semantics_enabled: Optional[bool] = Field(False, description="")
    sections: List[Sections] = Field([], description="")
"""Webform model"""

import logging
from enum import Enum
from typing import TYPE_CHECKING, Any, List, Optional, Union

from pydantic import AnyUrl, BaseModel, ConfigDict, Field, PrivateAttr, model_validator
from pydantic.alias_generators import to_camel

from dsms.knowledge.utils import id_generator

from dsms.knowledge.properties.custom_datatype import (  # isort:skip
    NumericalDataType,
)
from dsms.core.logging import handler  # isort:skip

if TYPE_CHECKING:
    from dsms.knowledge.kitem import KItem

logger = logging.getLogger(__name__)
logger.addHandler(handler)
logger.propagate = False


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

    label: Optional[str] = Field(None, description="Label of the option")
    value: Optional[Any] = Field(None, description="Value of the option")
    disabled: Optional[bool] = Field(False, description="Disabled option")


class WebformMeasurementUnit(BaseModel):
    """Measurement unit"""

    label: Optional[str] = Field(
        None, description="Label of the measurement unit"
    )
    iri: Optional[AnyUrl] = Field(
        None, description="IRI of the measurement unit"
    )
    symbol: Optional[str] = Field(
        None, description="Symbol of the measurement unit"
    )
    namespace: Optional[AnyUrl] = Field(
        None, description="Namespace of the measurement unit"
    )


class WebformRangeOptions(BaseModel):
    """Range options"""

    min: Optional[int] = Field(0, description="Minimum value")
    max: Optional[int] = Field(0, description="Maximum value")
    step: Optional[int] = Field(0, description="Step value")
    range: Optional[bool] = Field(False, description="Range value")


class RelationMappingType(Enum):
    """
    Relation mapping type
    """

    OBJECT_PROPERY = "object_property"
    DATA_PROPERTY = "data_property"
    ANNOTATION_PROPERTY = "annotation_property"


class RelationMapping(BaseModel):
    """Relation mapping"""

    iri: str = Field(..., description="IRI of the annotation", max_length=200)
    type: Optional[RelationMappingType] = Field(
        None, description="Type of the annotation"
    )
    class_iri: Optional[str] = Field(
        None,
        description="Target class IRI if the type of relation is an object property",
    )
    _kitem = PrivateAttr(default=None)

    model_config = ConfigDict(
        alias_generator=lambda field_name: to_camel(  # pylint: disable=W0108
            field_name
        )
    )

    def __setattr__(self, key, value) -> None:
        logger.debug(
            "Setting property for relation mapping `%s` with key `%s` with value `%s`.",
            self.iri,
            key,
            value,
        )

        # Set kitem as updated
        if key != "kitem" and self.kitem:
            logger.debug(
                "Setting related kitem with id `%s` as updated",
                self.kitem.id,
            )
            self.kitem.context.buffers.updated.update(
                {self.kitem.id: self.kitem}
            )
        elif key == "kitem":
            self.kitem = value

        super().__setattr__(key, value)

    @property
    def kitem(self) -> "KItem":
        """
        KItem instance the entry is related to

        Returns:
            KItem: KItem instance
        """
        return self._kitem

    @kitem.setter
    def kitem(self, value: "KItem") -> None:
        """
        Setter for the KItem instance related to the relation mapping.

        Args:
            value (KItem): The KItem instance to associate with the relation mapping.
        """
        self._kitem = value


class Input(BaseModel):
    """Input fields in the sections in webform"""

    model_config = ConfigDict(
        alias_generator=lambda field_name: to_camel(  # pylint: disable=W0108
            field_name
        )
    )

    id: Optional[str] = Field(
        default_factory=id_generator, description="ID of the input"
    )
    label: Optional[str] = Field(None, description="Label of the input")
    widget: Optional[Widget] = Field(None, description="Widget of the input")
    required: Optional[bool] = Field(False, description="Required input")
    value: Optional[Any] = Field(None, description="Value of the input")
    hint: Optional[str] = Field(None, description="Hint of the input")
    hidden: Optional[bool] = Field(False, description="Hidden input")
    ignore: Optional[bool] = Field(False, description="Ignore input")
    select_options: List[WebformSelectOption] = Field(
        [], description="List of select options"
    )
    measurement_unit: Optional[WebformMeasurementUnit] = Field(
        None, description="Measurement unit"
    )
    relation_mapping: Optional[RelationMapping] = Field(
        None, description="Relation mapping"
    )
    relation_mapping_extra: Optional[RelationMapping] = Field(
        None, description="Relation mapping extra"
    )
    multiple_selection: Optional[bool] = Field(
        False, description="Multiple selection"
    )
    knowledge_type: Optional[str] = Field(None, description="Knowledge type")
    range_options: Optional[WebformRangeOptions] = Field(
        None, description="Range options"
    )
    placeholder: Optional[str] = Field(
        None, description="Placeholder for the input"
    )


class Section(BaseModel):
    """Section in webform"""

    id: Optional[str] = Field(
        default_factory=id_generator, description="ID of the section"
    )
    name: Optional[str] = Field(None, description="Name of the section")
    inputs: List[Input] = Field(
        [], description="List of inputs in the section"
    )
    hidden: Optional[bool] = Field(False, description="Hidden section")


class Webform(BaseModel):
    """User defined webform for ktype"""

    model_config = ConfigDict(
        alias_generator=lambda field_name: to_camel(  # pylint: disable=W0108
            field_name
        )
    )
    semantics_enabled: Optional[bool] = Field(
        False, description="Semantics enabled"
    )
    sections_enabled: Optional[bool] = Field(
        False, description="Sections enabled"
    )
    class_mapping: Optional[str] = Field(None, description="Class mapping")
    sections: List[Section] = Field([], description="List of sections")


class MeasurementUnit(BaseModel):
    """Measurement unit"""

    iri: Optional[AnyUrl] = Field(
        None, description="IRI of the annotation", max_length=200
    )
    label: Optional[str] = Field(
        None, description="Label of the measurement unit", max_length=100
    )
    symbol: Optional[str] = Field(
        None, description="Symbol of the measurement unit", max_length=100
    )
    namespace: Optional[AnyUrl] = Field(
        None, description="Namespace of the measurement unit"
    )
    _kitem = PrivateAttr(default=None)

    def __setattr__(self, key, value) -> None:
        """
        Set an attribute of the MeasurementUnit instance.

        This method overrides the default behavior of setting an attribute.
        It logs the action and updates the related KItem in the buffer if
        applicable. If the key is 'kitem', it sets the KItem instance directly.

        Args:
            key (str): The name of the attribute to set.
            value (Any): The value to set for the attribute.
        """
        logger.debug(
            "Setting property for measurement unit `%s` with key `%s` with value `%s`.",
            self.iri,
            key,
            value,
        )

        # Set kitem as updated
        if key != "kitem" and self.kitem:
            logger.debug(
                "Setting related kitem with id `%s` as updated",
                self.kitem.id,
            )
            self.kitem.context.buffers.updated.update(
                {self.kitem.id: self.kitem}
            )

        elif key == "kitem":
            self.kitem = value

        super().__setattr__(key, value)

    @property
    def kitem(self) -> "KItem":
        """
        KItem instance the entry is related to

        Returns:
            KItem: KItem instance
        """
        return self._kitem

    @kitem.setter
    def kitem(self, value: "KItem") -> None:
        """
        Setter for the KItem instance related to the measurement unit.

        Args:
            value (KItem): The KItem instance to associate with the measurement unit.
        """
        self._kitem = value


class KnowledgeItemReference(BaseModel):
    """Reference to a knowledge item if linked in the custom properties"""

    id: str = Field(..., description="ID of the knowledge item")
    name: str = Field(..., description="Name of the knowledge item")


class Entry(BaseModel):
    """
    Entry in a custom properties section
    """

    id: str = Field(default_factory=id_generator)
    type: Widget = Field(..., description="Type of the entry")
    label: str = Field(..., description="Label of the entry")
    value: Optional[
        Union[
            str,
            int,
            KnowledgeItemReference,
            float,
            bool,
            List,
            NumericalDataType,
        ]
    ] = Field(None, description="Value of the entry")
    measurementUnit: Optional[MeasurementUnit] = Field(
        None, description="Measurement unit of the entry"
    )
    relationMapping: Optional[RelationMapping] = Field(
        None, description="Relation mapping of the entry"
    )
    _kitem = PrivateAttr(default=None)

    def __setattr__(self, key, value) -> None:
        logger.debug(
            "Setting property for entry `%s` with key `%s` with value `%s`.",
            self.name,
            key,
            value,
        )

        # Set kitem as updated
        if key != "kitem" and self.kitem:
            logger.debug(
                "Setting related kitem with id `%s` as updated",
                self.kitem.id,
            )
            self.kitem.context.buffers.updated.update(
                {self.kitem.id: self.kitem}
            )
        elif key == "kitem":
            self.kitem = value
            if self.measurementUnit:
                self.measurementUnit.kitem = value
            if self.relationMapping:
                self.relationMapping.kitem = value

        super().__setattr__(key, value)

    @property
    def kitem(self) -> "KItem":
        """
        KItem instance the entry is related to

        Returns:
            KItem: KItem instance
        """
        return self._kitem

    @kitem.setter
    def kitem(self, kitem: "KItem"):
        """
        Set KItem instance the entry is related to

        Args:
            kitem (KItem): KItem instance
        """
        self._kitem = kitem

    @property
    def ktype(self) -> "KItem":
        """
        KType instance the entry is related to

        Returns:
            KType: KType instance
        """
        return self.kitem.ktype

    @property
    def webform(self) -> "Webform":
        """
        Retrieve the webform associated with the KType of this entry.

        Returns:
            Webform: The webform instance related to the KType.
        """
        return self.ktype.webform

    @model_validator(mode="after")
    @classmethod
    def _validate_inputs(cls, self: "Entry") -> "Entry":
        spec = cls._get_input_spec(self)
        choices = None

        # check if widget is mapped to a data type
        if spec.widget in (
            Widget.TEXT,
            Widget.FILE,
            Widget.TEXTAREA,
            Widget.VOCABULARY_TERM,
        ):
            dtype = str
        elif spec.widget in (Widget.NUMBER, Widget.SLIDER):
            dtype = NumericalDataType
        elif spec.widget == Widget.CHECKBOX:
            dtype = bool
        elif spec.widget in (Widget.SELECT, Widget.RADIO, Widget.MULTI_SELECT):
            if spec.widget == Widget.MULTI_SELECT:
                dtype = list
            else:
                dtype = str
            choices = [choice.value for choice in spec.select_options]
        elif spec.widget == Widget.KNOWLEDGE_ITEM:
            dtype = KnowledgeItemReference
        else:
            raise ValueError(
                f"Widget type is not mapped to a data type: {self.widget}"
            )

        # check if value is set
        if self.value is None and spec.value is not None:
            self.value = spec.value

        # check if value is of correct type
        if self.value is not None and not isinstance(self.value, dtype):
            raise ValueError(
                f"Value of type {type(self.value)} is not of type {dtype}"
            )
        if (
            self.value is not None
            and choices is not None
            and self.value not in choices
        ):
            raise ValueError(
                f"Value {self.value} is not a valid choice for entry {self.label}"
            )
        if self.value is None and spec.value is None and self.required:
            raise ValueError(f"Value for entry {self.label} is required")

        # set name and kitem of numerical data type
        if isinstance(self.value, NumericalDataType):
            self.value.name = self.label
            self.value.kitem = self.kitem

        return self

    @classmethod
    def _get_input_spec(cls, self: "Entry"):
        potential_spec = []
        spec = None
        for section in self.webform.sections:
            for inp in section.inputs:
                if inp.id == self.id:
                    potential_spec.append(inp)
        if len(potential_spec) == 0:
            raise ValueError(
                f"Could not find input spec for entry {self.label}"
            )
        if len(potential_spec) > 1:
            raise ValueError(
                f"Found multiple input specs for entry {self.label}"
            )
        spec = potential_spec.pop()
        return spec


class CustomPropertiesSection(BaseModel):
    """
    Section for custom properties
    """

    id: Optional[str] = Field(default_factory=id_generator)
    name: str = Field(..., description="Name of the section")
    entries: List[Entry] = Field([], description="Entries of the section")
    _kitem = PrivateAttr(default=None)

    @property
    def kitem(self) -> "KItem":
        """
        KItem instance the section is related to

        Returns:
            KItem: KItem instance
        """
        return self._kitem

    @kitem.setter
    def kitem(self, kitem: "KItem"):
        """
        Set KItem instance the section is related to

        Args:
            kitem (KItem): KItem instance
        """
        self._kitem = kitem

    def __setattr__(self, key, value) -> None:
        """
        Set an attribute of the section.

        This method is overridden to intercept setting of properties. If the key is
        not a valid attribute of the section, it is interpreted as a label of an
        entry of the section. The value is then set for the entry.

        Args:
            key: The key of the attribute to be set.
            value: The value of the attribute to be set.
        """
        logger.debug(
            "Setting property for section `%s` with key `%s` with value `%s`.",
            self.name,
            key,
            value,
        )

        # Set kitem as updated
        if key != "kitem" and self.kitem:
            logger.debug(
                "Setting related kitem with id `%s` as updated",
                self.kitem.id,
            )
            self.kitem.context.buffers.updated.update(
                {self.kitem.id: self.kitem}
            )
        elif key == "kitem":
            self.kitem = value
            for entry in self.entries:
                entry.kitem = value

        # Set value
        if key not in self.model_dump().keys():
            to_be_updated = []
            for entry in self.entries:
                if entry.label == key:
                    to_be_updated.append(entry)
            if len(to_be_updated) == 0:
                raise AttributeError(
                    f"Section with name '{self.name}' has no attribute '{key}'"
                )
            if len(to_be_updated) > 1:
                raise AttributeError(
                    f"""Section with name '{self.name}'
                    has multiple attributes '{key}'. Please specify section!"""
                )

            to_be_updated = to_be_updated.pop()
            to_be_updated.value = value
        else:
            super().__setattr__(key, value)

    def __getattr__(self, key) -> Any:
        """
        Retrieve an entry from the section by its label.

        This method searches through the entries of the section to find an entry whose
        label matches the given key. If the entry is found and is unique, it returns the entry.
        If the entry is not found, or if multiple entries with the same label are found, it raises
        an AttributeError. If the attribute exists on the BaseModel, it is retrieved using the
        superclass's __getattr__ method.

        Args:
            key (str): The label of the entry to retrieve.

        Returns:
            Entry: The entry matching the given label.

        Raises:
            AttributeError: If no entry or multiple entries with the given label are found.
        """
        target = []
        if not hasattr(self, key):
            for entry in self.entries:
                if entry.label == key:
                    target.append(entry)
            if len(target) == 0:
                raise AttributeError(
                    f"Section with name `{self.name}` has no attribute '{key}'"
                )
            if len(target) > 1:
                raise AttributeError(
                    f"""Section with name `{self.name}`
                    has multiple attributes '{key}'. Please specify section!"""
                )

            target = target.pop()
        else:
            target = super().__getattr__(key)
        return target


class KItemCustomPropertiesModel(BaseModel):
    """
    A custom properties model for a KItem.
    """

    sections: List[CustomPropertiesSection] = Field(
        [], description="Sections of custom properties"
    )
    _kitem = PrivateAttr(default=None)

    @property
    def kitem(self) -> "KItem":
        """
        KItem instance the custom properties is related to

        Returns:
            KItem: KItem instance
        """
        return self._kitem

    @kitem.setter
    def kitem(self, kitem: "KItem"):
        """
        Set KItem instance the custom properties is related to

        Args:
            kitem (KItem): KItem instance
        """
        self._kitem = kitem

    def __getattr__(self, key):
        """
        Retrieve an entry from the custom properties sections by its label.

        This method searches through the entries of each section within the custom properties
        model to find an entry whose label matches the given key. If the entry is found and
        is unique, it returns the entry. If the entry is not found, or if multiple entries
        with the same label are found, it raises an AttributeError. If the attribute exists
        on the BaseModel, it is retrieved using the superclass's __getattr__ method.

        Args:
            key (str): The label of the entry to retrieve.

        Returns:
            Entry: The entry matching the given label.

        Raises:
            AttributeError: If no entry or multiple entries with the given label are found.
        """
        target = []
        if not hasattr(self, key):
            for section in self.sections:
                for entry in section.entries:
                    if entry.label == key:
                        target.append(entry)
            if len(target) == 0:
                raise AttributeError(
                    f"Custom properties model has no attribute '{key}'"
                )
            if len(target) > 1:
                raise AttributeError(
                    f"""Custom properties model has multiple attributes
                    '{key}'. Please specify section!"""
                )
            target = target.pop()
        else:
            target = super().__getattr__(key)
        return target

    def __setattr__(self, key, value) -> None:
        """
        Set a custom property's value by its label.

        This method searches through the entries of each section within the custom properties
        model to find an entry whose label matches the given key. If the entry is found and is
        unique, it sets the value of that entry. If the entry is not found, or if multiple
        entries with the same label are found, it raises an AttributeError. If the attribute
        exists on the BaseModel, it is set using the superclass's __setattr__ method.

        Args:
            key (str): The label of the entry to set.
            value (Any): The new value of the entry.

        Raises:
            AttributeError: If no entry or multiple entries with the given label are found.
        """

        logger.debug(
            "Setting property for custom properties model with key `%s` with value `%s`.",
            key,
            value,
        )

        # Set kitem as updated
        if key != "kitem" and self.kitem:
            logger.debug(
                "Setting related kitem for custom properties with id `%s` as updated",
                self.kitem.id,
            )
            self.kitem.context.buffers.updated.update(
                {self.kitem.id: self.kitem}
            )
        elif key == "kitem":
            self.kitem = value
            self.sections.kitem = value

        # Set value in model
        if key not in self.model_dump().keys():
            to_be_updated = []
            for section in self.sections:
                for entry in section.entries:
                    if entry.label == key:
                        to_be_updated.append(entry)
            if len(to_be_updated) == 0:
                raise AttributeError(
                    f"Custom properties model has no attribute '{key}'"
                )
            if len(to_be_updated) > 1:
                raise AttributeError(
                    f"""Custom properties model has multiple attributes
                    '{key}'. Please specify section!"""
                )
            to_be_updated = to_be_updated.pop()
            to_be_updated.value = value
        else:
            super().__setattr__(key, value)

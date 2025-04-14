"""Webform model"""

import logging
from enum import Enum
from typing import Any, Dict, List, Optional, Union
from uuid import UUID

from pydantic.alias_generators import to_camel

from pydantic import (  # isort:skip
    AnyUrl,
    BaseModel,
    ConfigDict,
    Field,
    model_validator,
    field_validator,
    AliasGenerator,
    AliasChoices,
)

from dsms.core.session import Session  # isort:skip

from dsms.knowledge.utils import (  # isort:skip
    generate_id,
    print_model,
)

from dsms.knowledge.semantics.units.utils import (  # isort:skip
    get_conversion_factor,
    get_property_unit,
)

from dsms.core.logging import handler  # isort:skip


logger = logging.getLogger(__name__)
logger.addHandler(handler)
logger.propagate = False


class Widget(Enum):
    """Enum for widgets"""

    TEXT = "Text"
    FILE = "File"
    TEXTAREA = "Textarea"
    NUMBER = "Number"
    SLIDER = "Slider"
    CHECKBOX = "Checkbox"
    SELECT = "Select"
    RADIO = "Radio"
    KNOWLEDGE_ITEM = "Knowledge item"
    MULTI_SELECT = "Multi-select"


class RelationMappingType(Enum):
    """
    Relation mapping type
    """

    OBJECT_PROPERY = "object_property"
    DATA_PROPERTY = "data_property"
    ANNOTATION_PROPERTY = "annotation_property"
    PROPERTY = "property"


class BaseWebformModel(BaseModel):
    """Base webform model"""

    model_config = ConfigDict(
        alias_generator=AliasGenerator(
            validation_alias=lambda field_name: AliasChoices(
                to_camel(field_name), field_name  # pylint: disable=W0108
            ),
            serialization_alias=lambda field_name: to_camel(  # pylint: disable=W0108
                field_name
            ),
        ),
        use_enum_values=True,
    )

    def __str__(self) -> str:
        """Pretty print the model fields"""
        return print_model(self, "webform")

    def __repr__(self) -> str:
        """Pretty print the model fields"""
        return str(self)


class WebformSelectOption(BaseWebformModel):
    """Choices in webform"""

    key: Optional[str] = Field(None, description="Label of the option")
    label: Optional[Any] = Field(None, description="Value of the option")
    disabled: Optional[bool] = Field(False, description="Disabled option")

    def __str__(self) -> str:
        """Pretty print the model fields"""
        return print_model(self, "select option")

    def __repr__(self) -> str:
        """Pretty print the model fields"""
        return str(self)


class WebformMeasurementUnit(BaseWebformModel):
    """Measurement unit"""

    label: Optional[str] = Field(
        None, description="Label of the measurement unit"
    )
    iri: Optional[Union[str, AnyUrl]] = Field(
        None, description="IRI of the measurement unit"
    )
    symbol: Optional[str] = Field(
        None, description="Symbol of the measurement unit"
    )
    namespace: Optional[Union[str, AnyUrl]] = Field(
        None, description="Namespace of the measurement unit"
    )

    @model_validator(mode="after")
    def check_measurement_unit(cls, self) -> "MeasurementUnit":
        """
        Validate and convert IRI and namespace fields to AnyUrl type.

        This method is a model validator that runs after the model is initialized.
        It ensures that the `iri` and `namespace` fields of the `MeasurementUnit`
        are of type `AnyUrl`. If they are not, it attempts to convert them to
        `AnyUrl`.

        Returns:
            MeasurementUnit: The validated and potentially modified instance.
        """

        if not isinstance(self.iri, AnyUrl):
            self.iri = str(self.iri)
        if not isinstance(self.namespace, AnyUrl):
            self.namespace = str(self.namespace)
        return self

    def __str__(self) -> str:
        """Pretty print the model fields"""
        return print_model(self, "webform measurement unit")

    def __repr__(self) -> str:
        """Pretty print the model fields"""
        return str(self)


class WebformRangeOptions(BaseWebformModel):
    """Range options"""

    min: Optional[Union[int, float]] = Field(0, description="Minimum value")
    max: Optional[Union[int, float]] = Field(0, description="Maximum value")
    step: Optional[Union[int, float]] = Field(0, description="Step value")
    range: Optional[bool] = Field(False, description="Range value")

    def __str__(self) -> str:
        """Pretty print the model fields"""
        return print_model(self, "range options")

    def __repr__(self) -> str:
        """Pretty print the model fields"""
        return str(self)


class WebformSelectOptionEntry(WebformSelectOption):
    """Webform option for a filled selection"""

    value: Optional[str] = Field(None, description="Value of the option")

    def __str__(self) -> str:
        """Pretty print the model fields"""
        return print_model(self, "select option entry")

    def __repr__(self) -> str:
        """Pretty print the model fields"""
        return str(self)


class RelationMapping(BaseWebformModel):
    """Relation mapping"""

    iri: Optional[str] = Field(None, description="IRI of the annotation")
    type: Optional[RelationMappingType] = Field(
        None, description="Type of the annotation"
    )
    class_iri: Optional[str] = Field(
        None,
        description="Target class IRI if the type of relation is an object property",
    )

    def __str__(self) -> str:
        """Pretty print the model fields"""
        return print_model(self, "relation mapping")

    def __repr__(self) -> str:
        """Pretty print the model fields"""
        return str(self)


class Input(BaseWebformModel):
    """Input fields in the sections in webform"""

    id: Optional[str] = Field(
        default_factory=generate_id, description="ID of the input"
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
    knowledge_type: Optional[Union[str, List[str], List[None]]] = Field(
        None, description="Knowledge type"
    )
    range_options: Optional[WebformRangeOptions] = Field(
        None, description="Range options"
    )
    placeholder: Optional[str] = Field(
        None, description="Placeholder for the input"
    )

    def __str__(self) -> str:
        """Pretty print the model fields"""
        return print_model(self, "input")

    def __repr__(self) -> str:
        """Pretty print the model fields"""
        return str(self)


class Section(BaseWebformModel):
    """Section in webform"""

    id: Optional[str] = Field(
        default_factory=generate_id, description="ID of the section"
    )
    name: Optional[str] = Field(None, description="Name of the section")
    inputs: List[Input] = Field(
        [], description="List of inputs in the section"
    )
    hidden: Optional[bool] = Field(False, description="Hidden section")

    def __str__(self) -> str:
        """Pretty print the model fields"""
        return print_model(self, "section")

    def __repr__(self) -> str:
        """Pretty print the model fields"""
        return str(self)


class Webform(BaseWebformModel):
    """User defined webform for ktype"""

    semantics_enabled: Optional[bool] = Field(
        False, description="Semantics enabled"
    )
    sections_enabled: Optional[bool] = Field(
        False, description="Sections enabled"
    )
    class_mapping: Optional[Union[List[str], str]] = Field(
        [], description="Class mapping"
    )
    sections: List[Section] = Field([], description="List of sections")

    def __str__(self) -> str:
        """Pretty print the model fields"""
        return print_model(self, "webform")

    def __repr__(self) -> str:
        """Pretty print the model fields"""
        return str(self)


class MeasurementUnit(BaseWebformModel):
    """Measurement unit"""

    iri: Optional[Union[str, AnyUrl]] = Field(
        None,
        description="IRI of the annotation",
    )
    label: Optional[str] = Field(
        None,
        description="Label of the measurement unit",
    )
    symbol: Optional[str] = Field(
        None,
        description="Symbol of the measurement unit",
    )
    namespace: Optional[Union[str, AnyUrl]] = Field(
        None, description="Namespace of the measurement unit"
    )

    def __str__(self) -> str:
        """Pretty print the model fields"""
        return print_model(self, "measurement_unit")

    def __repr__(self) -> str:
        """Pretty print the model fields"""
        return str(self)

    @model_validator(mode="after")
    def check_measurement_unit(cls, self) -> "MeasurementUnit":
        """
        Validate and convert IRI and namespace fields to AnyUrl type.

        This method is a model validator that runs after the model is initialized.
        It ensures that the `iri` and `namespace` fields of the `MeasurementUnit`
        are of type `AnyUrl`. If they are not, it attempts to convert them to
        `AnyUrl`.

        Returns:
            MeasurementUnit: The validated and potentially modified instance.
        """

        if not isinstance(self.iri, AnyUrl):
            self.iri = str(self.iri)
        if not isinstance(self.namespace, AnyUrl):
            self.namespace = str(self.namespace)
        return self


class KnowledgeItemReference(BaseModel):
    """Reference to a knowledge item if linked in the custom properties"""

    id: Union[str, UUID] = Field(..., description="ID of the knowledge item")
    name: str = Field(..., description="Name of the knowledge item")
    ktype_id: str = Field(..., description="ID of the knowledge type")
    slug: str = Field(..., description="Slug of the knowledge item")

    @field_validator("id")
    @classmethod
    def _validate_uuid(cls, value: Union[str, UUID]) -> str:
        return str(value)

    def __str__(self) -> str:
        """Pretty print the model fields"""
        return print_model(self, "knowledge item reference")

    def __repr__(self) -> str:
        """Pretty print the model fields"""
        return str(self)


class Entry(BaseWebformModel):
    """
    Entry in a custom properties section
    """

    id: str = Field(default_factory=generate_id)
    type: Optional[Widget] = Field(None, description="Type of the entry")
    label: str = Field(..., description="Label of the entry")
    value: Optional[Any] = Field(None, description="Value of the entry")
    measurement_unit: Optional[MeasurementUnit] = Field(
        None,
        description="Measurement unit of the entry",
    )
    relation_mapping: Optional[RelationMapping] = Field(
        None,
        description="Relation mapping of the entry",
    )
    required: Optional[bool] = Field(False, description="Required input")
    kitem_id: Optional[str] = Field(
        None, description="ID of the knowledge item", exclude=True
    )

    def __str__(self) -> str:
        """Pretty print the model fields"""
        return print_model(self, "entry", exclude_extra={"kitem_id"})

    def __repr__(self) -> str:
        """Pretty print the model fields"""
        return str(self)

    def get_unit(self) -> "Dict[str, Any]":
        """Get unit for the property"""
        return get_property_unit(
            self.kitem_id,  # pylint: disable=no-member
            self.label,
            self.measurement_unit,
            is_dataframe_column=True,
            autocomplete_symbol=Session.dsms.config.autocomplete_units,  # pylint: disable=no-member
        )

    def convert_to(
        self,
        unit_symbol_or_iri: str,
        decimals: "Optional[int]" = None,
        use_input_iri: bool = True,
        val: "Optional[Union[int, float]]" = None,
    ) -> float:
        """
        Convert the data of property to a different unit.

        Args:
            unit_symbol_or_iri (str): Symbol or IRI of the unit to convert to.
            decimals (Optional[int]): Number of decimals to round the result to. Defaults to None.
            use_input_iri (bool): If True, use IRI for unit comparison. Defaults to False.

        Returns:
            float: converted value of the property
        """
        value = val or self.value
        if isinstance(value, list):
            converted = []
            for iterval in value:
                converted.append(
                    self.convert_to(
                        unit_symbol_or_iri, decimals, use_input_iri, iterval
                    )
                )
        else:
            if not isinstance(value, (float, int)):
                raise ValueError("Value must be a number")
            unit = self.get_unit()
            if use_input_iri:
                input_str = unit.get("iri")
            else:
                input_str = unit.get("symbol")
            converted = value * get_conversion_factor(
                input_str, unit_symbol_or_iri, decimals=decimals
            )
        return converted


class CustomPropertiesSection(BaseWebformModel):
    """
    Section for custom properties
    """

    id: Optional[str] = Field(default_factory=generate_id)
    name: str = Field(..., description="Name of the section")
    entries: List[Entry] = Field([], description="Entries of the section")

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
        # Set value
        if key not in self.model_dump():
            to_be_updated = []
            for entry in self.entries:  # pylint: disable=not-an-iterable
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
        if not key in self.model_dump():
            for entry in self.entries:  # pylint: disable=not-an-iterable
                if entry.label == key:
                    target.append(entry)
            if len(target) == 0:
                raise AttributeError(
                    f"Section with name `{self.name}` has no attribute '{key}'"
                )
            if len(target) > 1:
                raise AttributeError(
                    f"""Section with name `{self.name}`
                    has multiple attributes '{key}'.
                    Please specify the concrete entry via indexing !"""
                )

            target = target.pop()
        else:
            target = super().__getattr__(key)
        return target

    def __getitem__(self, key):
        """
        Retrieve an entry from the section by its index.

        Args:
            key (int): The index of the entry to retrieve.

        Returns:
            Entry: The entry at the given index.

        Raises:
            IndexError: If the index is out of range.
        """
        return self.entries[key]  # pylint: disable=unsubscriptable-object

    def __iter__(self):
        """
        Iterate over the entries of the section.

        Yields:
            Entry: The entries in the section.
        """
        yield from self.entries  # pylint: disable=not-an-iterable

    def __len__(self):
        """
        Return the number of entries in the section.

        Returns:
            int: The number of entries in the section.
        """
        return len(self.entries)

    def __str__(self) -> str:
        """Pretty print the model fields"""
        return print_model(self, "section")

    def __repr__(self) -> str:
        """Pretty print the model fields"""
        return str(self)


class KItemCustomPropertiesModel(BaseWebformModel):
    """
    A custom properties model for a KItem.
    """

    sections: List[CustomPropertiesSection] = Field(
        [], description="Sections of custom properties"
    )

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

        if not key in self.model_dump():
            for section in self.sections:  # pylint: disable=not-an-iterable
                if section.name == key:
                    target.append(section)
                for entry in section.entries:
                    if entry.label == key:
                        target.append(entry)
            if len(target) == 0:
                raise AttributeError(
                    f"Custom properties model has no entry or section '{key}'"
                )
            if len(target) > 1:
                raise AttributeError(
                    f"""Custom properties model has multiple entries or sections for
                    '{key}'. Please specify section via list indexing!"""
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

        # Set value in model
        if key not in self.model_dump().keys():
            to_be_updated = []
            for section in self.sections:  # pylint: disable=not-an-iterable
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

    def __iter__(self):
        """
        Iterate over the sections in the custom properties.

        This method yields each section within the custom properties model,
        allowing for iteration over all sections.

        Yields:
            CustomPropertiesSection: The next section in the custom properties.
        """
        yield from self.sections  # pylint: disable=not-an-iterable

    def __len__(self):
        """
        Return the number of sections in the custom properties.

        Returns:
            int: The number of sections in the custom properties.
        """
        return len(self.sections)

    def __getitem__(self, key):
        """
        Retrieve a section from the custom properties by its index.

        Args:
            key (int): The index of the section to retrieve.

        Returns:
            CustomPropertiesSection: The section at the specified index.
        """
        return self.sections[key]  # pylint: disable=unsubscriptable-object

    def __str__(self) -> str:
        """Pretty print the model fields"""
        return print_model(self, "custom_properties")

    def __repr__(self) -> str:
        """Pretty print the model fields"""
        return str(self)

    # OVERRIDE
    def model_dump(self, *args, flat: bool = False, **kwargs):
        """
        Dump the custom properties model fields into a dictionary format.

        This method converts the model's sections and entries into a dictionary
        representation. If the `flat` parameter is set to True, it attempts to
        create a flat dictionary where each entry's label is a key and its value
        is the corresponding value. If duplicate labels are found, it raises a
        ValueError. If `flat` is False, the method utilizes the superclass's
        `model_dump` method for the output.

        Args:
            *args: Additional arguments for the superclass's `model_dump`.
            flat (bool): Whether to produce a flat dictionary. Defaults to False.
            **kwargs: Additional keyword arguments for the superclass's `model_dump`.

        Returns:
            dict: A dictionary representation of the custom properties model.

        Raises:
            ValueError: If `flat` is True and duplicate entry labels are found.
        """

        if flat:
            dumped = {}
            for section in self.sections:  # pylint: disable=not-an-iterable
                for entry in section.entries:
                    if entry.label in dumped:
                        raise ValueError(
                            f"""Flat model_dump is not possible.
                            Custom properties model has multiple entries for '{entry.label}'"""
                        )
                    dumped[entry.label] = entry.value
        else:
            dumped = super().model_dump(*args, **kwargs)
        return dumped

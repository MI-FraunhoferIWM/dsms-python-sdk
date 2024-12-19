"""Webform model"""

import logging
from enum import Enum
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Union

from pydantic.alias_generators import to_camel

from pydantic import (  # isort:skip
    AnyUrl,
    BaseModel,
    ConfigDict,
    Field,
    model_validator,
    AliasGenerator,
    AliasChoices,
)

from dsms.knowledge.utils import (  # isort:skip
    _map_data_type_to_widget,
    generate_id,
    print_model,
)

from dsms.knowledge.semantics.units.utils import (  # isort:skip
    get_conversion_factor,
    get_property_unit,
)

from dsms.core.logging import handler  # isort:skip

if TYPE_CHECKING:
    from dsms.knowledge.ktype import KType

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
    MULTI_SELECT = "Multi-select"


class WebformSelectOption(BaseModel):
    """Choices in webform"""

    label: Optional[str] = Field(None, description="Label of the option")
    value: Optional[Any] = Field(None, description="Value of the option")
    disabled: Optional[bool] = Field(False, description="Disabled option")

    def __str__(self) -> str:
        """Pretty print the model fields"""
        return print_model(self, "select option")

    def __repr__(self) -> str:
        """Pretty print the model fields"""
        return str(self)


class WebformMeasurementUnit(BaseModel):
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


class WebformRangeOptions(BaseModel):
    """Range options"""

    min: Optional[Union[int, float]] = Field(0, description="Minimum value")
    max: Optional[Union[int, float]] = Field(0, description="Maximum value")
    step: Optional[Union[int, float]] = Field(0, description="Step value")
    range: Optional[Union[int, float]] = Field(
        False, description="Range value"
    )

    def __str__(self) -> str:
        """Pretty print the model fields"""
        return print_model(self, "range options")

    def __repr__(self) -> str:
        """Pretty print the model fields"""
        return str(self)


class RelationMappingType(Enum):
    """
    Relation mapping type
    """

    OBJECT_PROPERY = "object_property"
    DATA_PROPERTY = "data_property"
    ANNOTATION_PROPERTY = "annotation_property"


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
        exclude={"kitem"},
        use_enum_values=True,
    )

    kitem: Optional[Any] = Field(
        None, description="Associated KItem instance", exclude=True, hide=True
    )

    @property
    def ktype(self) -> "KType":
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

    @property
    def dsms(self):
        """
        Get the DSMS instance associated with the kitem.

        This property retrieves the DSMS instance related to the kitem
        of the custom properties section.

        Returns:
            DSMS: The DSMS instance associated with the kitem.
        """
        return self.kitem.dsms

    def __str__(self) -> str:
        """Pretty print the model fields"""
        return print_model(self, "webform")

    def __repr__(self) -> str:
        """Pretty print the model fields"""
        return str(self)

    def __setattr__(self, key, value) -> None:
        """
        Set an attribute of the model.

        This method sets an attribute of the model and logs the operation.
        If the attribute being set is `kitem`, it directly assigns the value.
        For other attributes, it marks the associated `kitem` as updated in the
        session buffers if it exists.

        Args:
            key (str): The name of the attribute to set.
            value (Any): The value to set for the attribute.
        """
        logger.debug(
            "Setting property for model attribute with key `%s` with value `%s`.",
            key,
            value,
        )

        # Set kitem as updated
        if key != "kitem" and self.kitem:
            logger.debug(
                "Setting related kitem with id `%s` as updated",
                self.kitem.id,
            )
            self.kitem.session.buffers.updated.update(
                {self.kitem.id: self.kitem}
            )

        elif key == "kitem":
            self.kitem = value

        super().__setattr__(key, value)


class RelationMapping(BaseWebformModel):
    """Relation mapping"""

    iri: str = Field(..., description="IRI of the annotation")
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
    knowledge_type: Optional[str] = Field(None, description="Knowledge type")
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

    id: str = Field(..., description="ID of the knowledge item")
    name: str = Field(..., description="Name of the knowledge item")

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
    value: Optional[
        Union[
            str,
            int,
            float,
            KnowledgeItemReference,
            bool,
            List,
        ]
    ] = Field(None, description="Value of the entry")
    measurement_unit: Optional[MeasurementUnit] = Field(
        None,
        description="Measurement unit of the entry",
    )
    relation_mapping: Optional[RelationMapping] = Field(
        None,
        description="Relation mapping of the entry",
    )
    required: Optional[bool] = Field(False, description="Required input")

    def __setattr__(self, key, value) -> None:
        """
        Set an attribute of the Entry instance.

        This method overrides the default behavior of setting an attribute.
        It sets the KItem instance of the measurement unit and relation mapping
        if the key is 'kitem'.

        Args:
            key (str): The name of the attribute to set.
            value (Any): The value to set for the attribute.
        """
        if key == "kitem":
            if self.measurement_unit:
                self.measurement_unit.kitem = (  # pylint: disable=assigning-non-slot
                    value
                )
            if self.relation_mapping:
                self.relation_mapping.kitem = (  # pylint: disable=assigning-non-slot
                    value
                )

        super().__setattr__(key, value)

    def __str__(self) -> str:
        """Pretty print the model fields"""
        return print_model(self, "entry")

    def __repr__(self) -> str:
        """Pretty print the model fields"""
        return str(self)

    def get_unit(self) -> "Dict[str, Any]":
        """Get unit for the property"""
        if not isinstance(self.value, (float, int)):
            raise ValueError("Value must be a number")
        return get_property_unit(
            self.kitem.id,  # pylint: disable=no-member
            self.label,
            self.measurement_unit,
            is_dataframe_column=True,
            autocomplete_symbol=self.kitem.dsms.config.autocomplete_units,  # pylint: disable=no-member
        )

    def convert_to(
        self,
        unit_symbol_or_iri: str,
        decimals: "Optional[int]" = None,
        use_input_iri: bool = True,
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
        if not isinstance(self.value, (float, int)):
            raise ValueError("Value must be a number")
        unit = self.get_unit()
        if use_input_iri:
            input_str = unit.get("iri")
        else:
            input_str = unit.get("symbol")
        return self.value * get_conversion_factor(
            input_str, unit_symbol_or_iri, decimals=decimals
        )

    @model_validator(mode="after")
    @classmethod
    def _validate_inputs(cls, self: "Entry") -> "Entry":
        spec = cls._get_input_spec(self)
        if spec:
            if len(spec) == 0:
                raise ValueError(
                    f"Could not find input spec for entry {self.label}"
                )
            if len(spec) > 1:
                raise ValueError(
                    f"Found multiple input specs for entry {self.label}"
                )
            spec = spec.pop()
            self.type = spec.widget
            default_value = spec.value
            select_options = spec.select_options
        elif self.type and not spec:
            default_value = None
            select_options = []
        else:
            self.type = _map_data_type_to_widget(self.value)
            default_value = None
            select_options = []

        dtype = None
        choices = None

        # check if widget is mapped to a data type
        if self.type in (
            Widget.TEXT.value,
            Widget.FILE.value,
            Widget.TEXTAREA.value,
            Widget.VOCABULARY_TERM.value,
        ):
            dtype = str
        elif self.type in (Widget.NUMBER.value, Widget.SLIDER.value):
            dtype = (int, float)
        elif self.type == Widget.CHECKBOX.value:
            dtype = bool
        elif self.type in (
            Widget.SELECT.value,
            Widget.RADIO.value,
            Widget.MULTI_SELECT.value,
        ):
            if self.type == Widget.MULTI_SELECT.value:
                dtype = list
            else:
                dtype = str
            choices = [choice.value for choice in select_options]
        elif self.type == Widget.KNOWLEDGE_ITEM.value:
            dtype = KnowledgeItemReference
        else:
            raise ValueError(
                f"Widget type is not mapped to a data type: {self.type}"
            )

        # check if value is set
        if self.value is None and default_value is not None:
            self.value = default_value

        # check if value is of correct type
        if self.value is not None and not isinstance(self.value, dtype):
            raise ValueError(
                f"Value of type {type(self.value)} is not of type {dtype}"
            )
        if self.value is not None and choices is not None:
            error_message = f"""Value {self.value} is not a valid choice for entry {self.label}.
            Valid choices are: {choices}"""
            # in case of multi-select
            if isinstance(self.value, list):
                for value in self.value:
                    if value not in choices:
                        raise ValueError(error_message)
            # in case of single-select
            else:
                if self.value not in choices:
                    raise ValueError(error_message)
        if self.value is None and default_value is None and self.required:
            raise ValueError(f"Value for entry {self.label} is required")

        return self

    @classmethod
    def _get_input_spec(cls, self: "Entry"):
        spec = []
        if self.webform:
            for section in self.webform.sections:
                for inp in section.inputs:
                    if inp.id == self.id:
                        spec.append(inp)
        return spec


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
        if key == "kitem":
            for entry in self.entries:  # pylint: disable=not-an-iterable
                entry.kitem = value  # pylint: disable=assigning-non-slot

        # Set value
        if key not in self.model_dump() and key != "kitem":
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
        if not key in self.model_dump() and key != "kitem":
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

    @model_validator(mode="before")
    @classmethod
    def set_kitem(cls, self: Dict[str, Any]) -> Dict[str, Any]:
        """
        Set kitem for all entries of the section.

        This validator is called before the model is validated. It sets the kitem
        for all entries of the section if the kitem is set.

        Args:
            self (CustomPropertiesSection): The section to set the kitem for.
        """
        kitem = self.get("kitem")
        if kitem:
            for entry in self.get("entries"):
                if not "kitem" in entry:
                    entry["kitem"] = kitem
        return self

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

        if not key in self.model_dump() and key != "kitem":
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

        if key == "kitem":
            self.sections.kitem = value  # pylint: disable=assigning-non-slot

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

    @model_validator(mode="before")
    @classmethod
    def set_kitem(cls, self: Dict[str, Any]) -> Dict[str, Any]:
        """
        Set kitem for all sections of the custom properties model.

        This validator is called before the model is validated. It sets the kitem
        for all sections of the custom properties model if the kitem is set.

        Args:
            self (KItemCustomPropertiesModel): The custom properties model to set the kitem for.
        """
        kitem = self.get("kitem")
        if kitem:
            for section in self.get("sections"):
                if not "kitem" in section:
                    section["kitem"] = kitem
        return self

    def __str__(self) -> str:
        """Pretty print the model fields"""
        return print_model(self, "custom_properties")

    def __repr__(self) -> str:
        """Pretty print the model fields"""
        return str(self)

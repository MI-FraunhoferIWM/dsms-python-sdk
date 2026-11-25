"""Custom property entries are validated against the k-type's form."""

import pytest
import responses

from dsms.knowledge.kitem import KItem
from dsms.knowledge.ktype import KType
from dsms.knowledge.webform import Entry

# A form as the backend stores it in `KType.custom_properties` (camelCase).
FORM = {
    "sections": [
        {
            "id": "section-1",
            "name": "Material",
            "inputs": [
                {
                    "id": "color",
                    "label": "Color",
                    "widget": "Select",
                    "selectOptions": [{"key": "red", "label": "red"}],
                },
                {
                    "id": "size",
                    "label": "Size",
                    "widget": "Number",
                    "value": 3,
                },
                {"id": "homepage", "label": "Homepage", "widget": "URL"},
                {"id": "rating", "label": "Rating", "widget": "Star rating"},
                {"id": "formula", "label": "Formula", "widget": "LaTeX"},
                {"id": "term", "label": "Term", "widget": "Vocabulary select"},
                {"id": "pairs", "label": "Pairs", "widget": "Key-value pairs"},
                {"id": "rows", "label": "Rows", "widget": "Array group"},
            ],
        }
    ]
}
KTYPE = KType(id="material", name="Material", custom_properties=FORM)


@pytest.fixture
def dsms(custom_address):
    from dsms.core.dsms import DSMS

    with pytest.warns(UserWarning, match="No authentication details"):
        return DSMS(
            host_url=custom_address, ping=False, auto_fetch_ktypes=False
        )


def validate(entry_id, value):
    entry = Entry(id=entry_id, label=entry_id, value=value)
    return KItem.validate_custom_property_entry(entry, KTYPE)


@responses.activate
def test_select_values_are_checked_against_the_spec_options(dsms):
    assert validate("color", "red").value.label == "red"
    with pytest.raises(ValueError, match="not a valid select option"):
        validate("color", "blue")


@responses.activate
def test_the_default_value_comes_from_the_spec(dsms):
    assert validate("size", None).value == 3


@responses.activate
@pytest.mark.parametrize(
    "entry_id, value",
    [
        ("homepage", "https://example.org"),
        ("rating", 4),
        ("formula", "E = mc^2"),
        ("term", {"key": "https://w3id.org/x", "label": "X"}),
        ("term", "https://w3id.org/x"),
        ("pairs", [{"key": "a", "value": "1"}]),
        ("rows", [{"col": 1}, {"col": 2}]),
    ],
)
def test_the_newer_widgets_are_accepted(dsms, entry_id, value):
    assert validate(entry_id, value).value == value


@responses.activate
def test_a_wrong_type_for_a_newer_widget_is_rejected(dsms):
    with pytest.raises(ValueError, match="invalid"):
        validate("homepage", 42)


def test_a_flat_dict_takes_the_unit_from_the_spec():
    from dsms.knowledge.utils import _transform_custom_properties_schema

    form = {
        "sections": [
            {
                "id": "s",
                "name": "Geometry",
                "inputs": [
                    {
                        "id": "length",
                        "label": "Length",
                        "widget": "Number",
                        "measurementUnit": {
                            "label": "Millimetre",
                            "symbol": "mm",
                        },
                    }
                ],
            }
        ]
    }

    result = _transform_custom_properties_schema({"Length": 3}, form)

    entry = result["sections"][0]["entries"][0]
    assert entry["value"] == 3
    assert entry["measurement_unit"]["symbol"] == "mm"

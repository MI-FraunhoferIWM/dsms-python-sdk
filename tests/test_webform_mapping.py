"""Webforms and the RDF mapping generated from them.

knowledge-type-service and knowledge-service rely on this behaviour, see
semantic-dataspace/knowledge-types for the specs it has to handle.
"""

import json
import os

from dsms.knowledge.utils import generate_mapping
from dsms.knowledge.webform import Webform

FIXTURES = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fixtures")

# A form as written in a curated k-type spec: semantics on, but the class is
# declared at the type level (ontology_classes), not as class_mapping.
SPEC_STYLE_FORM = {
    "semantics_enabled": True,
    "sections_enabled": True,
    "sections": [
        {
            "id": "section-material-identity",
            "name": "Material Identity",
            "inputs": [
                {
                    "id": "input-material-name",
                    "label": "Material name",
                    "widget": "Text",
                    "relation_mapping": {
                        "iri": "http://xmlns.com/foaf/0.1/name",
                        "type": "data_property",
                    },
                },
            ],
        }
    ],
}


def test_mapping_of_a_form_with_class_mapping():
    with open(
        os.path.join(FIXTURES, "webform_youngs_modulus.json"), encoding="utf-8"
    ) as file:
        webform = json.load(file)

    mapping = generate_mapping("material", webform)

    assert mapping == {
        "iri": "https://w3id.org/my-vocab/material",
        "suffix": "slug",
        "source": "material[*]",
        "suffix_from_location": True,
        "custom_relations": [
            {
                "object_location": "material_name",
                "relation": "https://w3id.org/steel/ProcessOntology/hasMaterialIdentifier",
                "relation_type": "data_property",
                "object_type": "string",
            },
            {
                "object_location": "youngs_modulus",
                "relation": "https://w3id.org/steel/ProcessOntology/hasModulusOfElasticity_Object",
                "relation_type": "object_property",
                "object_type": {
                    "iri": "https://w3id.org/steel/ProcessOntology/ModulusOfElasticity",
                    "unit": "http://qudt.org/vocab/unit/MegaPA",
                },
            },
            # added because the form has no field labelled "Name"
            {
                "object_location": "Name",
                "relation": "http://www.w3.org/2000/01/rdf-schema#label",
                "relation_type": "annotation_property",
                "object_data_type": "string",
            },
        ],
    }


def test_a_spec_style_form_without_class_mapping_is_valid():
    webform = Webform.model_validate(SPEC_STYLE_FORM)

    assert webform.semantics_enabled
    assert not webform.class_mapping


def test_mapping_without_class_mapping_keeps_the_field_relations():
    """Services fill in the class from the type's ontology classes."""
    form = Webform.model_validate(SPEC_STYLE_FORM).model_dump(by_alias=True)

    mapping = generate_mapping("material", form)

    assert not mapping["iri"]
    assert mapping["custom_relations"][0] == {
        "object_location": "material_name",
        "relation": "http://xmlns.com/foaf/0.1/name",
        "relation_type": "data_property",
        "object_type": "string",
    }

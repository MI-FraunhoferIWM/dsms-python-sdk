"""Pytests for DSMS utilities"""

import pytest
import responses

# @responses.activate
# def test_kitem_list():
#     from dsms.core.dsms import DSMS

#     dsms = DSMS()


# @responses.activate
# def test_create_kitem():

#     from dsms.knowledge.utils import _create_new_kitem

#     from dsms.knowledge.kitem import KItem
#     from dsms.core.dsms import DSMS

#     dsms = DSMS()

#     item = KItem(name="foo", slug="bar", ktype_id=dsms.ktypes.Organization)


#     _create_new_kitem(item)


@responses.activate
def test_kitem_diffs(get_mock_kitem_ids, custom_address):
    from dsms.core.dsms import DSMS
    from dsms.knowledge.kitem import KItem
    from dsms.knowledge.utils import _get_kitems_diffs

    with pytest.warns(UserWarning, match="No authentication details"):
        dsms = DSMS(host_url=custom_address)

    linked_kitem1 = KItem(
        id=get_mock_kitem_ids[1],
        ktype_id=dsms.ktypes.Organization,
        name="foo456",
    )
    linked_kitem2 = KItem(
        id=get_mock_kitem_ids[2],
        ktype_id=dsms.ktypes.Organization,
        name="foo789",
    )
    linked_kitem3 = KItem(
        id=get_mock_kitem_ids[3],
        ktype_id=dsms.ktypes.Organization,
        name="bar123",
    )

    user_group = {"name": "private", "group_id": "private_123"}
    app = {"executable": "foo.exe", "title": "foo"}

    kitem_old = {
        "id": get_mock_kitem_ids[0],
        "name": "foo123",
        "ktype_id": dsms.ktypes.Organization.value,
        "annotations": [
            {
                "iri": "http://example.org/",
                "label": "bar",
                "namespace": "example",
            }
        ],
        "linked_kitems": [
            {
                "id": str(get_mock_kitem_ids[1]),
                "ktype_id": dsms.ktypes.Organization.value,
                "name": "foo456",
            },
            {
                "id": str(get_mock_kitem_ids[2]),
                "ktype_id": dsms.ktypes.Organization.value,
                "name": "foo789",
            },
        ],
        "user_groups": [user_group],
        "kitem_apps": [
            {
                "id": get_mock_kitem_ids[0],
                "kitem_app_id": 17,
                "executable": "bar.exe",
                "title": "bar",
                "description": None,
                "tags": None,
                "additional_properties": None,
            }
        ],
    }

    kitem_new = KItem(
        id=get_mock_kitem_ids[0],
        name="foo123",
        ktype_id=dsms.ktypes.Organization,
        annotations=[
            {
                "iri": "http://example.org/",
                "label": "foo",
                "namespace": "example",
            }
        ],
        linked_kitems=[linked_kitem3],
        user_groups=[user_group],
        kitem_apps=[app],
    )

    expected = {
        "kitems_to_link": [
            {"id": str(obj.id)} for obj in kitem_new.linked_kitems
        ],
        "annotations_to_link": [
            {
                "iri": "http://example.org/",
                "label": "foo",
                "namespace": "example",
            }
        ],
        "user_groups_to_add": [],
        "kitem_apps_to_update": [
            {
                "executable": "foo.exe",
                "title": "foo",
                "description": None,
                "tags": None,
                "additional_properties": None,
            }
        ],
        "kitems_to_unlink": [
            {"id": str(linked.id)} for linked in [linked_kitem1, linked_kitem2]
        ],
        "annotations_to_unlink": [
            {
                "iri": "http://example.org/",
                "label": "bar",
                "namespace": "example",
            }
        ],
        "user_groups_to_remove": [],
        "kitem_apps_to_remove": [
            {
                "executable": "bar.exe",
                "title": "bar",
                "description": None,
                "tags": None,
                "additional_properties": None,
            }
        ],
    }
    diffs = _get_kitems_diffs(kitem_old, kitem_new)

    for key, value in diffs.items():
        assert value == expected.pop(key)
    assert len(expected) == 0


@responses.activate
def test_unit_conversion(custom_address):
    """Test unit conversion test"""
    from dsms import DSMS
    from dsms.knowledge.semantics.units import get_conversion_factor

    with pytest.warns(UserWarning, match="No authentication details"):
        DSMS(host_url=custom_address)

    assert get_conversion_factor("mm", "m", decimals=3) == 0.001

    assert get_conversion_factor("km", "in", decimals=1) == 39370.1

    assert get_conversion_factor("GPa", "MPa") == 1000

    assert (
        get_conversion_factor(
            "http://qudt.org/vocab/unit/M",
            "http://qudt.org/vocab/unit/IN",
            decimals=1,
        )
        == 39.4
    )

    with pytest.raises(ValueError, match="Unit "):
        get_conversion_factor("kPa", "cm")

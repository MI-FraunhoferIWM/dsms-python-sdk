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
                "iri": "https://example.org/has_part",
                "label": "has part",
                "is_incoming": False,
                "kitem": {
                    "id": str(get_mock_kitem_ids[1]),
                    "ktype_id": dsms.ktypes.Organization.value,
                    "name": "foo456",
                },
            },
            {
                "iri": "https://example.org/has_part",
                "label": "has part",
                "is_incoming": False,
                "kitem": {
                    "id": str(get_mock_kitem_ids[2]),
                    "ktype_id": dsms.ktypes.Organization.value,
                    "name": "foo789",
                },
            },
        ],
        "apps": [
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
    with pytest.warns(
        UserWarning, match="Found a <class 'dsms.knowledge.kitem.KItem'>"
    ):
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
            apps=[app],
        )

    expected = {
        "kitems_to_link": [
            {
                "id": str(obj.kitem.id),
                "label": obj.label,
                "iri": obj.iri,
                "is_incoming": False,
            }
            for obj in kitem_new.linked_kitems
        ],
        "annotations_to_link": [
            {
                "iri": "http://example.org/",
                "label": "foo",
                "namespace": "example",
            }
        ],
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
            {
                "id": str(linked.id),
                "label": "has part",
                "iri": "https://example.org/has_part",
                "is_incoming": False,
            }
            for linked in [linked_kitem1, linked_kitem2]
        ],
        "annotations_to_unlink": [
            {
                "iri": "http://example.org/",
                "label": "bar",
                "namespace": "example",
            }
        ],
        "kitem_apps_to_remove": [
            {
                "executable": "bar.exe",
                "title": "bar",
                "description": None,
                "tags": None,
                "additional_properties": None,
            }
        ],
        "contexts_to_add_in": [],
        "contexts_to_remove_from": [],
    }

    diffs = _get_kitems_diffs(kitem_old, kitem_new)

    for key, value in diffs.items():
        assert value == expected.pop(key)
    assert len(expected) == 0


@responses.activate
def test_kitem_diffs_access_properties(get_mock_kitem_ids, custom_address):
    """visibility must be promoted to a top-level key; must not appear inside access_properties."""
    import pytest

    from dsms.core.dsms import DSMS
    from dsms.knowledge.kitem import KItem
    from dsms.knowledge.properties.access import KItemAccessProperties, Role
    from dsms.knowledge.utils import _get_kitems_diffs

    with pytest.warns(UserWarning, match="No authentication details"):
        dsms = DSMS(host_url=custom_address)

    user_id = "abc-123"

    kitem_old = {
        "id": get_mock_kitem_ids[0],
        "name": "foo",
        "ktype_id": dsms.ktypes.Organization.value,
        "annotations": [],
        "linked_kitems": [],
        "apps": [],
        "access_properties": {
            "visibility": "restricted",
            "grants": [{"id": user_id, "type": "user", "role": "owner"}],
        },
    }

    kitem_new = KItem(
        id=get_mock_kitem_ids[0],
        name="foo-item",
        slug="foo-item",
        ktype_id=dsms.ktypes.Organization,
        access_properties=KItemAccessProperties(
            visibility="internal",
            grants=[{"id": user_id, "type": "user", "role": Role.OWNER}],
        ),
    )

    diffs = _get_kitems_diffs(kitem_old, kitem_new)

    assert diffs["visibility"] == "internal"
    assert "visibility" not in diffs["access_properties"]


@responses.activate
def test_kitem_diffs_visibility_unchanged(get_mock_kitem_ids, custom_address):
    """When visibility hasn't changed it should not appear in the diff."""
    import pytest

    from dsms.core.dsms import DSMS
    from dsms.knowledge.kitem import KItem
    from dsms.knowledge.properties.access import KItemAccessProperties, Role
    from dsms.knowledge.utils import _get_kitems_diffs

    with pytest.warns(UserWarning, match="No authentication details"):
        dsms = DSMS(host_url=custom_address)

    user_id = "abc-123"
    other_user_id = "def-456"

    kitem_old = {
        "id": get_mock_kitem_ids[0],
        "name": "foo",
        "ktype_id": dsms.ktypes.Organization.value,
        "annotations": [],
        "linked_kitems": [],
        "apps": [],
        "access_properties": {
            "visibility": "internal",
            "grants": [{"id": user_id, "type": "user", "role": "owner"}],
        },
    }

    kitem_new = KItem(
        id=get_mock_kitem_ids[0],
        name="foo-item",
        slug="foo-item",
        ktype_id=dsms.ktypes.Organization,
        access_properties=KItemAccessProperties(
            visibility="internal",
            grants=[
                {"id": user_id, "type": "user", "role": Role.OWNER},
                {"id": other_user_id, "type": "user", "role": Role.MEMBER},
            ],
        ),
    )

    diffs = _get_kitems_diffs(kitem_old, kitem_new)

    assert "visibility" not in diffs
    assert "visibility" not in diffs["access_properties"]


@responses.activate
def test_kitem_diffs_visibility_only_keeps_grants(
    get_mock_kitem_ids, custom_address
):
    """A fresh access object with only a visibility must not send a grant list.

    The backend replaces grants whenever they are sent and rejects an empty
    list (at least one owner is required), so sending ``grants: []`` would
    turn a visibility change into an error.
    """
    import pytest

    from dsms.core.dsms import DSMS
    from dsms.knowledge.kitem import KItem
    from dsms.knowledge.properties.access import KItemAccessProperties
    from dsms.knowledge.utils import _get_kitems_diffs

    with pytest.warns(UserWarning, match="No authentication details"):
        dsms = DSMS(host_url=custom_address)

    kitem_old = {
        "id": get_mock_kitem_ids[0],
        "name": "foo",
        "ktype_id": dsms.ktypes.Organization.value,
        "annotations": [],
        "linked_kitems": [],
        "apps": [],
        "access_properties": {
            "visibility": "restricted",
            "grants": [{"id": "abc-123", "type": "user", "role": "owner"}],
        },
    }

    kitem_new = KItem(
        id=get_mock_kitem_ids[0],
        name="foo-item",
        slug="foo-item",
        ktype_id=dsms.ktypes.Organization,
        access_properties=KItemAccessProperties(visibility="public"),
    )

    diffs = _get_kitems_diffs(kitem_old, kitem_new)

    assert diffs["visibility"] == "public"
    assert "grants" not in diffs.get("access_properties", {})


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

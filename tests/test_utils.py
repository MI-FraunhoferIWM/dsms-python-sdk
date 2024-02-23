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

    annotation = {
        "iri": "http://example.org/",
        "name": "foo",
        "namespace": "example",
    }
    annotation2 = {
        "iri": "http://example.org/",
        "name": "bar",
        "namespace": "example",
    }
    user_group = {"name": "private", "group_id": "private_123"}
    app = {"executable": "foo.exe"}
    app2 = {"executable": "bar.exe"}

    kitem_old = KItem(
        id=get_mock_kitem_ids[0],
        name="foo123",
        ktype_id=dsms.ktypes.Organization,
        annotations=[annotation2],
        linked_kitems=[linked_kitem1, linked_kitem2],
        user_groups=[user_group],
        kitem_apps=[app2],
    )

    kitem_new = KItem(
        id=get_mock_kitem_ids[0],
        name="foo123",
        ktype_id=dsms.ktypes.Organization,
        annotations=[annotation],
        linked_kitems=[linked_kitem3],
        user_groups=[user_group],
        kitem_apps=[app],
    )

    expected = {
        "kitems_to_link": [
            obj.model_dump() for obj in kitem_new.linked_kitems
        ],
        "annotations_to_link": [
            obj.model_dump() for obj in kitem_new.annotations
        ],
        "user_groups_to_add": [],
        "kitem_apps_to_update": [
            obj.model_dump() for obj in kitem_new.kitem_apps
        ],
        "kitems_to_unlink": [
            obj.model_dump() for obj in kitem_old.linked_kitems
        ],
        "annotations_to_unlink": [
            obj.model_dump() for obj in kitem_old.annotations
        ],
        "user_groups_to_remove": [],
        "kitem_apps_to_remove": [
            obj.model_dump() for obj in kitem_old.kitem_apps
        ],
    }
    diffs = _get_kitems_diffs(kitem_old, kitem_new)
    assert sorted(diffs) == sorted(expected)

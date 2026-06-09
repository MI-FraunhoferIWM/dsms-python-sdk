"""Tests for groups models, public group constants, and DSMS user/group API."""

from urllib.parse import urljoin

import pytest
import responses as responses_lib

from dsms.knowledge.groups.models import (
    BaseGroup,
    Group,
    GroupList,
    User,
    UserList,
)
from dsms.knowledge.groups.public import (
    INTERNAL_GROUP,
    PUBLIC_GROUP,
)

# ---------------------------------------------------------------------------
# Group model
# ---------------------------------------------------------------------------


def test_group_basic():
    g = Group(id="grp-1", name="Engineering")
    assert g.id == "grp-1"
    assert g.name == "Engineering"
    assert g.subgroups is None


def test_group_with_subgroups():
    child = Group(id="grp-child", name="Backend")
    parent = Group(id="grp-parent", name="Engineering", subgroups=[child])
    assert len(parent.subgroups) == 1
    assert parent.subgroups[0].id == "grp-child"


def test_group_deeply_nested():
    leaf = Group(id="leaf", name="Leaf")
    mid = Group(id="mid", name="Mid", subgroups=[leaf])
    root = Group(id="root", name="Root", subgroups=[mid])
    assert root.subgroups[0].subgroups[0].id == "leaf"


# ---------------------------------------------------------------------------
# GroupList
# ---------------------------------------------------------------------------


def test_grouplist_flat_no_subgroups():
    gl = GroupList([Group(id="a", name="A"), Group(id="b", name="B")])
    flat = gl.flat
    assert {g.id for g in flat} == {"a", "b"}


def test_grouplist_flat_includes_subgroups():
    child = Group(id="child", name="Child")
    parent = Group(id="parent", name="Parent", subgroups=[child])
    gl = GroupList([parent])
    flat = gl.flat
    assert {g.id for g in flat} == {"parent", "child"}


def test_grouplist_flat_deep():
    leaf = Group(id="leaf", name="Leaf")
    mid = Group(id="mid", name="Mid", subgroups=[leaf])
    root = Group(id="root", name="Root", subgroups=[mid])
    gl = GroupList([root])
    assert {g.id for g in gl.flat} == {"root", "mid", "leaf"}


def test_grouplist_flat_returns_basegroups():
    """flat must return BaseGroup instances (no subgroups field)."""
    child = Group(id="child", name="Child")
    parent = Group(id="parent", name="Parent", subgroups=[child])
    gl = GroupList([parent])
    for item in gl.flat:
        assert isinstance(item, BaseGroup)


def test_grouplist_by_id():
    gl = GroupList([Group(id="a", name="Alpha"), Group(id="b", name="Beta")])
    by_id = gl.by_id
    assert by_id["a"].name == "Alpha"
    assert by_id["b"].name == "Beta"


def test_grouplist_by_id_includes_subgroups():
    child = Group(id="child", name="Child")
    parent = Group(id="parent", name="Parent", subgroups=[child])
    gl = GroupList([parent])
    assert "child" in gl.by_id
    assert "parent" in gl.by_id


def test_grouplist_by_name():
    gl = GroupList([Group(id="a", name="Alpha"), Group(id="b", name="Beta")])
    assert gl.by_name["Alpha"].id == "a"
    assert gl.by_name["Beta"].id == "b"


# ---------------------------------------------------------------------------
# User model
# ---------------------------------------------------------------------------


def test_user_basic():
    u = User(id="u-1", username="alice")
    assert u.id == "u-1"
    assert u.username == "alice"
    assert u.user_groups is None


def test_user_with_groups():
    g = BaseGroup(id="g-1", name="Engineering")
    u = User(id="u-1", username="alice", user_groups=[g])
    assert len(u.user_groups) == 1
    assert u.user_groups[0].id == "g-1"


# ---------------------------------------------------------------------------
# UserList
# ---------------------------------------------------------------------------


def test_userlist_by_id():
    ul = UserList(
        [User(id="u1", username="alice"), User(id="u2", username="bob")]
    )
    assert ul.by_id["u1"].username == "alice"
    assert ul.by_id["u2"].username == "bob"


def test_userlist_by_username():
    ul = UserList(
        [User(id="u1", username="alice"), User(id="u2", username="bob")]
    )
    assert ul.by_username["alice"].id == "u1"


def test_userlist_by_name_is_alias_for_by_username():
    ul = UserList([User(id="u1", username="alice")])
    assert ul.by_name == ul.by_username
    assert ul.by_name["alice"].id == "u1"


def test_userlist_getitem_by_id():
    ul = UserList([User(id="u1", username="alice")])
    assert ul["u1"].username == "alice"


def test_userlist_getitem_missing_raises():
    ul = UserList([User(id="u1", username="alice")])
    with pytest.raises(KeyError):
        _ = ul["nonexistent"]


# ---------------------------------------------------------------------------
# Public group constants
# ---------------------------------------------------------------------------


def test_internal_group_id():
    """INTERNAL_GROUP.id must match the BaseConfiguration default."""
    assert INTERNAL_GROUP.id == "dsms:internal"


def test_public_group_id():
    assert PUBLIC_GROUP.id == "dsms:public"


def test_internal_group_has_name():
    assert INTERNAL_GROUP.name != ""


def test_public_group_has_name():
    assert PUBLIC_GROUP.name != ""


def test_refresh_public_groups_uses_custom_config():
    """refresh_public_groups(config) must update the module-level constants."""
    from dsms.core.configuration import BaseConfiguration
    from dsms.knowledge.groups import public as pub

    original_id = pub.INTERNAL_GROUP.id

    custom_cfg = BaseConfiguration(
        id_internal="custom:internal",
        id_public="custom:external",
        label_internal="Custom Internal",
        label_public="Custom External",
    )
    pub.refresh_public_groups(custom_cfg)

    assert pub.INTERNAL_GROUP.id == "custom:internal"
    assert pub.PUBLIC_GROUP.id == "custom:external"
    assert pub.INTERNAL_GROUP.name == "Custom Internal"

    # Restore defaults so other tests are not affected
    pub.refresh_public_groups()
    assert pub.INTERNAL_GROUP.id == original_id


def test_refresh_public_groups_without_arg_restores_defaults(
    reset_dsms_session,
):
    """refresh_public_groups() with no argument should use env/defaults."""
    from dsms.knowledge.groups import public as pub

    pub.refresh_public_groups()
    assert pub.INTERNAL_GROUP.id == "dsms:internal"
    assert pub.PUBLIC_GROUP.id == "dsms:public"


# ---------------------------------------------------------------------------
# DSMS.user_groups, DSMS.users, DSMS.get_user — caching and HTTP behaviour
# ---------------------------------------------------------------------------

MOCK_GROUPS = [
    {"id": "grp-1", "name": "Engineering", "subgroups": []},
    {
        "id": "grp-2",
        "name": "Research",
        "subgroups": [{"id": "grp-3", "name": "ML", "subgroups": []}],
    },
]

MOCK_USERS = [
    {"id": "u-1", "username": "alice", "user_groups": []},
    {"id": "u-2", "username": "bob", "user_groups": []},
]

MOCK_SINGLE_USER = {"id": "u-1", "username": "alice", "user_groups": []}


@responses_lib.activate
def test_user_groups_returns_grouplist(custom_address):
    responses_lib.add(
        responses_lib.GET,
        urljoin(custom_address, "api/users/groups"),
        json=MOCK_GROUPS,
        status=200,
    )

    with pytest.warns(UserWarning):
        from dsms.core.dsms import DSMS

        dsms = DSMS(
            host_url=custom_address,
            ping_backend=False,
            auto_fetch_ktypes=False,
        )

    result = dsms.user_groups
    assert isinstance(result, GroupList)
    assert len(result) == 2
    assert result.by_id["grp-1"].name == "Engineering"


@responses_lib.activate
def test_user_groups_is_cached(custom_address):
    """Second access to user_groups must not make a second HTTP request."""
    responses_lib.add(
        responses_lib.GET,
        urljoin(custom_address, "api/users/groups"),
        json=MOCK_GROUPS,
        status=200,
    )

    with pytest.warns(UserWarning):
        from dsms.core.dsms import DSMS

        dsms = DSMS(
            host_url=custom_address,
            ping_backend=False,
            auto_fetch_ktypes=False,
        )

    _ = dsms.user_groups
    _ = dsms.user_groups

    group_calls = [
        c for c in responses_lib.calls if "api/users/groups" in c.request.url
    ]
    assert len(group_calls) == 1


@responses_lib.activate
def test_refresh_user_groups_re_fetches(custom_address):
    """refresh_user_groups() must make a new HTTP request and update the cache."""
    responses_lib.add(
        responses_lib.GET,
        urljoin(custom_address, "api/users/groups"),
        json=MOCK_GROUPS,
        status=200,
    )
    responses_lib.add(
        responses_lib.GET,
        urljoin(custom_address, "api/users/groups"),
        json=[{"id": "grp-new", "name": "New Group", "subgroups": []}],
        status=200,
    )

    with pytest.warns(UserWarning):
        from dsms.core.dsms import DSMS

        dsms = DSMS(
            host_url=custom_address,
            ping_backend=False,
            auto_fetch_ktypes=False,
        )

    _ = dsms.user_groups
    dsms.refresh_user_groups()

    assert dsms.user_groups.by_id["grp-new"].name == "New Group"
    group_calls = [
        c for c in responses_lib.calls if "api/users/groups" in c.request.url
    ]
    assert len(group_calls) == 2


@responses_lib.activate
def test_users_is_cached(custom_address):
    """Second access to users must not make a second HTTP request."""
    responses_lib.add(
        responses_lib.GET,
        urljoin(custom_address, "api/users/"),
        json=MOCK_USERS,
        status=200,
    )

    with pytest.warns(UserWarning):
        from dsms.core.dsms import DSMS

        dsms = DSMS(
            host_url=custom_address,
            ping_backend=False,
            auto_fetch_ktypes=False,
        )

    _ = dsms.users
    _ = dsms.users

    user_calls = [
        c for c in responses_lib.calls if "api/users/" in c.request.url
    ]
    assert len(user_calls) == 1


@responses_lib.activate
def test_refresh_users_re_fetches(custom_address):
    responses_lib.add(
        responses_lib.GET,
        urljoin(custom_address, "api/users/"),
        json=MOCK_USERS,
        status=200,
    )
    responses_lib.add(
        responses_lib.GET,
        urljoin(custom_address, "api/users/"),
        json=[{"id": "u-3", "username": "carol", "user_groups": []}],
        status=200,
    )

    with pytest.warns(UserWarning):
        from dsms.core.dsms import DSMS

        dsms = DSMS(
            host_url=custom_address,
            ping_backend=False,
            auto_fetch_ktypes=False,
        )

    _ = dsms.users
    dsms.refresh_users()

    assert dsms.users["u-3"].username == "carol"


@responses_lib.activate
def test_get_user_returns_user_object(custom_address):
    """DSMS.get_user(id) must return a typed User, not a raw dict."""
    responses_lib.add(
        responses_lib.GET,
        urljoin(custom_address, "api/users/u-1"),
        json=MOCK_SINGLE_USER,
        status=200,
    )

    with pytest.warns(UserWarning):
        from dsms.core.dsms import DSMS

        dsms = DSMS(
            host_url=custom_address,
            ping_backend=False,
            auto_fetch_ktypes=False,
        )

    user = dsms.get_user("u-1")

    assert isinstance(user, User)
    assert user.id == "u-1"
    assert user.username == "alice"


@responses_lib.activate
def test_get_user_raises_on_missing(custom_address):
    responses_lib.add(
        responses_lib.GET,
        urljoin(custom_address, "api/users/nonexistent"),
        json={"detail": "Not found"},
        status=404,
    )

    with pytest.warns(UserWarning):
        from dsms.core.dsms import DSMS

        dsms = DSMS(
            host_url=custom_address,
            ping_backend=False,
            auto_fetch_ktypes=False,
        )

    with pytest.raises(ValueError, match="nonexistent"):
        dsms.get_user("nonexistent")


# ---------------------------------------------------------------------------
# Group CRUD — get_group_members
# ---------------------------------------------------------------------------

MOCK_MEMBERS = [
    {
        "id": "u-1",
        "username": "alice",
        "firstName": "Alice",
        "lastName": "A",
        "email": "alice@example.com",
    },
    {
        "id": "u-2",
        "username": "bob",
        "firstName": "Bob",
        "lastName": "B",
        "email": "bob@example.com",
    },
]


@responses_lib.activate
def test_get_group_members_returns_user_list(custom_address):
    responses_lib.add(
        responses_lib.GET,
        urljoin(custom_address, "api/users/groups/grp-1/members"),
        json=MOCK_MEMBERS,
        status=200,
    )

    with pytest.warns(UserWarning):
        from dsms.core.dsms import DSMS

        dsms = DSMS(
            host_url=custom_address,
            ping_backend=False,
            auto_fetch_ktypes=False,
        )

    members = dsms.get_group_members("grp-1")
    assert len(members) == 2
    assert all(isinstance(m, User) for m in members)
    assert members[0].username == "alice"
    assert members[1].username == "bob"


@responses_lib.activate
def test_get_group_members_raises_on_error(custom_address):
    responses_lib.add(
        responses_lib.GET,
        urljoin(custom_address, "api/users/groups/bad-id/members"),
        json={"detail": "Not found"},
        status=404,
    )

    with pytest.warns(UserWarning):
        from dsms.core.dsms import DSMS

        dsms = DSMS(
            host_url=custom_address,
            ping_backend=False,
            auto_fetch_ktypes=False,
        )

    with pytest.raises(ConnectionError, match="bad-id"):
        dsms.get_group_members("bad-id")


# ---------------------------------------------------------------------------
# Group CRUD — create_group
# ---------------------------------------------------------------------------

MOCK_NEW_GROUP = {"id": "grp-new", "name": "New Group"}
MOCK_NEW_SUBGROUP = {"id": "grp-sub", "name": "Sub Group"}


@responses_lib.activate
def test_create_group_top_level(custom_address):
    responses_lib.add(
        responses_lib.POST,
        urljoin(custom_address, "api/users/groups"),
        json=MOCK_NEW_GROUP,
        status=201,
    )
    responses_lib.add(
        responses_lib.GET,
        urljoin(custom_address, "api/users/groups"),
        json=[MOCK_NEW_GROUP],
        status=200,
    )

    with pytest.warns(UserWarning):
        from dsms.core.dsms import DSMS

        dsms = DSMS(
            host_url=custom_address,
            ping_backend=False,
            auto_fetch_ktypes=False,
        )

    group = dsms.create_group("New Group")
    assert isinstance(group, Group)
    assert group.id == "grp-new"
    assert group.name == "New Group"
    # cache must be invalidated
    assert dsms._user_groups is None


@responses_lib.activate
def test_create_group_as_subgroup(custom_address):
    responses_lib.add(
        responses_lib.POST,
        urljoin(custom_address, "api/users/groups/grp-1/subgroups"),
        json=MOCK_NEW_SUBGROUP,
        status=201,
    )

    with pytest.warns(UserWarning):
        from dsms.core.dsms import DSMS

        dsms = DSMS(
            host_url=custom_address,
            ping_backend=False,
            auto_fetch_ktypes=False,
        )

    group = dsms.create_group("Sub Group", parent_id="grp-1")
    assert isinstance(group, Group)
    assert group.id == "grp-sub"

    call = responses_lib.calls[0]
    assert "grp-1/subgroups" in call.request.url


@responses_lib.activate
def test_create_group_raises_on_error(custom_address):
    responses_lib.add(
        responses_lib.POST,
        urljoin(custom_address, "api/users/groups"),
        json={"detail": "Bad request"},
        status=400,
    )

    with pytest.warns(UserWarning):
        from dsms.core.dsms import DSMS

        dsms = DSMS(
            host_url=custom_address,
            ping_backend=False,
            auto_fetch_ktypes=False,
        )

    with pytest.raises(ValueError, match="Failed to create group"):
        dsms.create_group("Bad")


# ---------------------------------------------------------------------------
# Group CRUD — update_group
# ---------------------------------------------------------------------------


@responses_lib.activate
def test_update_group_name(custom_address):
    responses_lib.add(
        responses_lib.PUT,
        urljoin(custom_address, "api/users/groups/grp-1"),
        json={"id": "grp-1", "name": "Renamed"},
        status=200,
    )

    with pytest.warns(UserWarning):
        from dsms.core.dsms import DSMS

        dsms = DSMS(
            host_url=custom_address,
            ping_backend=False,
            auto_fetch_ktypes=False,
        )

    updated = dsms.update_group("grp-1", name="Renamed")
    assert isinstance(updated, Group)
    assert updated.name == "Renamed"
    assert dsms._user_groups is None


@responses_lib.activate
def test_update_group_raises_when_nothing_provided(custom_address):
    with pytest.warns(UserWarning):
        from dsms.core.dsms import DSMS

        dsms = DSMS(
            host_url=custom_address,
            ping_backend=False,
            auto_fetch_ktypes=False,
        )

    with pytest.raises(ValueError, match="At least one"):
        dsms.update_group("grp-1")


# ---------------------------------------------------------------------------
# Group CRUD — delete_group
# ---------------------------------------------------------------------------


@responses_lib.activate
def test_delete_group(custom_address):
    responses_lib.add(
        responses_lib.DELETE,
        urljoin(custom_address, "api/users/groups/grp-1"),
        status=204,
    )

    with pytest.warns(UserWarning):
        from dsms.core.dsms import DSMS

        dsms = DSMS(
            host_url=custom_address,
            ping_backend=False,
            auto_fetch_ktypes=False,
        )

    dsms.delete_group("grp-1")
    assert dsms._user_groups is None
    assert len(responses_lib.calls) == 1
    assert "groups/grp-1" in responses_lib.calls[0].request.url


@responses_lib.activate
def test_delete_group_raises_on_error(custom_address):
    responses_lib.add(
        responses_lib.DELETE,
        urljoin(custom_address, "api/users/groups/grp-missing"),
        json={"detail": "Not found"},
        status=404,
    )

    with pytest.warns(UserWarning):
        from dsms.core.dsms import DSMS

        dsms = DSMS(
            host_url=custom_address,
            ping_backend=False,
            auto_fetch_ktypes=False,
        )

    with pytest.raises(ValueError, match="Failed to delete"):
        dsms.delete_group("grp-missing")


# ---------------------------------------------------------------------------
# Group CRUD — add_group_member / remove_group_member
# ---------------------------------------------------------------------------


@responses_lib.activate
def test_add_group_member(custom_address):
    responses_lib.add(
        responses_lib.POST,
        urljoin(custom_address, "api/users/groups/grp-1/members"),
        status=204,
    )

    with pytest.warns(UserWarning):
        from dsms.core.dsms import DSMS

        dsms = DSMS(
            host_url=custom_address,
            ping_backend=False,
            auto_fetch_ktypes=False,
        )

    dsms.add_group_member("grp-1", "u-1")
    call = responses_lib.calls[0]
    assert "groups/grp-1/members" in call.request.url
    import json as _json

    body = _json.loads(call.request.body)
    assert body["user_id"] == "u-1"


@responses_lib.activate
def test_add_group_member_raises_on_error(custom_address):
    responses_lib.add(
        responses_lib.POST,
        urljoin(custom_address, "api/users/groups/grp-1/members"),
        json={"detail": "User not found"},
        status=404,
    )

    with pytest.warns(UserWarning):
        from dsms.core.dsms import DSMS

        dsms = DSMS(
            host_url=custom_address,
            ping_backend=False,
            auto_fetch_ktypes=False,
        )

    with pytest.raises(ValueError, match="Failed to add user"):
        dsms.add_group_member("grp-1", "bad-user")


@responses_lib.activate
def test_remove_group_member(custom_address):
    responses_lib.add(
        responses_lib.DELETE,
        urljoin(custom_address, "api/users/groups/grp-1/members/u-1"),
        status=204,
    )

    with pytest.warns(UserWarning):
        from dsms.core.dsms import DSMS

        dsms = DSMS(
            host_url=custom_address,
            ping_backend=False,
            auto_fetch_ktypes=False,
        )

    dsms.remove_group_member("grp-1", "u-1")
    call = responses_lib.calls[0]
    assert "groups/grp-1/members/u-1" in call.request.url


@responses_lib.activate
def test_remove_group_member_raises_on_error(custom_address):
    responses_lib.add(
        responses_lib.DELETE,
        urljoin(custom_address, "api/users/groups/grp-1/members/u-bad"),
        json={"detail": "User not found"},
        status=404,
    )

    with pytest.warns(UserWarning):
        from dsms.core.dsms import DSMS

        dsms = DSMS(
            host_url=custom_address,
            ping_backend=False,
            auto_fetch_ktypes=False,
        )

    with pytest.raises(ValueError, match="Failed to remove user"):
        dsms.remove_group_member("grp-1", "u-bad")


# ---------------------------------------------------------------------------
# Group-in-group: get_group_subgroups / add_group_to_group / remove_group_from_group
# ---------------------------------------------------------------------------

MOCK_SUBGROUPS = [
    {"id": "grp-child-1", "name": "Child A"},
    {"id": "grp-child-2", "name": "Child B"},
]


@responses_lib.activate
def test_get_group_subgroups_returns_grouplist(custom_address):
    responses_lib.add(
        responses_lib.GET,
        urljoin(custom_address, "api/users/groups/grp-1/subgroups"),
        json=MOCK_SUBGROUPS,
        status=200,
    )

    with pytest.warns(UserWarning):
        from dsms.core.dsms import DSMS

        dsms = DSMS(
            host_url=custom_address,
            ping_backend=False,
            auto_fetch_ktypes=False,
        )

    subs = dsms.get_group_subgroups("grp-1")
    assert isinstance(subs, GroupList)
    assert len(subs) == 2
    assert subs.by_id["grp-child-1"].name == "Child A"
    assert subs.by_id["grp-child-2"].name == "Child B"


@responses_lib.activate
def test_get_group_subgroups_raises_on_error(custom_address):
    responses_lib.add(
        responses_lib.GET,
        urljoin(custom_address, "api/users/groups/bad-id/subgroups"),
        json={"detail": "Not found"},
        status=404,
    )

    with pytest.warns(UserWarning):
        from dsms.core.dsms import DSMS

        dsms = DSMS(
            host_url=custom_address,
            ping_backend=False,
            auto_fetch_ktypes=False,
        )

    with pytest.raises(ConnectionError, match="bad-id"):
        dsms.get_group_subgroups("bad-id")


@responses_lib.activate
def test_add_group_to_group(custom_address):
    responses_lib.add(
        responses_lib.POST,
        urljoin(
            custom_address, "api/users/groups/grp-parent/subgroups/grp-child"
        ),
        status=204,
    )

    with pytest.warns(UserWarning):
        from dsms.core.dsms import DSMS

        dsms = DSMS(
            host_url=custom_address,
            ping_backend=False,
            auto_fetch_ktypes=False,
        )

    dsms.add_group_to_group("grp-parent", "grp-child")

    assert len(responses_lib.calls) == 1
    assert (
        "groups/grp-parent/subgroups/grp-child"
        in responses_lib.calls[0].request.url
    )
    # cache must be invalidated
    assert dsms._user_groups is None


@responses_lib.activate
def test_add_group_to_group_raises_on_error(custom_address):
    responses_lib.add(
        responses_lib.POST,
        urljoin(
            custom_address, "api/users/groups/grp-parent/subgroups/bad-child"
        ),
        json={"detail": "Group not found"},
        status=404,
    )

    with pytest.warns(UserWarning):
        from dsms.core.dsms import DSMS

        dsms = DSMS(
            host_url=custom_address,
            ping_backend=False,
            auto_fetch_ktypes=False,
        )

    with pytest.raises(ValueError, match="bad-child"):
        dsms.add_group_to_group("grp-parent", "bad-child")


@responses_lib.activate
def test_remove_group_from_group(custom_address):
    responses_lib.add(
        responses_lib.DELETE,
        urljoin(
            custom_address, "api/users/groups/grp-parent/subgroups/grp-child"
        ),
        status=204,
    )

    with pytest.warns(UserWarning):
        from dsms.core.dsms import DSMS

        dsms = DSMS(
            host_url=custom_address,
            ping_backend=False,
            auto_fetch_ktypes=False,
        )

    dsms.remove_group_from_group("grp-parent", "grp-child")

    assert len(responses_lib.calls) == 1
    assert (
        "groups/grp-parent/subgroups/grp-child"
        in responses_lib.calls[0].request.url
    )
    assert dsms._user_groups is None


@responses_lib.activate
def test_remove_group_from_group_raises_on_error(custom_address):
    responses_lib.add(
        responses_lib.DELETE,
        urljoin(
            custom_address, "api/users/groups/grp-parent/subgroups/bad-child"
        ),
        json={"detail": "Group not found"},
        status=404,
    )

    with pytest.warns(UserWarning):
        from dsms.core.dsms import DSMS

        dsms = DSMS(
            host_url=custom_address,
            ping_backend=False,
            auto_fetch_ktypes=False,
        )

    with pytest.raises(ValueError, match="bad-child"):
        dsms.remove_group_from_group("grp-parent", "bad-child")


# ---------------------------------------------------------------------------
# GroupListBase removed — flat returns a plain list of BaseGroup
# ---------------------------------------------------------------------------


def test_grouplist_flat_is_plain_list():
    """After removing GroupListBase, .flat must return a plain list."""
    gl = GroupList(
        [Group(id="a", name="A", subgroups=[Group(id="b", name="B")])]
    )
    result = gl.flat
    assert isinstance(result, list)
    assert not type(result).__name__ == "GroupListBase"
    assert all(isinstance(g, BaseGroup) for g in result)

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

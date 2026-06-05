"""Extended tests for access.py — covering gaps identified in post-merge review."""

import pytest

from dsms.knowledge.properties.access import (
    GroupAccessProperty,
    KItemAccessProperties,
    OperationType,
    Role,
    RoleMapping,
    UserAccessProperty,
)


# ---------------------------------------------------------------------------
# Role hierarchy
# ---------------------------------------------------------------------------


def test_role_ordering():
    """Role integer values must be strictly ascending: USER < CONTRIBUTOR < OWNER < ADMIN."""
    assert Role.USER < Role.CONTRIBUTOR < Role.OWNER < Role.ADMIN


def test_role_gte_comparison():
    """>=  on Role values must work correctly for threshold checks."""
    assert Role.OWNER >= Role.CONTRIBUTOR
    assert Role.ADMIN >= Role.OWNER
    assert not (Role.USER >= Role.CONTRIBUTOR)


# ---------------------------------------------------------------------------
# min_access_level / max_access_level return type
# ---------------------------------------------------------------------------


def test_min_access_level_returns_role_instance():
    """min_access_level must return a Role member, not a plain int."""
    result = RoleMapping.min_access_level(OperationType.READ)
    assert isinstance(result, Role)
    assert result is Role.USER


def test_max_access_level_returns_role_instance():
    """max_access_level must return a Role member, not a plain int."""
    result = RoleMapping.max_access_level(OperationType.READ)
    assert isinstance(result, Role)
    assert result is Role.ADMIN


@pytest.mark.parametrize(
    "operation, expected_min",
    [
        (OperationType.READ, Role.USER),
        (OperationType.UPDATE, Role.CONTRIBUTOR),
        (OperationType.DELETE, Role.OWNER),
        (OperationType.MANAGE, Role.OWNER),
    ],
)
def test_min_access_level_correct_role(operation, expected_min):
    assert RoleMapping.min_access_level(operation) is expected_min


@pytest.mark.parametrize(
    "operation",
    [
        OperationType.READ,
        OperationType.UPDATE,
        OperationType.DELETE,
        OperationType.MANAGE,
    ],
)
def test_max_access_level_is_admin(operation):
    """ADMIN always holds the maximum access level for every mapped operation."""
    assert RoleMapping.max_access_level(operation) is Role.ADMIN


# ---------------------------------------------------------------------------
# Unmapped operations raise ValueError
# ---------------------------------------------------------------------------


def test_min_access_level_create_raises():
    """CREATE is not assigned to any role — min_access_level must raise ValueError."""
    with pytest.raises(ValueError, match="create"):
        RoleMapping.min_access_level(OperationType.CREATE)


def test_max_access_level_create_raises():
    """CREATE is not assigned to any role — max_access_level must raise ValueError."""
    with pytest.raises(ValueError, match="create"):
        RoleMapping.max_access_level(OperationType.CREATE)


def test_error_message_lists_valid_operations():
    """The ValueError message must tell the caller which operations are valid."""
    with pytest.raises(ValueError) as exc_info:
        RoleMapping.min_access_level(OperationType.CREATE)
    msg = str(exc_info.value)
    for op in (OperationType.READ, OperationType.UPDATE, OperationType.DELETE, OperationType.MANAGE):
        assert op.value in msg


# ---------------------------------------------------------------------------
# serialize_role_json — correct mode behaviour
# ---------------------------------------------------------------------------


def test_serialize_role_json_mode():
    """Python mode → name string; JSON/wire mode → integer value."""
    prop = UserAccessProperty(user_id="u1", role=Role.OWNER)

    python_dump = prop.model_dump(mode="python")
    assert python_dump["role"] == "OWNER"
    assert isinstance(python_dump["role"], str)

    json_dump = prop.model_dump(mode="json")
    assert json_dump["role"] == Role.OWNER.value
    assert isinstance(json_dump["role"], int)


# ---------------------------------------------------------------------------
# KItemAccessProperties wire format
# ---------------------------------------------------------------------------


def test_model_dump_json_produces_integer_roles():
    """model_dump(mode='json') must produce integer role values for the wire format."""
    props = KItemAccessProperties(
        user_access=[UserAccessProperty(user_id="u1", role=Role.OWNER)],
        group_access=[GroupAccessProperty(group_id="g1", role=Role.USER)],
    )
    payload = props.model_dump(mode="json")

    assert payload["user_access"][0]["role"] == Role.OWNER.value
    assert isinstance(payload["user_access"][0]["role"], int)
    assert payload["group_access"][0]["role"] == Role.USER.value
    assert isinstance(payload["group_access"][0]["role"], int)


def test_model_dump_python_produces_string_roles():
    """model_dump(mode='python') must produce string role names for display."""
    props = KItemAccessProperties(
        user_access=[UserAccessProperty(user_id="u1", role=Role.CONTRIBUTOR)],
        group_access=[],
    )
    payload = props.model_dump(mode="python")
    assert payload["user_access"][0]["role"] == "CONTRIBUTOR"


def test_round_trip_from_backend_dict():
    """A payload as returned by the backend (integer roles) must round-trip correctly."""
    backend_payload = {
        "user_access": [
            {"user_id": "alice", "role": Role.OWNER.value},
            {"user_id": "bob", "role": Role.USER.value},
        ],
        "group_access": [
            {"group_id": "dsms:internally-public", "role": Role.USER.value},
        ],
    }

    props = KItemAccessProperties(**backend_payload)

    assert props.by_user["alice"].role is Role.OWNER
    assert props.by_user["bob"].role is Role.USER
    assert props.by_group["dsms:internally-public"].role is Role.USER

    # Serialise back and verify identity
    re_serialised = props.model_dump(mode="json")
    assert re_serialised["user_access"][0] == {"user_id": "alice", "role": Role.OWNER.value}
    assert re_serialised["group_access"][0] == {
        "group_id": "dsms:internally-public",
        "role": Role.USER.value,
    }


# ---------------------------------------------------------------------------
# user_by_role property (untested in original suite)
# ---------------------------------------------------------------------------


def test_user_by_role():
    """user_by_role must group user IDs by their Role."""
    props = KItemAccessProperties(
        user_access=[
            UserAccessProperty(user_id="alice", role=Role.OWNER),
            UserAccessProperty(user_id="bob", role=Role.USER),
            UserAccessProperty(user_id="carol", role=Role.USER),
        ]
    )
    by_role = props.user_by_role
    assert by_role[Role.OWNER] == ["alice"]
    assert set(by_role[Role.USER]) == {"bob", "carol"}
    assert Role.CONTRIBUTOR not in by_role


def test_user_by_role_empty():
    assert KItemAccessProperties().user_by_role == {}


# ---------------------------------------------------------------------------
# Validator: None inputs become empty lists
# ---------------------------------------------------------------------------


def test_none_user_access_becomes_empty_list():
    props = KItemAccessProperties(user_access=None, group_access=None)
    assert props.user_access == []
    assert props.group_access == []

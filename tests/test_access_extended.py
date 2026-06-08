"""Extended tests for access.py"""

import pytest

from dsms.knowledge.properties.access import (
    AccessGrant,
    KItemAccessProperties,
    OperationType,
    Role,
    RoleMapping,
)

# ---------------------------------------------------------------------------
# Role hierarchy
# ---------------------------------------------------------------------------


def test_role_ordering():
    """Role integer values must be strictly ascending: MEMBER < CONTRIBUTOR < OWNER."""
    assert Role.MEMBER < Role.CONTRIBUTOR < Role.OWNER


def test_role_gte_comparison():
    """>=  on Role values must work correctly for threshold checks."""
    assert Role.OWNER >= Role.CONTRIBUTOR
    assert not (Role.MEMBER >= Role.CONTRIBUTOR)


# ---------------------------------------------------------------------------
# min_access_level / max_access_level return type
# ---------------------------------------------------------------------------


def test_min_access_level_returns_role_instance():
    """min_access_level must return a Role member, not a plain int."""
    result = RoleMapping.min_access_level(OperationType.READ)
    assert isinstance(result, Role)
    assert result is Role.MEMBER


def test_max_access_level_returns_role_instance():
    """max_access_level must return a Role member, not a plain int."""
    result = RoleMapping.max_access_level(OperationType.READ)
    assert isinstance(result, Role)
    assert result is Role.OWNER


@pytest.mark.parametrize(
    "operation, expected_min",
    [
        (OperationType.READ, Role.MEMBER),
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
def test_max_access_level_is_owner(operation):
    """OWNER always holds the maximum access level for every mapped operation."""
    assert RoleMapping.max_access_level(operation) is Role.OWNER


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
    for op in (
        OperationType.READ,
        OperationType.UPDATE,
        OperationType.DELETE,
        OperationType.MANAGE,
    ):
        assert op.value in msg


# ---------------------------------------------------------------------------
# serialize_role_json — correct mode behaviour
# ---------------------------------------------------------------------------


def test_serialize_role_json_mode():
    """Python mode -> uppercase name string; JSON/wire mode -> lowercase name string."""
    grant = AccessGrant(id="u1", type="user", role=Role.OWNER)

    python_dump = grant.model_dump(mode="python")
    assert python_dump["role"] == "OWNER"
    assert isinstance(python_dump["role"], str)

    json_dump = grant.model_dump(mode="json")
    assert json_dump["role"] == "owner"
    assert isinstance(json_dump["role"], str)


# ---------------------------------------------------------------------------
# KItemAccessProperties wire format
# ---------------------------------------------------------------------------


def test_model_dump_json_produces_string_roles():
    """model_dump(mode='json') must produce lowercase string role values for the wire format."""
    props = KItemAccessProperties(
        grants=[
            AccessGrant(id="u1", type="user", role=Role.OWNER),
            AccessGrant(id="g1", type="group", role=Role.MEMBER),
        ]
    )
    payload = props.model_dump(mode="json")

    user_grant = next(g for g in payload["grants"] if g["id"] == "u1")
    group_grant = next(g for g in payload["grants"] if g["id"] == "g1")
    assert user_grant["role"] == "owner"
    assert isinstance(user_grant["role"], str)
    assert group_grant["role"] == "member"
    assert isinstance(group_grant["role"], str)


def test_model_dump_python_produces_string_roles():
    """model_dump(mode='python') must produce string role names for display."""
    props = KItemAccessProperties(
        grants=[AccessGrant(id="u1", type="user", role=Role.CONTRIBUTOR)]
    )
    payload = props.model_dump(mode="python")
    assert payload["grants"][0]["role"] == "CONTRIBUTOR"


def test_round_trip_from_backend_dict():
    """A payload as returned by the backend (string roles) must round-trip correctly."""
    backend_payload = {
        "visibility": "internal",
        "grants": [
            {"id": "alice", "type": "user", "role": "owner"},
            {"id": "bob", "type": "user", "role": "member"},
            {"id": "dsms:internal", "type": "group", "role": "member"},
        ],
    }

    props = KItemAccessProperties(**backend_payload)

    assert props.by_id["alice"].role is Role.OWNER
    assert props.by_id["bob"].role is Role.MEMBER
    assert props.by_id["dsms:internal"].role is Role.MEMBER
    assert props.visibility == "internal"

    re_serialised = props.model_dump(mode="json")
    assert re_serialised["grants"][0] == {
        "id": "alice",
        "type": "user",
        "role": "owner",
    }
    assert re_serialised["grants"][2] == {
        "id": "dsms:internal",
        "type": "group",
        "role": "member",
    }


# ---------------------------------------------------------------------------
# by_role property
# ---------------------------------------------------------------------------


def test_by_role():
    """by_role must group principal IDs by their Role."""
    props = KItemAccessProperties(
        grants=[
            AccessGrant(id="alice", type="user", role=Role.OWNER),
            AccessGrant(id="bob", type="user", role=Role.MEMBER),
            AccessGrant(id="carol", type="user", role=Role.MEMBER),
        ]
    )
    by_role = props.by_role
    assert by_role[Role.OWNER] == ["alice"]
    assert set(by_role[Role.MEMBER]) == {"bob", "carol"}
    assert Role.CONTRIBUTOR not in by_role


def test_by_role_empty():
    assert KItemAccessProperties().by_role == {}


# ---------------------------------------------------------------------------
# Default grants
# ---------------------------------------------------------------------------


def test_empty_grants_default():
    """Default grants must be an empty list."""
    props = KItemAccessProperties()
    assert props.grants == []
    assert props.visibility == "private"

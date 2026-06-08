"""Tests for Access Property Module"""

from typing import List

import pytest
from pydantic import ValidationError

from dsms.knowledge.properties.access import (
    AccessGrant,
    KItemAccessProperties,
    OperationType,
    Role,
    RoleMapping,
)


@pytest.fixture
def sample_user_grants() -> List[AccessGrant]:
    return [
        AccessGrant(id="user1", type="user", role=Role.OWNER),
        AccessGrant(id="user2", type="user", role=Role.MEMBER),
        AccessGrant(id="user3", type="user", role=Role.CONTRIBUTOR),
    ]


@pytest.fixture
def sample_group_grants() -> List[AccessGrant]:
    return [
        AccessGrant(id="group1", type="group", role=Role.OWNER),
        AccessGrant(id="group2", type="group", role=Role.MEMBER),
    ]


@pytest.fixture
def access_properties(
    sample_user_grants, sample_group_grants
) -> KItemAccessProperties:
    return KItemAccessProperties(
        grants=sample_user_grants + sample_group_grants,
    )


def test_access_level_owner():
    """Test access_level property for OWNER role"""
    grant = AccessGrant(id="u1", type="user", role=Role.OWNER)
    expected = [
        OperationType.READ,
        OperationType.UPDATE,
        OperationType.DELETE,
        OperationType.MANAGE,
    ]
    assert grant.access_level == expected
    assert grant.role.value == Role.OWNER.value


def test_minimum_access_level():
    """Test min_access_level method"""
    assert (
        RoleMapping.min_access_level(OperationType.READ) == Role.MEMBER.value
    )
    assert (
        RoleMapping.min_access_level(OperationType.UPDATE)
        == Role.CONTRIBUTOR.value
    )
    assert (
        RoleMapping.min_access_level(OperationType.DELETE) == Role.OWNER.value
    )
    assert (
        RoleMapping.min_access_level(OperationType.MANAGE) == Role.OWNER.value
    )


def test_maximum_access_level():
    """Test max_access_level method"""
    assert RoleMapping.max_access_level(OperationType.READ) == Role.OWNER.value
    assert (
        RoleMapping.max_access_level(OperationType.UPDATE) == Role.OWNER.value
    )
    assert (
        RoleMapping.max_access_level(OperationType.DELETE) == Role.OWNER.value
    )
    assert (
        RoleMapping.max_access_level(OperationType.MANAGE) == Role.OWNER.value
    )


def test_access_level_member():
    """Test access_level property for MEMBER role"""
    grant = AccessGrant(id="u1", type="user", role=Role.MEMBER)
    expected = [OperationType.READ]
    assert grant.access_level == expected
    assert grant.role.value == Role.MEMBER.value


def test_access_level_contributor():
    """Test access_level property for CONTRIBUTOR role"""
    grant = AccessGrant(id="u1", type="user", role=Role.CONTRIBUTOR)
    expected = [OperationType.READ, OperationType.UPDATE]
    assert grant.access_level == expected
    assert grant.role.value == Role.CONTRIBUTOR.value


def test_by_id_users(access_properties):
    """Test by_id property returns correct lookup for user grants"""
    result = access_properties.by_id

    assert "user1" in result
    assert "user2" in result
    assert "user3" in result

    assert result["user1"].role == Role.OWNER
    assert result["user2"].role == Role.MEMBER
    assert result["user3"].role == Role.CONTRIBUTOR
    assert result["user1"].role.value == Role.OWNER.value
    assert result["user2"].role.value == Role.MEMBER.value
    assert result["user3"].role.value == Role.CONTRIBUTOR.value


def test_by_id_groups(access_properties):
    """Test by_id property returns correct lookup for group grants"""
    result = access_properties.by_id

    assert "group1" in result
    assert "group2" in result

    assert result["group1"].role == Role.OWNER
    assert result["group2"].role == Role.MEMBER
    assert result["group1"].role.value == Role.OWNER.value
    assert result["group2"].role.value == Role.MEMBER.value


def test_operation_by_user_principal():
    """Test operation_by_principal for user grants"""
    props = KItemAccessProperties(
        grants=[
            AccessGrant(id="user1", type="user", role=Role.OWNER),
            AccessGrant(id="user2", type="user", role=Role.MEMBER),
            AccessGrant(id="user3", type="user", role=Role.CONTRIBUTOR),
        ]
    )
    result = props.operation_by_principal

    assert set(result[OperationType.READ]) == {"user1", "user2", "user3"}
    assert set(result[OperationType.UPDATE]) == {"user1", "user3"}
    assert result[OperationType.DELETE] == ["user1"]
    assert result[OperationType.MANAGE] == ["user1"]


def test_operation_by_group_principal():
    """Test operation_by_principal for group grants"""
    props = KItemAccessProperties(
        grants=[
            AccessGrant(id="group1", type="group", role=Role.OWNER),
            AccessGrant(id="group2", type="group", role=Role.MEMBER),
        ]
    )
    result = props.operation_by_principal

    assert set(result[OperationType.READ]) == {"group1", "group2"}
    assert result[OperationType.UPDATE] == ["group1"]
    assert result[OperationType.DELETE] == ["group1"]
    assert result[OperationType.MANAGE] == ["group1"]


def test_operation_by_principal_multiple_same_operation():
    """Test operation_by_principal with multiple principals having same operations"""
    props = KItemAccessProperties(
        grants=[
            AccessGrant(id="user1", type="user", role=Role.MEMBER),
            AccessGrant(id="user2", type="user", role=Role.MEMBER),
            AccessGrant(id="user3", type="user", role=Role.CONTRIBUTOR),
        ]
    )
    result = props.operation_by_principal

    assert set(result[OperationType.READ]) == {"user1", "user2", "user3"}
    assert result[OperationType.UPDATE] == ["user3"]


def test_role_parsed_from_int():
    """Test that roles parsed from integer values work correctly"""
    props = KItemAccessProperties(
        grants=[
            AccessGrant(id="user1", type="user", role=1),
            AccessGrant(id="user2", type="user", role=1),
            AccessGrant(id="user3", type="user", role=2),
        ]
    )
    result = props.operation_by_principal

    assert set(result[OperationType.READ]) == {"user1", "user2", "user3"}
    assert result[OperationType.UPDATE] == ["user3"]
    assert props.by_id["user1"].role == Role.MEMBER
    assert props.by_id["user1"].role.value == Role.MEMBER.value


def test_by_role_groups():
    """Test by_role with group grants"""
    props = KItemAccessProperties(
        grants=[
            AccessGrant(id="group1", type="group", role=Role.MEMBER),
            AccessGrant(id="group2", type="group", role=Role.MEMBER),
            AccessGrant(id="group3", type="group", role=Role.OWNER),
        ]
    )
    result = props.operation_by_principal

    assert set(result[OperationType.READ]) == {"group1", "group2", "group3"}
    assert result[OperationType.MANAGE] == ["group3"]
    assert props.by_role[Role.OWNER] == ["group3"]
    assert props.by_role[Role.MEMBER] == ["group1", "group2"]


def test_model_creation_with_defaults():
    """Test model creation with default values"""
    props = KItemAccessProperties()

    assert props.grants == []
    assert props.visibility == "private"
    assert props.by_id == {}
    assert props.by_role == {}
    assert props.operation_by_principal == {}


def test_grant_creation():
    """Test AccessGrant creation and access_level"""
    grant = AccessGrant(id="test_user", type="user", role=Role.CONTRIBUTOR)

    assert grant.id == "test_user"
    assert grant.type == "user"
    assert grant.role == Role.CONTRIBUTOR
    assert grant.access_level == [OperationType.READ, OperationType.UPDATE]


def test_duplicate_user_grants_raises_error():
    """Test that duplicate (id, type) user grants raise ValueError"""
    grants = [
        AccessGrant(id="user1", type="user", role=Role.OWNER),
        AccessGrant(id="user2", type="user", role=Role.MEMBER),
        AccessGrant(
            id="user1", type="user", role=Role.CONTRIBUTOR
        ),  # Duplicate
    ]

    with pytest.raises(ValidationError) as exc_info:
        KItemAccessProperties(grants=grants)

    error_details = exc_info.value.errors()
    assert len(error_details) == 1
    assert error_details[0]["type"] == "value_error"
    assert "Duplicate grant found" in str(error_details[0]["ctx"]["error"])


def test_duplicate_group_grants_raises_error():
    """Test that duplicate (id, type) group grants raise ValueError"""
    grants = [
        AccessGrant(id="group1", type="group", role=Role.OWNER),
        AccessGrant(id="group2", type="group", role=Role.MEMBER),
        AccessGrant(
            id="group1", type="group", role=Role.CONTRIBUTOR
        ),  # Duplicate
    ]

    with pytest.raises(ValidationError) as exc_info:
        KItemAccessProperties(grants=grants)

    error_details = exc_info.value.errors()
    assert len(error_details) == 1
    assert error_details[0]["type"] == "value_error"
    assert "Duplicate grant found" in str(error_details[0]["ctx"]["error"])


def test_same_id_different_type_no_error():
    """Test that the same ID for user and group is not a duplicate"""
    grants = [
        AccessGrant(id="shared-id", type="user", role=Role.OWNER),
        AccessGrant(id="shared-id", type="group", role=Role.MEMBER),
    ]
    props = KItemAccessProperties(grants=grants)
    assert len(props.grants) == 2


def test_case_sensitive_ids():
    """Test that IDs are case sensitive (no duplicates if different case)"""
    grants = [
        AccessGrant(id="User1", type="user", role=Role.OWNER),
        AccessGrant(id="user1", type="user", role=Role.MEMBER),
        AccessGrant(id="USER1", type="user", role=Role.CONTRIBUTOR),
    ]

    props = KItemAccessProperties(grants=grants)

    assert len(props.grants) == 3
    assert props.by_id["User1"].role == Role.OWNER
    assert props.by_id["user1"].role == Role.MEMBER
    assert props.by_id["USER1"].role == Role.CONTRIBUTOR
    assert props.by_role[Role.OWNER] == ["User1"]
    assert props.by_role[Role.MEMBER] == ["user1"]
    assert props.by_role[Role.CONTRIBUTOR] == ["USER1"]


def test_case_sensitive_ids_dict():
    """Test that IDs are case sensitive when passed as dicts"""
    grants = [
        {"id": "User1", "type": "user", "role": 3},
        {"id": "user1", "type": "user", "role": 1},
        {"id": "USER1", "type": "user", "role": 2},
    ]

    props = KItemAccessProperties(grants=grants)

    assert len(props.grants) == 3
    assert props.by_id["User1"].role == Role.OWNER
    assert props.by_id["user1"].role == Role.MEMBER
    assert props.by_id["USER1"].role == Role.CONTRIBUTOR
    assert props.by_role[Role.OWNER] == ["User1"]
    assert props.by_role[Role.MEMBER] == ["user1"]
    assert props.by_role[Role.CONTRIBUTOR] == ["USER1"]

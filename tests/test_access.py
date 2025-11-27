""""Tests for Access Property Module"""

from typing import List

import pytest
from pydantic import ValidationError

from dsms.knowledge.properties.access import (
    BaseAccessProperty,
    GroupAccessProperty,
    KItemAccessProperties,
    OperationType,
    Role,
    UserAccessProperty,
)


@pytest.fixture
def sample_user_access() -> List[UserAccessProperty]:
    """Create sample user access properties"""
    return [
        UserAccessProperty(user_id="user1", role=Role.OWNER),
        UserAccessProperty(user_id="user2", role=Role.USER),
        UserAccessProperty(user_id="user3", role=Role.CONTRIBUTOR),
    ]


@pytest.fixture
def sample_group_access() -> List[GroupAccessProperty]:
    """Create sample group access properties"""
    return [
        GroupAccessProperty(group_id="group1", role=Role.ADMIN),
        GroupAccessProperty(group_id="group2", role=Role.USER),
    ]


@pytest.fixture
def access_properties(
    sample_user_access, sample_group_access
) -> KItemAccessProperties:
    """Create KItemAccessProperties instance with sample data"""
    return KItemAccessProperties(
        user_access=sample_user_access,
        group_access=sample_group_access,
    )


def test_access_level_owner():
    """Test access_level property for OWNER role"""
    prop = BaseAccessProperty(role=Role.OWNER)
    expected = [
        OperationType.READ,
        OperationType.UPDATE,
        OperationType.DELETE,
        OperationType.MANAGE,
    ]
    assert prop.access_level == expected
    assert prop.role.value == Role.OWNER.value


def test_access_level_user():
    """Test access_level property for USER role"""
    prop = BaseAccessProperty(role=Role.USER)
    expected = [OperationType.READ]
    assert prop.access_level == expected
    assert prop.role.value == Role.USER.value


def test_access_level_contributor():
    """Test access_level property for CONTRIBUTOR role"""
    prop = BaseAccessProperty(role=Role.CONTRIBUTOR)
    expected = [OperationType.READ, OperationType.UPDATE]
    assert prop.access_level == expected
    assert prop.role.value == Role.CONTRIBUTOR.value


def test_access_level_admin():
    """Test access_level property for ADMIN role"""
    prop = BaseAccessProperty(role=Role.ADMIN)
    expected = [
        OperationType.READ,
        OperationType.UPDATE,
        OperationType.DELETE,
        OperationType.MANAGE,
    ]
    assert prop.access_level == expected
    assert prop.role.value == Role.ADMIN.value


@pytest.mark.usefixtures("access_properties")
def test_by_user_property(access_properties):
    """Test by_user property returns correct user mapping"""
    result = access_properties.by_user

    assert len(result) == 3
    assert "user1" in result
    assert "user2" in result
    assert "user3" in result

    assert result["user1"].role == Role.OWNER
    assert result["user2"].role == Role.USER
    assert result["user3"].role == Role.CONTRIBUTOR
    assert result["user1"].role.value == Role.OWNER.value
    assert result["user2"].role.value == Role.USER.value
    assert result["user3"].role.value == Role.CONTRIBUTOR.value


@pytest.mark.usefixtures("access_properties")
def test_by_group_property(access_properties):
    """Test by_group property returns correct group mapping"""
    result = access_properties.by_group

    assert len(result) == 2
    assert "group1" in result
    assert "group2" in result

    assert result["group1"].role == Role.ADMIN
    assert result["group2"].role == Role.USER
    assert result["group1"].role.value == Role.ADMIN.value
    assert result["group2"].role.value == Role.USER.value


@pytest.mark.usefixtures("access_properties")
def test_operation_by_user_property(access_properties):
    """Test operation_by_user property returns correct operation mapping"""
    result = access_properties.operation_by_user

    # user1 (OWNER): READ, UPDATE, DELETE, MANAGE
    # user2 (USER): READ
    # user3 (CONTRIBUTOR): READ, UPDATE

    expected_read = ["user1", "user2", "user3"]
    expected_update = ["user1", "user3"]
    expected_delete = ["user1"]
    expected_manage = ["user1"]

    assert set(result[OperationType.READ]) == set(expected_read)
    assert set(result[OperationType.UPDATE]) == set(expected_update)
    assert set(result[OperationType.DELETE]) == set(expected_delete)
    assert set(result[OperationType.MANAGE]) == set(expected_manage)


@pytest.mark.usefixtures("access_properties")
def test_operation_by_group_property(access_properties):
    """Test operation_by_group property returns correct operation mapping"""
    result = access_properties.operation_by_group

    # group1 (ADMIN): READ, UPDATE, DELETE, MANAGE
    # group2 (USER): READ

    expected_read = ["group1", "group2"]
    expected_update = ["group1"]
    expected_delete = ["group1"]
    expected_manage = ["group1"]

    assert set(result[OperationType.READ]) == set(expected_read)
    assert set(result[OperationType.UPDATE]) == set(expected_update)
    assert set(result[OperationType.DELETE]) == set(expected_delete)
    assert set(result[OperationType.MANAGE]) == set(expected_manage)


def test_operation_by_user_multiple_same_operation():
    """Test operation_by_user with multiple users having same operations"""
    user_access = [
        UserAccessProperty(user_id="user1", role=Role.USER),
        UserAccessProperty(user_id="user2", role=Role.USER),
        UserAccessProperty(user_id="user3", role=Role.CONTRIBUTOR),
    ]
    props = KItemAccessProperties(user_access=user_access)
    result = props.operation_by_user

    # All users should have READ access
    assert set(result[OperationType.READ]) == {"user1", "user2", "user3"}
    # Only user3 (CONTRIBUTOR) should have UPDATE access
    assert result[OperationType.UPDATE] == ["user3"]


def test_operation_by_group_from_int():
    """Test operation_by_user with multiple users having same operations"""
    user_access = [
        UserAccessProperty(user_id="user1", role=1),
        UserAccessProperty(user_id="user2", role=1),
        UserAccessProperty(user_id="user3", role=2),
    ]
    props = KItemAccessProperties(user_access=user_access)
    result = props.operation_by_user

    # All users should have READ access
    assert set(result[OperationType.READ]) == {"user1", "user2", "user3"}
    # Only user3 (CONTRIBUTOR) should have UPDATE access
    assert result[OperationType.UPDATE] == ["user3"]
    assert props.by_user["user1"].role == Role.USER
    assert props.by_user["user1"].role.value == Role.USER.value


def test_operation_by_group_multiple_same_operation():
    """Test operation_by_group with multiple groups having same operations"""
    group_access = [
        GroupAccessProperty(group_id="group1", role=Role.USER),
        GroupAccessProperty(group_id="group2", role=Role.USER),
        GroupAccessProperty(group_id="group3", role=Role.ADMIN),
    ]
    props = KItemAccessProperties(group_access=group_access)
    result = props.operation_by_group

    # All groups should have READ access
    assert set(result[OperationType.READ]) == {"group1", "group2", "group3"}
    # Only group3 (ADMIN) should have MANAGE access
    assert result[OperationType.MANAGE] == ["group3"]
    assert props.group_by_role[Role.ADMIN] == ["group3"]
    assert props.group_by_role[Role.USER] == ["group1", "group2"]


def test_model_creation_with_defaults():
    """Test model creation with default values"""
    props = KItemAccessProperties()

    assert props.user_access == []
    assert props.group_access == []
    assert props.by_user == {}
    assert props.by_group == {}
    assert props.operation_by_user == {}
    assert props.operation_by_group == {}


def test_user_access_property_creation():
    """Test UserAccessProperty creation and access_level inheritance"""
    user_prop = UserAccessProperty(user_id="test_user", role=Role.CONTRIBUTOR)

    assert user_prop.user_id == "test_user"
    assert user_prop.role == Role.CONTRIBUTOR
    assert user_prop.access_level == [OperationType.READ, OperationType.UPDATE]


def test_duplicate_user_ids_raises_error():
    """Test that duplicate user IDs raise ValueError"""
    user_access = [
        UserAccessProperty(user_id="user1", role=Role.OWNER),
        UserAccessProperty(user_id="user2", role=Role.USER),
        UserAccessProperty(
            user_id="user1", role=Role.CONTRIBUTOR
        ),  # Duplicate
    ]

    with pytest.raises(ValidationError) as exc_info:
        KItemAccessProperties(user_access=user_access, group_access=[])

    # Check that the ValueError with the correct message is included
    error_details = exc_info.value.errors()
    assert len(error_details) == 1
    assert error_details[0]["type"] == "value_error"
    assert "Duplicate identifier found: user1" in str(
        error_details[0]["ctx"]["error"]
    )


def test_duplicate_group_ids_raises_error():
    """Test that duplicate group IDs raise ValueError"""
    group_access = [
        GroupAccessProperty(group_id="group1", role=Role.ADMIN),
        GroupAccessProperty(group_id="group2", role=Role.USER),
        GroupAccessProperty(
            group_id="group1", role=Role.CONTRIBUTOR
        ),  # Duplicate
    ]

    with pytest.raises(ValidationError) as exc_info:
        KItemAccessProperties(user_access=[], group_access=group_access)

    error_details = exc_info.value.errors()
    assert len(error_details) == 1
    assert error_details[0]["type"] == "value_error"
    assert "Duplicate identifier found: group1" in str(
        error_details[0]["ctx"]["error"]
    )


def test_both_user_and_group_duplicates_raises_multiple_errors():
    """Test that duplicates in both user and group access raise multiple errors"""
    user_access = [
        UserAccessProperty(user_id="user1", role=Role.OWNER),
        UserAccessProperty(user_id="user1", role=Role.USER),  # Duplicate
    ]
    group_access = [
        GroupAccessProperty(group_id="group1", role=Role.ADMIN),
        GroupAccessProperty(group_id="group1", role=Role.USER),  # Duplicate
    ]

    with pytest.raises(ValidationError) as exc_info:
        KItemAccessProperties(
            user_access=user_access, group_access=group_access
        )

    error_details = exc_info.value.errors()
    assert len(error_details) == 2

    # Check both errors
    user_error = next(
        err for err in error_details if err["loc"] == ("user_access",)
    )
    group_error = next(
        err for err in error_details if err["loc"] == ("group_access",)
    )

    assert "Duplicate identifier found: user1" in str(
        user_error["ctx"]["error"]
    )
    assert "Duplicate identifier found: group1" in str(
        group_error["ctx"]["error"]
    )


def test_case_sensitive_ids():
    """Test that IDs are case sensitive (no duplicates if different case)"""
    user_access = [
        UserAccessProperty(user_id="User1", role=Role.OWNER),
        UserAccessProperty(user_id="user1", role=Role.USER),  # Different case
        UserAccessProperty(
            user_id="USER1", role=Role.CONTRIBUTOR
        ),  # Different case
    ]

    # Should not throw an exception
    props = KItemAccessProperties(user_access=user_access, group_access=[])

    assert len(props.user_access) == 3
    assert props.by_user["User1"].role == Role.OWNER
    assert props.by_user["user1"].role == Role.USER
    assert props.by_user["USER1"].role == Role.CONTRIBUTOR
    assert props.user_by_role[Role.OWNER] == ["User1"]
    assert props.user_by_role[Role.USER] == ["user1"]
    assert props.user_by_role[Role.CONTRIBUTOR] == ["USER1"]

"""KItem Access Property Module"""

from enum import Enum, auto
from typing import Dict, List, Literal, Optional

from pydantic import BaseModel, Field, field_serializer, field_validator

from dsms.core.session import Session
from dsms.knowledge.utils import print_model


class OperationType(str, Enum):
    """Operation Types Enum"""

    CREATE = "create"
    READ = "read"
    UPDATE = "update"
    DELETE = "delete"
    MANAGE = "manage"


class Role(int, Enum):
    """Role Enum"""

    MEMBER = auto()
    CONTRIBUTOR = auto()
    OWNER = auto()


class RoleMapping(List[OperationType], Enum):
    """Role Mapping Enum"""

    OWNER = [
        OperationType.READ,
        OperationType.UPDATE,
        OperationType.DELETE,
        OperationType.MANAGE,
    ]
    MEMBER = [OperationType.READ]
    CONTRIBUTOR = [OperationType.READ, OperationType.UPDATE]

    @classmethod
    def get_operations(cls, role: Role) -> List[OperationType]:
        """Get operations for a role"""
        return getattr(cls, role.name.upper())

    @classmethod
    def min_access_level(cls, operation: OperationType) -> Role:
        """Get minimum role required for an operation.

        Raises ValueError if no role grants the given operation (e.g. CREATE).
        """
        candidates = [
            role.value
            for role in Role
            if operation in cls.get_operations(role)
        ]
        if not candidates:
            valid = [
                op.value
                for op in OperationType
                if any(op in cls.get_operations(r) for r in Role)
            ]
            raise ValueError(
                f"No role grants the '{operation.value}' operation. "
                f"Valid operations are: {valid}"
            )
        return Role(min(candidates))

    @classmethod
    def max_access_level(cls, operation: OperationType) -> Role:
        """Get maximum role required for an operation.

        Raises ValueError if no role grants the given operation (e.g. CREATE).
        """
        candidates = [
            role.value
            for role in Role
            if operation in cls.get_operations(role)
        ]
        if not candidates:
            valid = [
                op.value
                for op in OperationType
                if any(op in cls.get_operations(r) for r in Role)
            ]
            raise ValueError(
                f"No role grants the '{operation.value}' operation. "
                f"Valid operations are: {valid}"
            )
        return Role(max(candidates))


class BaseAccessProperty(BaseModel):
    """KItem Access Property Model"""

    role: Role = Field(
        ...,
        description="Defines the role mapping for access control.",
        example=RoleMapping.OWNER,
    )

    @field_validator("role", mode="before")
    @classmethod
    def parse_role(cls, v):
        """Accept string names (e.g. 'owner') or legacy integer values."""
        if isinstance(v, str):
            return Role[v.upper()]
        if isinstance(v, int):
            return Role(v)
        return v

    @property
    def access_level(self) -> List[OperationType]:
        """Set access level based on role"""
        return RoleMapping.get_operations(self.role)

    @field_serializer("role")
    def serialize_role_json(self, value: Role, _info):
        """Serialize role to JSON"""
        if _info.mode == "python":
            return value.name  # Python mode: uppercase name
        return (
            value.name.lower()
        )  # wire mode: "member", "contributor", "owner"


class UserAccessProperty(BaseAccessProperty):
    """KItem User Access Property Model"""

    user_id: str = Field(
        ...,
        description="The unique identifier of the user.",
        example="1a3b5c7d-9e0f-4g2h-8i1j-2k3l4m5n6o7p",
    )


class GroupAccessProperty(BaseAccessProperty):
    """KItem Group Access Property Model"""

    group_id: str = Field(
        ...,
        description="The unique identifier of the group.",
        example="g1h2i3j4-k5l6-m7n8-o9p0-q1r2s3t4u5v6",
    )


class KItemAccessProperties(BaseModel):
    """KItem Access Properties Model"""

    visibility: Literal["private", "internal", "public"] = Field(
        "private",
        description=(
            "Visibility level: private (explicit access only), "
            "internal (all authenticated users), public (everyone)."
        ),
    )
    user_access: Optional[List[UserAccessProperty]] = Field(
        [],
        description="List of user access properties.",
    )
    group_access: Optional[List[GroupAccessProperty]] = Field(
        [],
        description="List of group access properties (special visibility groups are excluded).",
    )

    def __str__(self) -> str:
        """Pretty print the access properties fields"""
        return print_model(
            self,
            "access_properties",
            exclude_extra=Session.dsms.config.hide_properties,
        )

    def __repr__(self) -> str:
        return str(self)

    @field_validator("user_access", "group_access", mode="after")
    @classmethod
    def check_duplicates(cls, v):
        """Ensure no duplicate user or group IDs"""
        if v is None:
            return []
        seen = set()
        for item in v:
            identifier = (
                item.user_id
                if isinstance(item, UserAccessProperty)
                else item.group_id
            )
            if identifier in seen:
                raise ValueError(f"Duplicate identifier found: {identifier}")
            seen.add(identifier)
        return v

    @property
    def by_user(self) -> Dict[str, UserAccessProperty]:
        """Get user access properties"""
        return {uap.user_id: uap for uap in self.user_access}

    @property
    def by_group(self) -> Dict[str, GroupAccessProperty]:
        """Get group access properties"""
        return {gap.group_id: gap for gap in self.group_access}

    @property
    def operation_by_user(self) -> Dict[OperationType, List[str]]:
        """Get access properties by operation type"""
        operation_dict: Dict[OperationType, List[str]] = {}
        for uap in self.user_access:
            for operation in uap.access_level:
                if operation not in operation_dict:
                    operation_dict[operation] = []
                if uap.user_id not in operation_dict[operation]:
                    operation_dict[operation].append(uap.user_id)
        return operation_dict

    @property
    def operation_by_group(self) -> Dict[OperationType, List[str]]:
        """Get group access properties by operation type"""
        operation_dict: Dict[OperationType, List[str]] = {}
        for gap in self.group_access:
            for operation in gap.access_level:
                if operation not in operation_dict:
                    operation_dict[operation] = []
                if gap.group_id not in operation_dict[operation]:
                    operation_dict[operation].append(gap.group_id)
        return operation_dict

    @property
    def user_by_role(self) -> Dict[Role, List[str]]:
        """Get users by role"""
        role_dict: Dict[Role, List[str]] = {}
        for uap in self.user_access:
            if uap.role not in role_dict:
                role_dict[uap.role] = []
            role_dict[uap.role].append(uap.user_id)
        return role_dict

    @property
    def group_by_role(self) -> Dict[Role, List[str]]:
        """Get groups by role"""
        role_dict: Dict[Role, List[str]] = {}
        for gap in self.group_access:
            if gap.role not in role_dict:
                role_dict[gap.role] = []
            role_dict[gap.role].append(gap.group_id)
        return role_dict

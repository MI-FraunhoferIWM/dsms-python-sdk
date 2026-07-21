"""KItem Access Property Module"""

from enum import Enum, auto
from typing import Dict, List, Literal

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


class AccessGrant(BaseModel):
    """A single principal (user or group) grant on a KItem."""

    id: str = Field(
        ...,
        description="The unique identifier of the user or group.",
    )
    type: Literal["user", "group"] = Field(
        ...,
        description="Whether this grant is for a user or a group.",
    )
    role: Role = Field(
        ...,
        description="Defines the role mapping for access control.",
    )

    @field_validator("role", mode="before")
    @classmethod
    def parse_role(cls, v):
        """Accept string names (e.g. 'owner') or integer values."""
        if isinstance(v, str):
            return Role[v.upper()]
        if isinstance(v, int):
            return Role(v)
        return v

    @property
    def access_level(self) -> List[OperationType]:
        """Operations granted by this role."""
        return RoleMapping.get_operations(self.role)

    @field_serializer("role")
    def serialize_role_json(self, value: Role, _info):
        """Serialize role as uppercase string in Python mode, lowercase for JSON."""
        if _info.mode == "python":
            return value.name
        return value.name.lower()


class KItemAccessProperties(BaseModel):
    """KItem Access Properties Model"""

    visibility: Literal["private", "internal", "public"] = Field(
        "private",
        description=(
            "Visibility level: private (explicit access only), "
            "internal (all authenticated users), public (everyone)."
        ),
    )
    grants: List[AccessGrant] = Field(
        default_factory=list,
        description="Unified list of user and group access grants.",
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

    @field_validator("grants", mode="after")
    @classmethod
    def check_duplicates(cls, v):
        """Ensure no duplicate principal (id, type) pairs."""
        if v is None:
            return []
        seen: set = set()
        for item in v:
            key = (item.id, item.type)
            if key in seen:
                raise ValueError(f"Duplicate grant found: {key}")
            seen.add(key)
        return v

    @property
    def by_id(self) -> Dict[str, "AccessGrant"]:
        """Get grants indexed by principal ID."""
        return {g.id: g for g in self.grants}

    @property
    def by_role(self) -> Dict[Role, List[str]]:
        """Get principal IDs grouped by role."""
        role_dict: Dict[Role, List[str]] = {}
        for g in self.grants:
            if g.role not in role_dict:
                role_dict[g.role] = []
            role_dict[g.role].append(g.id)
        return role_dict

    @property
    def operation_by_principal(self) -> Dict[OperationType, List[str]]:
        """Get principal IDs grouped by operation type."""
        op_dict: Dict[OperationType, List[str]] = {}
        for g in self.grants:
            for operation in g.access_level:
                if operation not in op_dict:
                    op_dict[operation] = []
                if g.id not in op_dict[operation]:
                    op_dict[operation].append(g.id)
        return op_dict

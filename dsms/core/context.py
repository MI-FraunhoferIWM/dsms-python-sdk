"""Most basic item in DSMS"""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Any, Dict, Optional
    from uuid import UUID

    from dsms.core.dsms import DSMS
    from dsms.knowledge.kitem import KItem


class Buffers:
    """Buffers of KItems for synchronization with the DSMS backend"""

    created: "Dict[UUID, KItem]" = {}

    updated: "Dict[UUID, KItem]" = {}

    deleted: "Dict[UUID, KItem]" = {}


class Context:
    """Object giving the current DSMS context."""

    dsms: "Optional[DSMS]" = None

    ktypes: "Dict[str, Any]" = {}

    buffers: Buffers = Buffers

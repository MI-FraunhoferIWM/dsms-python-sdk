"""Most basic item in DSMS"""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Any, Dict, Optional

    from dsms.core.dsms import DSMS
    from dsms.knowledge.kitem import KItem


class Buffers:
    """Buffers of KItems for synchronization with the DSMS backend"""

    added: "Dict[str, KItem]" = {}

    deleted: "Dict[str, KItem]" = {}

    @classmethod
    def clear(cls):
        """Clear all buffers of KItems for synchronization with the DSMS backend"""
        cls.added = {}
        cls.deleted = {}


class Session:
    """Object giving the current DSMS session."""

    kitems: "Dict[str, KItem]" = {}

    dsms: "Optional[DSMS]" = None

    ktypes: "Dict[str, Any]" = {}

    buffers: Buffers = Buffers

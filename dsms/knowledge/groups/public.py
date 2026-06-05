"""DSMS Public User Groups Module."""

from dsms.core.configuration import BaseConfiguration
from dsms.core.session import Session

from .models import Group

# The internally/externally public group objects will generally
# be served by the user-service, but we define them here for uniquely
# setting the ids and names in a common place.
# They can be adapted through environment variables anyway.
# A common place is needed because the group objects are used in various places
# such as internally within the knowledge service, the user service, and the SDK itself.
# If the IDs and names of these public groups are only delivered in the user service,
# we cannot distinguish them from the ones which come from keycloak
# - indicating only organizational groups.
#
# NOTE: These constants are initialised at import time using whatever config is
# available then (env-vars or defaults).  If a DSMS instance is later created
# with a Configuration that overrides id_internally_public / id_externally_public,
# call refresh_public_groups(config) to keep the constants in sync.


def _make_public_groups(cfg=None):
    if cfg is None:
        cfg = Session.dsms.config if Session.dsms else BaseConfiguration()
    return (
        Group(id=cfg.id_internally_public, name=cfg.label_internally_public),
        Group(id=cfg.id_externally_public, name=cfg.label_externally_public),
    )


INTERNALLY_PUBLIC_GROUP, EXTERNALLY_PUBLIC_GROUP = _make_public_groups()


def refresh_public_groups(config=None) -> None:
    """Re-create the public group constants from the given (or current) config.

    Call this after constructing a DSMS instance whose Configuration overrides
    id_internally_public or id_externally_public so that the module-level
    constants stay in sync with the running configuration.
    """
    global INTERNALLY_PUBLIC_GROUP, EXTERNALLY_PUBLIC_GROUP
    INTERNALLY_PUBLIC_GROUP, EXTERNALLY_PUBLIC_GROUP = _make_public_groups(
        config
    )

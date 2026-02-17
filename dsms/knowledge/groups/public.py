"""DSMS Public User Groups Module."""

from dsms.core.configuration import BaseConfiguration
from dsms.core.session import Session

from .models import Group

if not Session.dsms:
    config = BaseConfiguration()
else:
    config = Session.dsms.config

# The internally/externally public group objects will generally
# be served by the user-service, but we define them here for uniquely
# setting the ids and names in a common place.
# They can be adapted through environment variables anyway.
# A common place is needed because the group objects are used in various places
# such as internally within the knowledge service, the user service, and the SDK itself.
# If the IDs and names of these public groups are only delivered in the user service,
# we cannot distinguish them from the ones which come from keycloak
# - indicating only organizational groups.

INTERNALLY_PUBLIC_GROUP = Group(
    id=config.id_internally_public,
    name=config.label_internally_public,
)

EXTERNALLY_PUBLIC_GROUP = Group(
    id=config.id_externally_public,
    name=config.label_externally_public,
)

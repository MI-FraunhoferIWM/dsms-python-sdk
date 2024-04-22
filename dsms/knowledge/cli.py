"""Command line interface for kitem inspection"""


import click
from pydantic import BaseModel

from dsms import DSMS
from dsms.knowledge.properties import HDF5Container


@click.command()
@click.argument("kitem-id")
@click.option("-p", "--kitem-property", help="Name of the kitem property")
@click.option("-e", "--env", default=".env", help="Env file to load for the ")
@click.option(
    "-k",
    "--key",
    default=None,
    help="key of the subproperty of the KItem Property. E.g. a list index or a column name",
)
def lookup_kitem(kitem_id, kitem_property, env, key):
    """Simple CLI for looking up KItems from the DSMS"""
    dsms = DSMS(env=env)
    item = dsms[kitem_id]
    if kitem_property:
        attribute = getattr(item, kitem_property)
        if key:
            if not isinstance(attribute, (HDF5Container, BaseModel)):
                response = attribute[int(key)]
            else:
                response = getattr(attribute, key)
            if hasattr(response, "get_unit"):
                response = f"{response} {response.get_unit().get('symbol')}"
        else:
            response = attribute
    else:
        response = item
    click.echo(response)


if __name__ == "__main__":
    lookup_kitem()

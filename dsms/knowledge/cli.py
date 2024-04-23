"""Command line interface for kitem inspection"""


import click

from dsms import DSMS


@click.command()
@click.argument("kitem-id")
@click.option(
    "-e", "--env", default=".env", help="Env file to load for the dsms session"
)
@click.option("-u", "--units", is_flag=True, help="Display KItem with units")
def lookup_kitem(kitem_id, env, units):
    """Simple CLI for looking up KItems from the DSMS"""
    dsms = DSMS(env=env, display_units=units)
    item = dsms[kitem_id]
    click.echo(item)


if __name__ == "__main__":
    lookup_kitem()

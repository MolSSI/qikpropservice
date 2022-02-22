"""
CLI Interface file

Provides all the CLI commands which then invoke the library
"""

from inspect import getfullargspec

import click

from . import __version__
from .data_models import SeverHelloGETResponse
from .qplib import qikprop_as_a_service, QikpropAsAService


service_spec = getfullargspec(qikprop_as_a_service)


def _check_server(ctx, param, value):
    """Callback function to check if the server URI is actually listening"""
    endpoint = QikpropAsAService(server=value)
    connection_good, data_dict = endpoint.server_status()
    if not connection_good:
        click.echo(f"QikProp API Server at URI {value} could not be reached")
        ctx.exit()
    server_details = SeverHelloGETResponse(**data_dict)
    click.echo(f'Connected to {value} serving: "{server_details.title}"; version "{server_details.version_as_str}"')
    # Actually return the value
    return value


@click.group(name="qpcli")
@click.version_option(version=__version__, package_name="QikPropAsAServiceCLI")
def qpcli():
    """Access the QikProp as a Service API to process files and receive compressed output files from QikProp"""
    pass


@qpcli.command()
@click.option("--fast", "fast_processing", is_flag=True, default=service_spec.kwonlydefaults["fast"],
              help="Fast Processing Mode in QikProp")
@click.option("--similar", type=click.IntRange(min=0), default=service_spec.kwonlydefaults["similar"],
              help="Generate this number of most similar molecules relative to last processed")
@click.option("--uri", type=str, callback=_check_server, default=service_spec.kwonlydefaults["server_uri"])
@click.argument("files", nargs=-1, type=click.Path(exists=True))  # No help kwarg
def run(files, uri, fast_processing, similar):
    """
    Run the QikProp service

    Processes FILES provided against the server. Will return tarballs in {filename}.tar.gz as per the
    qikprop_as_a_service function in the qplib module.
    """
    qikprop_as_a_service(files,
                         server_uri=uri,
                         fast=fast_processing,
                         similar=similar)




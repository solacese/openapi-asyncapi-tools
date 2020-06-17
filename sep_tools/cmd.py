import click
import logging

from .EventPortal import EventPortal

logging.basicConfig(level=logging.INFO)

@click.group()
@click.version_option()
def cli():
    pass

@cli.command(name="importOpenAPI")
@click.argument('open_api_spec_file', type=click.Path(exists=True))
@click.option('--domain', default="TestDomain", show_default=True, 
    help='Application Domain')
@click.option('--application', default="TestApp", show_default=True,
    help='Application')
@click.option('--token', envvar='EVENT_PORTAL_TOKEN', required=True,
    help="The API token of Solace's Cloud REST API, could be set with env variable [EVENT_PORTAL_TOKEN]")
def cmdImportOpenAPI(open_api_spec_file, domain, application, token):
    """Generate an Application based on the specified OpenAPI 3.0 specification"""

    logging.info("Import file '{}' to build Application '{}' within Domain '{}'".format(
        open_api_spec_file, application, domain
    ))
    ep = EventPortal(token)
    ep.importOpenAPISpec(open_api_spec_file, domain, application)

@cli.command(name="generateAsyncAPI")
@click.argument('application')
@click.option('--token', envvar='EVENT_PORTAL_TOKEN', required=True,
    help="The API token of Solace's Cloud REST API, could be set with env variable [EVENT_PORTAL_TOKEN]")
def generateAsyncAPI(application, token):
    """Generate a AsyncAPI spec for the specified Application"""

    logging.info("Generate AsyncAPI spec for the Application '{}'".format(
         application
    ))
    ep = EventPortal(token)
    ep.generateAsyncApi(application)

if __name__ == '__main__':
    cli()
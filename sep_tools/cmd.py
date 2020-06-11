import click
import logging

logging.basicConfig(level=logging.INFO)

@click.command(name="importOpenAPI")
@click.argument('open_api_spec_file', type=click.Path(exists=True))
@click.option('--domain', default="TestDomain", show_default=True, 
    help='Application Domain')
@click.option('--application', default="TestApp", show_default=True,
    help='Application')
def cmdImportOpenAPI(open_api_spec_file, domain, application):
    print("Import file '{}' to build Application '{}' within Domain '{}'".format(
        open_api_spec_file, domain, application
    ))


if __name__ == '__main__':
    cmdImportOpenAPI()
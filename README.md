# OpenAPI AsyncAPI Tools

Tooling to assist with exchange of information between API Portal and Event Portal

## Installation

Clone this repo then install the package locally with:

```bash
$ pip install .
```

## Usage

You MUST [Obtain an API token from Solace Cloud](https://docs.solace.com/Solace-Cloud/ght_use_rest_api_client_profiles.htm) using your account before launching this tool.

```bash
$ sep importOpenAPI --help
Usage: importOpenAPI [OPTIONS] OPEN_API_SPEC_FILE

Options:
  --domain TEXT       Application Domain  [default: TestDomain]
  --application TEXT  Application  [default: TestApp]
  --token TEXT        The API token of Solace's Cloud REST API, could be set
                      with env variable [EVENT_PORTAL_TOKEN]  [required]

  --help              Show this message and exit.
```

## Known Issues

If you encountered below issue like :

> RuntimeError: Click will abort further execution because Python 3 was configured to use ASCII as encoding for the environment. Consult https://click.palletsprojects.com/python3/ for mitigation steps.

Please run `export LC_ALL=en_US.UTF-8` to fix it.

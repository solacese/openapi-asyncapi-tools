from setuptools import setup, find_packages

with open('README.md') as f:
    readme = f.read()

setup(
    name='sep-tools',
    version='0.1.0',
    description='',
    long_description=readme,
    author='Solace SE',
    url='https://github.com/solacese/openapi-asyncapi-tools',
    packages=find_packages(exclude=('tests', 'docs')),
    install_requires=[
        'click',
        'PyYAML',
    ],
    entry_points={
        "console_scripts": [
            "importOpenAPI=sep_tools.cmd:cmdImportOpenAPI",
        ]
    },
)

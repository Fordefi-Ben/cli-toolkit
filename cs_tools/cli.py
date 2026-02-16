"""CS_Tools CLI entry point."""

import click

from .commands.configure import configure
from .commands.assets import assets, create as assets_create
from .commands.vaults import vaults, refresh as vaults_refresh

# Mobile logs commands
from mobile_logs.commands import summary as logs_summary
from mobile_logs.commands import errors as logs_errors
from mobile_logs.commands import search as logs_search
from mobile_logs.commands import export as logs_export


@click.group()
@click.version_option(version="0.1.0", prog_name="cstool")
def cli():
    """cstool - Fordefi API CLI
    
    A command-line tool for interacting with the Fordefi API
    asset creation endpoint.
    
    Get started by running:
    
        cstool configure
    
    Then create assets with:
    
        cstool create-asset
        cstool assets create  (also works)
    
    Or refresh vault assets with:
    
        cstool refresh-vault
        cstool vaults refresh  (also works)
    
    Analyze mobile logs with:
    
        cstool logs-summary logs.zip
        cstool logs-errors logs.zip
    """
    pass


# Register command groups
cli.add_command(configure)
cli.add_command(assets)
cli.add_command(vaults)

# Register aliases for convenience
cli.add_command(assets_create, name="create-asset")
cli.add_command(vaults_refresh, name="refresh-vault")

# Mobile logs commands
cli.add_command(logs_summary, name="logs-summary")
cli.add_command(logs_errors, name="logs-errors")
cli.add_command(logs_search, name="logs-search")
cli.add_command(logs_export, name="logs-export")


if __name__ == "__main__":
    cli()

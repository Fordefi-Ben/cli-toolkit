"""Mobile Logs CLI entry point."""

import click

from .commands import summary, errors, search, export


@click.group()
@click.version_option(version="0.1.0", prog_name="mobile_logs")
def cli():
    """Mobile Logs - Parse and analyze Fordefi mobile app logs.
    
    A CLI tool for extracting insights from mobile device
    diagnostic logs (flog*.txt files).
    
    Quick start:
    
        mlogs summary logs.zip
        
        mlogs errors logs.zip
        
        mlogs search logs.zip "token"
    """
    pass


# Register commands
cli.add_command(summary)
cli.add_command(errors)
cli.add_command(search)
cli.add_command(export)


if __name__ == "__main__":
    cli()

"""Configure command for CS_Tools CLI."""

import click

from ..config import (
    load_config,
    save_config,
    CONFIG_FILE,
)


@click.command()
def configure():
    """Configure CS_Tools with your API credentials."""
    click.echo(click.style("CS_Tools Configuration", fg="cyan", bold=True))
    click.echo()
    
    # Load existing config for defaults
    existing_config = load_config()
    
    # Prompt for API key
    existing_key = existing_config.get("api_key", "")
    masked_key = ""
    if existing_key:
        # Show first 8 and last 4 characters
        if len(existing_key) > 12:
            masked_key = f"{existing_key[:8]}...{existing_key[-4:]}"
        else:
            masked_key = "****"
    
    if masked_key:
        click.echo(f"Current API key: {masked_key}")
    
    api_key = click.prompt(
        "Enter your Fordefi API key",
        default="",
        hide_input=True,
        show_default=False,
    )
    
    # Keep existing key if user just pressed enter
    if not api_key and existing_key:
        api_key = existing_key
        click.echo("Keeping existing API key.")
    elif not api_key:
        click.echo(click.style("Warning: No API key provided.", fg="yellow"))
    
    # Save configuration
    config = {
        "api_key": api_key,
    }
    
    save_config(config)
    
    click.echo()
    click.echo(click.style("✅ Configuration saved!", fg="green", bold=True))
    click.echo(f"Config file: {CONFIG_FILE}")
    click.echo()
    click.echo("You can now use 'cs_tools assets create' to create assets.")
    click.echo()
    click.echo(click.style("Tip:", fg="cyan"), nl=False)
    click.echo(" You can also set the CS_TOOLS_API_KEY environment variable")
    click.echo("to override the stored API key.")

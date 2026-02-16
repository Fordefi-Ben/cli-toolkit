"""API client for CS_Tools CLI."""

from typing import Dict, Any

import requests

from .config import get_api_key, get_api_base_url
from .errors import handle_response


ASSET_ENDPOINT = "/api/v1/assets/asset-infos"
TIMEOUT = 30


def create_asset(payload: Dict[str, Any]) -> None:
    """Create an asset via the Fordefi API.
    
    Args:
        payload: The asset creation payload
        
    Raises:
        click.ClickException: If API key is not configured
    """
    import click
    
    api_key = get_api_key()
    if not api_key:
        raise click.ClickException(
            "API key not configured. Run 'cs_tools configure' first."
        )
    
    base_url = get_api_base_url()
    url = f"{base_url}{ASSET_ENDPOINT}"
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    
    try:
        response = requests.post(
            url,
            json=payload,
            headers=headers,
            timeout=TIMEOUT,
        )
        handle_response(response, "Asset created successfully!")
    except requests.exceptions.Timeout:
        click.echo(click.style("❌ Request Timeout", fg="red", bold=True))
        click.echo()
        click.echo("The request timed out after 30 seconds.")
        click.echo("Please try again.")
    except requests.exceptions.ConnectionError:
        click.echo(click.style("❌ Connection Error", fg="red", bold=True))
        click.echo()
        click.echo("Could not connect to the API server.")
        click.echo("Please check your internet connection and try again.")
    except requests.exceptions.RequestException as e:
        click.echo(click.style("❌ Request Error", fg="red", bold=True))
        click.echo()
        click.echo(f"An error occurred: {e}")

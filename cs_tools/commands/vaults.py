"""Vault commands for CS_Tools CLI."""

import json
from typing import Optional, List

import click
import requests

from ..config import get_api_base_url, is_configured
from ..errors import handle_response


REFRESH_ENDPOINT = "/api/v1/assets/refresh-owned-assets"
TIMEOUT = 30


@click.group()
def vaults():
    """Vault management commands."""
    pass


@vaults.command()
@click.option(
    "--token", "-t",
    help="Ephemeral bearer token (required for this endpoint)"
)
@click.option(
    "--vault-id", "-v",
    multiple=True,
    help="Vault ID(s) to refresh (can specify multiple)"
)
@click.option(
    "--asset-id", "-a",
    multiple=True,
    help="Asset ID(s) to refresh (can specify multiple)"
)
@click.option(
    "--org-id", "-o",
    help="Organization ID to refresh (required)"
)
def refresh(token: str, vault_id: tuple, asset_id: tuple, org_id: str):
    """Refresh owned assets for vaults.
    
    This endpoint requires an ephemeral bearer token (not your regular API key).
    
    Examples:
    
        # Interactive mode
        cs_tools vaults refresh
        
        # With token flag
        cs_tools vaults refresh -t "your-ephemeral-token" -v vault-id
        
        # Multiple vaults
        cs_tools vaults refresh -t "token" -v vault-id-1 -v vault-id-2
        
        # All options
        cs_tools vaults refresh -t "token" -v vault-id -a asset-id -o org-id
    """
    # If no options provided, run full interactive mode
    is_interactive = not token and not vault_id and not asset_id and not org_id
    
    if is_interactive:
        token, vault_id, asset_id, org_id = prompt_for_all_inputs()
    elif not token:
        # They provided some IDs but no token, prompt for token only
        token = prompt_for_token()
    
    if not token:
        click.echo(click.style("❌ No token provided", fg="red", bold=True))
        click.echo("An ephemeral bearer token is required for this endpoint.")
        return
    
    # Build payload
    payload = {}
    
    if vault_id:
        payload["vault_ids"] = list(vault_id)
    if asset_id:
        payload["asset_ids"] = list(asset_id)
    if org_id:
        payload["organization_ids"] = [org_id]
    
    if not payload:
        click.echo(click.style("❌ No IDs provided", fg="red", bold=True))
        click.echo("Please provide at least one vault ID or asset ID, and an organization ID.")
        return
    
    if not org_id:
        click.echo(click.style("❌ Organization ID required", fg="red", bold=True))
        click.echo("An organization ID must be provided.")
        return
    
    # Show what we're sending
    click.echo()
    click.echo("Refreshing with payload:")
    click.echo(json.dumps(payload, indent=2))
    click.echo()
    click.echo("Sending request...")
    click.echo()
    
    # Make request
    refresh_assets(token, payload)


def prompt_for_token() -> str:
    """Prompt user for ephemeral bearer token."""
    click.echo()
    click.echo(click.style("Note:", fg="yellow"), nl=False)
    click.echo(" This endpoint requires an ephemeral bearer token, not your regular API key.")
    click.echo()
    
    token = click.prompt(
        "Enter ephemeral bearer token",
        hide_input=True
    )
    
    return token.strip()


def prompt_for_all_inputs() -> tuple:
    """Prompt user for token and all IDs interactively."""
    click.echo(click.style("Refresh Vault Assets", fg="cyan", bold=True))
    
    # Collect IDs first (before token to minimize expiration risk)
    vault_ids = prompt_for_id_list("vault")
    asset_ids = prompt_for_id_list("asset")
    org_id = prompt_for_single_org_id()
    
    # Get token last
    token = prompt_for_token()
    
    return token, tuple(vault_ids), tuple(asset_ids), org_id


def prompt_for_id_list(id_type: str) -> List[str]:
    """Prompt user for a list of IDs of a specific type.
    
    Args:
        id_type: The type of ID (e.g., "vault", "asset")
        
    Returns:
        List of IDs entered by the user
    """
    click.echo()
    count = click.prompt(
        f"How many {id_type} IDs do you want to enter?",
        type=int,
        default=0
    )
    
    if count <= 0:
        return []
    
    ids = []
    for i in range(1, count + 1):
        id_value = click.prompt(f"  {id_type.capitalize()} ID {i}/{count}")
        if id_value.strip():
            ids.append(id_value.strip())
    
    return ids


def prompt_for_single_org_id() -> str:
    """Prompt user for a single organization ID.
    
    Returns:
        Organization ID
    """
    click.echo()
    org_id = click.prompt("Enter organization ID")
    
    return org_id.strip()


def refresh_assets(token: str, payload: dict) -> None:
    """Make the refresh assets API call."""
    base_url = get_api_base_url()
    url = f"{base_url}{REFRESH_ENDPOINT}"
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }
    
    try:
        response = requests.post(
            url,
            json=payload,
            headers=headers,
            timeout=TIMEOUT,
        )
        handle_refresh_response(response)
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


def handle_refresh_response(response) -> None:
    """Handle the refresh API response."""
    if response.status_code == 200:
        click.echo(click.style("✅ Refresh triggered successfully!", fg="green", bold=True))
        click.echo()
        try:
            data = response.json()
            if data:
                click.echo(json.dumps(data, indent=2))
        except json.JSONDecodeError:
            if response.text:
                click.echo(response.text)
    else:
        # Use the standard error handler for non-200 responses
        handle_response(response)

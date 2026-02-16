"""Error handling for CS_Tools CLI."""

import json
from typing import Any, Dict, Optional

import click


def handle_response(response, success_message: str = "Request completed successfully!") -> None:
    """Handle API response and display appropriate output."""
    status_code = response.status_code

    if status_code == 200:
        handle_success(response, success_message)
    elif status_code == 400:
        handle_bad_request(response)
    elif status_code == 401:
        handle_unauthorized(response)
    elif status_code == 403:
        handle_forbidden(response)
    elif status_code == 404:
        handle_not_found(response)
    elif status_code == 408:
        handle_timeout(response)
    elif status_code == 422:
        handle_validation_error(response)
    elif status_code == 429:
        handle_rate_limit(response)
    elif status_code >= 500:
        handle_server_error(response)
    else:
        handle_unknown_error(response)


def handle_success(response, message: str = "Request completed successfully!") -> None:
    """Handle successful response."""
    click.echo(click.style(f"✅ {message}", fg="green", bold=True))
    click.echo()
    try:
        data = response.json()
        click.echo(json.dumps(data, indent=2))
    except json.JSONDecodeError:
        click.echo(response.text)


def handle_bad_request(response) -> None:
    """Handle 400 Bad Request error."""
    click.echo(click.style("❌ Bad Request (400)", fg="red", bold=True))
    click.echo()
    
    try:
        data = response.json()
        if "title" in data:
            click.echo(f"Title: {data['title']}")
        if "detail" in data:
            click.echo(f"Detail: {data['detail']}")
        if "full_detail" in data:
            click.echo(f"Full Detail: {data['full_detail']}")
        if "system_error_code" in data:
            click.echo(f"System Error Code: {data['system_error_code']}")
        
        # If none of the expected fields, print raw JSON
        if not any(k in data for k in ["title", "detail", "full_detail", "system_error_code"]):
            click.echo(json.dumps(data, indent=2))
    except json.JSONDecodeError:
        click.echo(response.text)


def handle_unauthorized(response) -> None:
    """Handle 401 Unauthorized error."""
    click.echo(click.style("❌ Unauthorized (401)", fg="red", bold=True))
    click.echo()
    click.echo("Your API key appears to be invalid or expired.")
    click.echo()
    click.echo(click.style("Suggestions:", fg="yellow"))
    click.echo("  • Check that your API key is correct")
    click.echo("  • Make sure you're using a TRADER key (not a viewer key)")
    click.echo("  • Run 'cs_tools configure' to update your API key")
    
    try:
        data = response.json()
        if data:
            click.echo()
            click.echo("API Response:")
            click.echo(json.dumps(data, indent=2))
    except json.JSONDecodeError:
        pass


def handle_forbidden(response) -> None:
    """Handle 403 Forbidden error."""
    click.echo(click.style("❌ Forbidden (403)", fg="red", bold=True))
    click.echo()
    click.echo("Your API key does not have permission for this operation.")
    click.echo()
    click.echo(click.style("Suggestions:", fg="yellow"))
    click.echo("  • You need a TRADER key to create assets")
    click.echo("  • Contact your administrator to upgrade your API key permissions")
    
    try:
        data = response.json()
        if data:
            click.echo()
            click.echo("API Response:")
            click.echo(json.dumps(data, indent=2))
    except json.JSONDecodeError:
        pass


def handle_not_found(response) -> None:
    """Handle 404 Not Found error."""
    click.echo(click.style("❌ Not Found (404)", fg="red", bold=True))
    click.echo()
    click.echo(click.style("Suggestions:", fg="yellow"))
    click.echo("  • Double-check the token address is correct")
    click.echo("  • Verify you selected the correct chain/network")
    click.echo("  • Ensure the token exists on the specified network")
    
    try:
        data = response.json()
        if data:
            click.echo()
            click.echo("API Response:")
            click.echo(json.dumps(data, indent=2))
    except json.JSONDecodeError:
        pass


def handle_timeout(response) -> None:
    """Handle 408 Timeout error."""
    click.echo(click.style("❌ Request Timeout (408)", fg="red", bold=True))
    click.echo()
    click.echo("The request timed out while waiting for a response.")
    click.echo()
    click.echo(click.style("Suggestions:", fg="yellow"))
    click.echo("  • Please try again in a few moments")
    click.echo("  • If the problem persists, the API may be experiencing issues")


def handle_validation_error(response) -> None:
    """Handle 422 Validation Error."""
    click.echo(click.style("❌ Validation Error (422)", fg="red", bold=True))
    click.echo()
    
    try:
        data = response.json()
        
        # Handle FastAPI-style validation errors
        if "detail" in data and isinstance(data["detail"], list):
            click.echo("Validation errors:")
            click.echo()
            for i, error in enumerate(data["detail"], 1):
                loc = error.get("loc", [])
                msg = error.get("msg", "Unknown error")
                error_type = error.get("type", "unknown")
                
                location = " -> ".join(str(l) for l in loc) if loc else "unknown"
                click.echo(f"  {i}. Location: {location}")
                click.echo(f"     Message: {msg}")
                click.echo(f"     Type: {error_type}")
                click.echo()
        else:
            click.echo(json.dumps(data, indent=2))
    except json.JSONDecodeError:
        click.echo(response.text)


def handle_rate_limit(response) -> None:
    """Handle 429 Rate Limit error."""
    click.echo(click.style("❌ Rate Limited (429)", fg="red", bold=True))
    click.echo()
    click.echo("You've exceeded the API rate limit.")
    click.echo()
    click.echo(click.style("Suggestions:", fg="yellow"))
    click.echo("  • Wait a few minutes before trying again")
    click.echo("  • Reduce the frequency of your requests")
    
    try:
        data = response.json()
        if data:
            click.echo()
            click.echo("API Response:")
            click.echo(json.dumps(data, indent=2))
    except json.JSONDecodeError:
        pass


def handle_server_error(response) -> None:
    """Handle 5xx Server Error."""
    click.echo(click.style(f"❌ Server Error ({response.status_code})", fg="red", bold=True))
    click.echo()
    click.echo("The API server encountered an error.")
    click.echo()
    
    # Try to extract request_id for support
    request_id = None
    try:
        data = response.json()
        request_id = data.get("request_id")
        if request_id:
            click.echo(f"Request ID: {click.style(request_id, fg='cyan')}")
            click.echo("Please provide this ID when contacting support.")
            click.echo()
    except json.JSONDecodeError:
        pass
    
    # Check headers for request ID as fallback
    if not request_id:
        request_id = response.headers.get("x-request-id") or response.headers.get("X-Request-Id")
        if request_id:
            click.echo(f"Request ID: {click.style(request_id, fg='cyan')}")
            click.echo("Please provide this ID when contacting support.")
            click.echo()
    
    click.echo(click.style("Suggestions:", fg="yellow"))
    click.echo("  • Try again in a few moments")
    click.echo("  • If the problem persists, contact support")


def handle_unknown_error(response) -> None:
    """Handle unknown error status codes."""
    click.echo(click.style(f"❌ Error ({response.status_code})", fg="red", bold=True))
    click.echo()
    
    try:
        data = response.json()
        click.echo(json.dumps(data, indent=2))
    except json.JSONDecodeError:
        click.echo(response.text if response.text else "No response body")

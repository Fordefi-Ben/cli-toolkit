# cstool Developer Guide

This document covers how to extend and modify the cstool CLI.

## Project Architecture

```
CS_Tool/
├── cs_tools/
│   ├── cli.py           # Main entry point, registers commands
│   ├── config.py        # Configuration management (~/.cs_tools/config.yaml)
│   ├── api.py           # HTTP client for Fordefi API (asset creation)
│   ├── errors.py        # Response/error handling
│   ├── constants.py     # Blockchain types, networks, exchanges
│   ├── payloads.py      # Payload builders for each blockchain
│   └── commands/
│       ├── __init__.py  # Exports all commands
│       ├── configure.py # Configuration command
│       ├── assets.py    # Asset creation command
│       └── vaults.py    # Vault refresh command
└── mobile_logs/         # Mobile log parsing package
    ├── cli.py           # Standalone CLI (also integrated into cstool)
    ├── parser.py        # Log format parser
    ├── extractor.py     # Zip extraction and file discovery
    ├── filters.py       # Filter by level, module, time, text
    ├── redactor.py      # Sanitize sensitive data
    ├── datetime_utils.py # Flexible datetime parsing
    ├── grouping.py      # Session grouping utilities
    └── commands/
        ├── summary.py   # logs-summary command
        ├── errors.py    # logs-errors command
        ├── search.py    # logs-search command
        └── export.py    # logs-export command
```

## Existing Commands

### `cstool configure`
Sets up API key and base URL. Stores config in `~/.cs_tools/config.yaml`.

### `cstool assets create` (alias: `cstool create-asset`)
Interactive asset creation for various blockchains. Uses the stored API key.

### `cstool vaults refresh` (alias: `cstool refresh-vault`)
Refreshes owned assets for vaults. **Requires an ephemeral bearer token** (not the stored API key).

**Endpoint:** `POST /api/v1/assets/refresh-owned-assets`

**Payload:**
```json
{
  "vault_ids": ["..."],
  "asset_ids": ["..."],
  "organization_ids": ["..."]  // Single org ID in array (required)
}
```

**Usage:**
```bash
# Interactive
cstool vaults refresh

# Non-interactive
cstool vaults refresh -t "ephemeral-token" -v vault-id-1 -v vault-id-2 -a asset-id -o org-id
```

### Mobile Logs Commands

| Command | Description | Key Options |
|---------|-------------|-------------|
| `cstool logs-summary` | Quick stats (device, OS, app version, error count) | — |
| `cstool logs-errors` | Show sessions containing errors | `--redact`, `--gap`, `-n` (limit) |
| `cstool logs-search` | Search/filter log entries | `--after`, `--before`, `--group/--no-group`, `--gap` |
| `cstool logs-export` | Export filtered logs to file | `-o` (optional, auto-names), `-f` (default: json), `--after`, `--before`, `--group/--no-group`, `--gap` |

---

## Mobile Logs Module Details

### Datetime Utilities (`datetime_utils.py`)

Provides flexible datetime parsing for `--after` and `--before` filters.

**Supported formats:**
- ISO: `2026-01-15`, `2026-01-15 10:30`, `2026-01-15T10:30`
- Month-day: `01-15`, `1/15`
- Named month: `jan 15`, `january 15`, `jan 15 10pm`
- Time only: `10:00`, `10pm` (for filtering, not range queries)

**Key functions:**
```python
from mobile_logs.datetime_utils import parse_datetime_filter, parse_flexible_datetime

# For --after/--before filters
dt = parse_datetime_filter("jan 15", filter_type='after')  # Returns start of day
dt = parse_datetime_filter("jan 15", filter_type='before')  # Returns end of day

# For general parsing (returns DateTimeParseResult with start/end range)
result = parse_flexible_datetime("jan 15 10pm")
```

### Session Grouping (`grouping.py`)

Groups log entries into sessions based on time gaps between consecutive entries.

**Key functions:**
```python
from mobile_logs.grouping import group_by_sessions, format_session_header, Session

# Group entries (default: 5-minute gap threshold)
sessions: List[Session] = group_by_sessions(entries, gap_threshold_seconds=300)

# Each Session has:
session.entries        # List[LogEntry]
session.start_time     # datetime
session.end_time       # datetime
session.duration_seconds  # float
session.entry_count    # int
session.error_count    # int

# Format header for display
header = format_session_header(session, width=70)
# "━━━ Session 1 • Jan 15, 11:06 AM (47 entries, 3.2s) ━━━"
```

**Session detection algorithm:**
1. Sort entries by timestamp
2. Iterate through entries, tracking current session
3. If gap between consecutive entries exceeds threshold, start new session
4. Return list of Session objects

---

## Adding New Commands

### Step 1: Create the Command File

Create a new file in `cs_tools/commands/`. For example, `cs_tools/commands/transactions.py`:

```python
"""Transaction commands for cstool CLI."""

import click

from ..config import is_configured, get_api_key, get_api_base_url


@click.group()
def transactions():
    """Transaction management commands."""
    pass


@transactions.command()
def list():
    """List recent transactions."""
    if not is_configured():
        click.echo(click.style("❌ Not configured", fg="red", bold=True))
        click.echo("Please run 'cstool configure' first.")
        return
    
    click.echo("Fetching transactions...")
    # Implementation here
```

### Step 2: Export from commands/__init__.py

Edit `cs_tools/commands/__init__.py`:

```python
"""Commands for cstool CLI."""

from .configure import configure
from .assets import assets
from .vaults import vaults
from .transactions import transactions  # Add this line

__all__ = ["configure", "assets", "vaults", "transactions"]
```

### Step 3: Register in cli.py

Edit `cs_tools/cli.py`:

```python
from .commands.configure import configure
from .commands.assets import assets
from .commands.vaults import vaults
from .transactions import transactions  # Add this import

# ... existing code ...

# Register commands
cli.add_command(configure)
cli.add_command(assets)
cli.add_command(vaults)
cli.add_command(transactions)  # Add this line
```

### Command Patterns

**Simple command (no subcommands):**

```python
@click.command()
def mycommand():
    """Description shown in help."""
    click.echo("Hello!")
```

**Command group (with subcommands):**

```python
@click.group()
def mygroup():
    """Group description."""
    pass

@mygroup.command()
def subcommand():
    """Subcommand description."""
    pass
```

**Command with arguments and options:**

```python
@click.command()
@click.argument("name")  # Required positional argument
@click.option("--count", "-c", default=1, help="Number of times")
@click.option("--verbose", "-v", is_flag=True, help="Verbose output")
def greet(name: str, count: int, verbose: bool):
    """Greet someone."""
    for _ in range(count):
        if verbose:
            click.echo(f"Greeting: Hello, {name}!")
        else:
            click.echo(f"Hello, {name}!")
```

### Commands with Different Authentication

Some endpoints require different authentication (e.g., ephemeral tokens instead of the stored API key). See `vaults.py` for an example:

```python
@click.command()
@click.option(
    "--token", "-t",
    help="Ephemeral bearer token (required for this endpoint)"
)
def mycommand(token: str):
    """Command requiring ephemeral token."""
    
    # Prompt for token if not provided
    if not token:
        click.echo(click.style("Note:", fg="yellow"), nl=False)
        click.echo(" This endpoint requires an ephemeral bearer token.")
        token = click.prompt("Enter ephemeral bearer token", hide_input=True)
    
    # Use the token directly instead of get_api_key()
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }
    # ... make request
```

### Commands with Multiple ID Inputs

For commands that accept multiple IDs (like `vaults refresh`), use this pattern:

```python
def prompt_for_id_list(id_type: str) -> List[str]:
    """Prompt user for a list of IDs of a specific type."""
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
```

For CLI flags, use `multiple=True`:

```python
@click.option(
    "--vault-id", "-v",
    multiple=True,
    help="Vault ID(s) to refresh (can specify multiple)"
)
def mycommand(vault_id: tuple):
    # vault_id is a tuple, convert to list if needed
    vault_ids = list(vault_id)
```

---

## Creating Command Aliases

You can create shorter or alternative names for commands while keeping the original command structure intact.

### Current Aliases

| Full Command | Alias |
|--------------|-------|
| `cstool assets create` | `cstool create-asset` |
| `cstool vaults refresh` | `cstool refresh-vault` |

### Adding a New Alias

```python
# cli.py

# Import the subcommand
from .commands.mygroup import mygroup, mysubcommand as mygroup_mysubcommand

# Register both
cli.add_command(mygroup)  # cstool mygroup mysubcommand
cli.add_command(mygroup_mysubcommand, name="my-alias")  # cstool my-alias
```

### Naming Conventions

- Use kebab-case for aliases: `create-asset`, `refresh-vault`
- Keep aliases short but descriptive

---

## Testing Changes

### Manual Testing

```bash
# Reinstall after changes (pipx - macOS)
pipx install /path/to/CS_Tool --force

# Or if using a virtual environment
pip install -e .

# Test help output
cstool --help
cstool assets --help
cstool assets create --help

# Test commands
cstool create-asset
cstool refresh-vault
cstool logs-summary /path/to/logs.zip

# Test new datetime and session features
cstool logs-search logs.zip -a "jan 15" -b "jan 16"
cstool logs-errors logs.zip --gap 60
cstool logs-export logs.zip               # auto-generates logs.json
cstool logs-export logs.zip -f text       # auto-generates logs.txt
```

---

## Code Style Guidelines

- Use type hints for function parameters and return values
- Add docstrings to all public functions
- Use Click's built-in utilities for user interaction (`click.prompt`, `click.echo`, `click.style`)
- Handle errors gracefully with helpful user messages
- Use kebab-case for command names (e.g., `create-asset`, `logs-summary`)

---

## Common Patterns

### Colored Output

```python
# Success
click.echo(click.style("✅ Success!", fg="green", bold=True))

# Error
click.echo(click.style("❌ Error!", fg="red", bold=True))

# Warning
click.echo(click.style("⚠️ Warning", fg="yellow"))

# Info
click.echo(click.style("ℹ️ Info", fg="cyan"))
```

### User Prompts

```python
# Simple prompt
name = click.prompt("Enter name")

# With default
name = click.prompt("Enter name", default="default_value")

# Hidden input (for secrets)
api_key = click.prompt("Enter API key", hide_input=True)

# Confirmation
if click.confirm("Are you sure?"):
    # proceed
```

### Session Grouping in Commands

When adding session grouping to a new command:

```python
from ..grouping import group_by_sessions, format_session_header, DEFAULT_GAP_THRESHOLD

@click.command()
@click.option('--group/--no-group', default=True, help='Group by session')
@click.option('--gap', '-g', default=DEFAULT_GAP_THRESHOLD, type=float,
              help=f'Session gap threshold in seconds (default: {DEFAULT_GAP_THRESHOLD})')
def mycommand(group: bool, gap: float):
    # ... get entries ...
    
    if group:
        sessions = group_by_sessions(entries, gap)
        for session in sessions:
            if len(sessions) > 1:
                click.echo(format_session_header(session))
            for entry in session.entries:
                display_entry(entry)
    else:
        for entry in entries:
            display_entry(entry)
```

### Flexible Datetime Parsing in Commands

When adding datetime filters to a new command:

```python
from ..datetime_utils import parse_datetime_filter

@click.command()
@click.option('--after', '-a', help='Only entries after this time')
@click.option('--before', '-b', help='Only entries before this time')
def mycommand(after: str, before: str):
    after_dt = None
    before_dt = None
    
    if after:
        try:
            after_dt = parse_datetime_filter(after, 'after')
        except ValueError as e:
            click.echo(click.style(f"❌ Invalid --after value: {e}", fg="red"))
            return
    
    if before:
        try:
            before_dt = parse_datetime_filter(before, 'before')
        except ValueError as e:
            click.echo(click.style(f"❌ Invalid --before value: {e}", fg="red"))
            return
    
    # Use after_dt and before_dt for filtering
```

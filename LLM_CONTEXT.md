# cstool - LLM Context Document

> **Purpose**: This document provides complete context for LLMs to understand, modify, and extend the cstool CLI. Drop this entire file into your prompt when working on this codebase.

> **IMPORTANT**: When making ANY code changes, you MUST update ALL THREE documentation files:
> - `README.md` — user-facing docs
> - `DEVELOPER.md` — developer docs  
> - `LLM_CONTEXT.md` — this file

---

## Project Overview

**cstool** is a Python CLI for interacting with the Fordefi API. It currently supports:
1. **Asset creation** (`cstool create-asset`) — create token assets across 10 blockchain types
2. **Vault refresh** (`cstool refresh-vault`) — trigger refresh of owned assets for vaults
3. **Mobile logs analysis** (`cstool logs-*`) — parse and analyze Fordefi mobile app diagnostic logs

**Tech stack**: Python 3.8+, Click (CLI), Requests (HTTP), PyYAML (config), python-dateutil (datetime parsing)

**Installation**: `pipx install /path/to/CS_Tool` (macOS) or `pip install -e .` (venv)

**Reinstall after changes**: `pipx install /path/to/CS_Tool --force`

---

## File Map

```
CS_Tool/
├── pyproject.toml          # Package config, defines "cstool" entry point
├── requirements.txt        # Dependencies: click, requests, pyyaml, python-dateutil
├── README.md               # User documentation
├── DEVELOPER.md            # Developer documentation  
├── LLM_CONTEXT.md          # This file
├── cs_tools/
│   ├── __init__.py         # Package init, version string
│   ├── cli.py              # Entry point, registers all commands and aliases
│   ├── config.py           # Config management (~/.cs_tools/config.yaml)
│   ├── api.py              # HTTP client for asset creation endpoint
│   ├── errors.py           # Response handling for all HTTP status codes
│   ├── constants.py        # Blockchain types, networks, exchanges lists
│   ├── payloads.py         # Payload builder functions for each blockchain
│   └── commands/
│       ├── __init__.py     # Exports command groups
│       ├── configure.py    # `cstool configure` command
│       ├── assets.py       # `cstool assets create` command
│       └── vaults.py       # `cstool vaults refresh` command
└── mobile_logs/            # Mobile log parsing package
    ├── __init__.py         # Package init
    ├── cli.py              # Standalone CLI (also integrated into cstool)
    ├── parser.py           # Log format parser (box-drawing format)
    ├── extractor.py        # Zip extraction and file discovery
    ├── filters.py          # Filter by level, module, time, text
    ├── redactor.py         # Sanitize sensitive data
    ├── datetime_utils.py   # Flexible datetime parsing (dateutil-based)
    ├── grouping.py         # Session grouping by time gaps
    └── commands/
        ├── __init__.py     # Exports commands
        ├── summary.py      # `logs-summary` - quick stats
        ├── errors.py       # `logs-errors` - show all errors (with session grouping)
        ├── search.py       # `logs-search` - search/filter (with session grouping)
        └── export.py       # `logs-export` - export to file (with session grouping)
```

---

## Data Flow

### Asset Creation Flow
```
User runs: cstool create-asset
    │
    ▼
cli.py → routes to assets.create()
    │
    ▼
assets.py → interactive prompts:
    1. select_blockchain() → returns blockchain type
    2. For most chains:
       - get_chain_for_blockchain() → returns network/chain
       - get_address_for_blockchain() → returns token address
       - build_payload() → calls appropriate builder
    3. For Aptos (special handling):
       - handle_aptos() → prompts for token type (coin/new_coin)
       - Then prompts for network and address based on type
    │
    ▼
api.py → create_asset() sends POST to /api/v1/assets/asset-infos
    │
    ▼
errors.py → handle_response() processes result
```

### Vault Refresh Flow
```
User runs: cstool refresh-vault
    │
    ▼
cli.py → routes to vaults.refresh()
    │
    ▼
vaults.py → prompts for:
    1. Vault IDs (count, then each ID)
    2. Asset IDs (optional)
    3. Single organization ID (required)
    4. Ephemeral bearer token (last, to minimize expiration risk)
    │
    ▼
refresh_assets() → sends POST to /api/v1/assets/refresh-owned-assets
    │
    ▼
handle_refresh_response() → processes result
```

### Mobile Logs Flow
```
User runs: cstool logs-search logs.zip -a "jan 15" -m AuthBloc
    │
    ▼
extractor.py → load_logs() extracts zip, finds flog*.txt files
    │
    ▼
parser.py → parse_file() yields LogEntry objects
    │
    ▼
datetime_utils.py → parse_datetime_filter() parses flexible date input
    │
    ▼
filters.py → filter_entries() applies level/module/search/time filters
    │
    ▼
grouping.py → group_by_sessions() clusters entries by time gaps
    │
    ▼
Display grouped results with session headers
```

---

## Current Commands

| Command | Alias | Auth | Key Options |
|---------|-------|------|-------------|
| `cstool configure` | — | — | — |
| `cstool assets create` | `cstool create-asset` | Stored API key | — |
| `cstool vaults refresh` | `cstool refresh-vault` | Ephemeral token | `-t`, `-v`, `-a`, `-o` |
| `cstool logs-summary` | — | — | — |
| `cstool logs-errors` | — | — | `--redact`, `--gap`, `-n` (limit) |
| `cstool logs-search` | — | — | `--after`, `--before`, `--group/--no-group`, `--gap` |
| `cstool logs-export` | — | — | `-o` (optional), `--after`, `--before`, `--group/--no-group`, `--gap`, `-f` (default: json) |

---

## API Endpoints

### Asset Creation
- **URL**: `{base_url}/api/v1/assets/asset-infos`
- **Method**: POST
- **Auth**: `Authorization: Bearer {api_key}` (from config)
- **Timeout**: 30s

### Vault Refresh  
- **URL**: `{base_url}/api/v1/assets/refresh-owned-assets`
- **Method**: POST
- **Auth**: `Authorization: Bearer {ephemeral_token}` (user-provided each time)
- **Timeout**: 30s
- **Payload**:
```json
{
  "vault_ids": ["uuid", ...],
  "asset_ids": ["uuid", ...],
  "organization_ids": ["uuid"]  // Single org ID in array (required)
}
```

---

## Mobile Logs Module

### Log Format

Fordefi mobile logs use a box-drawing format:
```
{"version":1,"sembast":1}
┌─────────────────────────────────────────────────────────
│ 💡 [2026-01-15 11:06:33.048] [ModuleName] Message here
└─────────────────────────────────────────────────────────
```

**Timestamp format:** `YYYY-MM-DD HH:MM:SS.mmm` (e.g., `2026-01-15 11:06:33.048`)

**Log levels:** `💡` (info), `⛔` (error)

**Modules:** AuthBloc, KeysStorage, VaultSigner, SyncBloc, GoSDK, MpcInvoker, etc.

### LogEntry Dataclass (parser.py)

```python
@dataclass
class LogEntry:
    timestamp: datetime
    level: str          # 'info' or 'error'
    icon: str           # 💡 or ⛔
    module: Optional[str]
    message: str
    raw: str
    file_source: str
    line_number: int
```

### Flexible Datetime Parsing (datetime_utils.py)

Supports multiple input formats for `--after` and `--before` filters:

| Format | Example | Notes |
|--------|---------|-------|
| ISO date | `2026-01-15` | Returns full day range |
| ISO datetime | `2026-01-15 10:30` | Exact time |
| Month-day | `01-15`, `1/15` | Assumes current year |
| Named month | `jan 15`, `january 15` | Assumes current year |
| With time | `jan 15 10pm` | Named month + time |

**Key functions:**
```python
# For filter boundaries (--after/--before)
parse_datetime_filter(input_str, filter_type='after'|'before') -> datetime

# For general parsing (returns start/end range)
parse_flexible_datetime(input_str) -> DateTimeParseResult
```

### Session Grouping (grouping.py)

Groups log entries into sessions based on time gaps between consecutive entries.

**Default gap threshold:** 300 seconds (5 minutes)

**Session dataclass:**
```python
@dataclass
class Session:
    entries: List[LogEntry]
    index: int  # 1-based session number
    
    # Properties:
    start_time: datetime
    end_time: datetime
    duration_seconds: float
    entry_count: int
    error_count: int
```

**Key functions:**
```python
# Group entries into sessions
group_by_sessions(entries, gap_threshold_seconds=300) -> List[Session]

# Format session header for display
format_session_header(session, width=70) -> str
# Returns: "━━━ Session 1 • Jan 15, 11:06 AM (47 entries, 3.2s) ━━━"

# Get aggregate stats
get_session_stats(sessions) -> dict
```

**Algorithm:**
1. Sort entries by timestamp
2. Iterate through entries
3. If gap between consecutive entries > threshold, start new session
4. Return list of Session objects

### Sensitive Data Redaction (redactor.py)

The `--redact` flag replaces:
- Email addresses → `[EMAIL]`
- UUIDs → `[UUID]`
- Firebase tokens → `[FCM_TOKEN]`
- Base64 encrypted keys → `[ENCRYPTED_KEY]`
- iOS paths → `[IOS_PATH]`

### Mobile Logs Commands

```bash
# Quick summary
cstool logs-summary logs.zip

# Show sessions containing errors (full session context)
cstool logs-errors logs.zip
cstool logs-errors logs.zip --redact
cstool logs-errors logs.zip --gap 60  # 1-minute sessions
cstool logs-errors logs.zip -n 5      # limit to 5 sessions

# Search with flexible dates and session grouping
cstool logs-search logs.zip -m AuthBloc
cstool logs-search logs.zip -a "jan 15" -b "jan 16"
cstool logs-search logs.zip -a "jan 15 10am" -b "jan 15 2pm"
cstool logs-search logs.zip --gap 120

# Export (auto-names: logs.zip → logs.json, JSON includes session metadata)
cstool logs-export logs.zip                    # exports to logs.json next to source
cstool logs-export logs.zip -f text            # exports to logs.txt
cstool logs-export logs.zip -o custom.json     # custom filename
cstool logs-export logs.zip --no-group         # disable session grouping
```

---

## Blockchain Configuration

### Network Selection Logic

| Blockchain | Network Source | Behavior |
|------------|----------------|----------|
| `evm` | Freeform input | User types network (e.g., `evm_1`, `evm_137`) |
| `solana`, `tron`, `sui`, `cosmos` | `NETWORKS` dict | User selects from numbered menu |
| `aptos` | `NETWORKS` dict | Special flow: prompts for token type (coin/new_coin) first, then network |
| `stacks`, `starknet`, `ton` | `SINGLE_NETWORKS` dict | Auto-selected, no prompt |
| `exchange` | N/A | User selects exchange from `EXCHANGES` list |

### Current Constants (constants.py)

```python
BLOCKCHAIN_TYPES = ["evm", "tron", "solana", "aptos", "cosmos", "stacks", "starknet", "sui", "ton", "exchange"]

DEFAULT_STANDARDS = {
    "evm": "erc20", "tron": "trc20", "solana": "spl_token", "aptos": "coin",
    "stacks": "sip10", "starknet": "erc20", "sui": "coin", "ton": "jetton", "cosmos": "token"
}

NETWORKS = {
    "solana": ["solana_mainnet", "solana_devnet", "solana_eclipse_mainnet", "solana_fogo_mainnet", "solana_fogo_testnet"],
    "tron": ["tron_mainnet", "tron_shasta"],
    "aptos": ["aptos_mainnet", "aptos_testnet", "aptos_movement_mainnet", "aptos_movement_testnet"],
    "sui": ["sui_mainnet", "sui_testnet"],
    "cosmos": ["cosmos_agoric-3", "cosmos_akashnet-2", ...]
}

SINGLE_NETWORKS = {"stacks": "stacks_mainnet", "starknet": "starknet_mainnet", "ton": "ton_mainnet"}

EXCHANGES = ["binance", "bybit", "coinbase_international", "coinbase_us", "okx", "kraken"]
```

---

## Modification Checklists

### To Add a New Command

1. **Create file**: `cs_tools/commands/newcmd.py`
2. **Export** from `commands/__init__.py`
3. **Register** in `cli.py` with `cli.add_command(newcmd)`
4. **Add alias** if needed: `cli.add_command(newcmd, name="my-alias")`

### To Add a Command Alias

```python
# In cli.py
from .commands.assets import assets, create as assets_create
cli.add_command(assets_create, name="create-asset")
```

### To Add Session Grouping to a New Logs Command

```python
from ..grouping import group_by_sessions, format_session_header, DEFAULT_GAP_THRESHOLD

@click.command()
@click.option('--group/--no-group', default=True)
@click.option('--gap', '-g', default=DEFAULT_GAP_THRESHOLD, type=float)
def mycommand(group: bool, gap: float):
    # ... get entries ...
    if group:
        sessions = group_by_sessions(entries, gap)
        for session in sessions:
            click.echo(format_session_header(session))
            for entry in session.entries:
                display_entry(entry)
```

### To Add Flexible Datetime Filters

```python
from ..datetime_utils import parse_datetime_filter

@click.option('--after', '-a', help='Flexible datetime (e.g., jan 15, 01-15 10:30)')
@click.option('--before', '-b', help='Flexible datetime')
def mycommand(after: str, before: str):
    if after:
        after_dt = parse_datetime_filter(after, 'after')
    if before:
        before_dt = parse_datetime_filter(before, 'before')
```

---

## Constraints & Rules

1. **No input validation** — let the API handle invalid inputs
2. **30s timeout** on all requests
3. **Ephemeral tokens** — `vaults refresh` requires user-provided token each time
4. **Config permissions** — always set 0600 on config.yaml
5. **Alias naming** — use kebab-case (`create-asset`, `logs-summary`)
6. **Documentation** — update all THREE docs for any code change
7. **Session grouping** — enabled by default, threshold is 300 seconds (5 minutes)
8. **Datetime parsing** — date-only inputs return full day range
9. **Export defaults** — output filename auto-generated from source name (e.g., `logs.zip` → `logs.json`), default format is JSON

---

## Testing After Changes

```bash
# Reinstall
pipx install /path/to/CS_Tool --force

# Verify
cstool --help
cstool create-asset
cstool refresh-vault
cstool logs-summary /path/to/logs.zip

# Test datetime and session features
cstool logs-search logs.zip -a "jan 15" -b "jan 16"
cstool logs-search logs.zip -a "jan 15 10am" -b "jan 15 2pm"
cstool logs-errors logs.zip              # shows full sessions with errors
cstool logs-errors logs.zip -n 3         # limit to 3 sessions
cstool logs-export logs.zip              # auto-generates logs.json
cstool logs-export logs.zip -f text      # auto-generates logs.txt
cstool logs-export logs.zip --no-group   # without session grouping
```

---

## JSON Export Format (with session grouping)

When exporting with `--format json` and `--group` (default):

```json
{
  "sessions": [
    {
      "session_number": 1,
      "start_time": "2026-01-15T11:06:33.048000",
      "end_time": "2026-01-15T11:06:36.207000",
      "duration_seconds": 3.159,
      "entry_count": 47,
      "error_count": 2,
      "entries": [
        {
          "timestamp": "2026-01-15T11:06:33.048000",
          "level": "info",
          "module": "KeysStorage",
          "message": "...",
          "file": "flog0.txt",
          "line": 5
        }
      ]
    }
  ],
  "stats": {
    "session_count": 3,
    "total_entries": 125,
    "total_errors": 5,
    "total_duration_seconds": 47.2,
    "avg_session_duration_seconds": 15.7,
    "avg_entries_per_session": 41.7
  }
}
```

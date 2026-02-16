# cstool

A command-line interface tool for interacting with the Fordefi API.

## Installation

First, clone the repository:

```bash
git clone https://github.com/Fordefi-Ben/cli-toolkit.git
cd CS_Tool
```

### macOS (Recommended)

On macOS with Homebrew, use `pipx` to install the tool globally:

```bash
# Install pipx if you haven't already
brew install pipx

# Install cstool
pipx install .
```

This installs `cstool` in an isolated environment and makes it available system-wide.

To update after making code changes:

```bash
pipx install /path/to/CS_Tool --force
```

To uninstall:

```bash
pipx uninstall cs-tools
```

### Using a Virtual Environment

If you prefer using a virtual environment:

```bash
cd CS_Tool
python3 -m venv venv
source venv/bin/activate
pip install -e .
```

You'll need to activate the venv each time you open a new terminal:

```bash
source /path/to/CS_Tool/venv/bin/activate
```

### Direct pip Install (Linux / Other Systems)

On systems that allow direct pip installs:

```bash
cd CS_Tool
pip install -e .
```

## Setup

Before using the tool, configure your API key:

```bash
cstool configure
```

You will be prompted to enter:
- **API Key**: Your Fordefi API key (must be a TRADER key, not a viewer key)
- **API Base URL**: The Fordefi API base URL (default: https://api.fordefi.com)

Configuration is stored in `~/.cs_tools/config.yaml` with secure permissions (0600).

> **Security note:** Your API key is stored in plaintext in the config file. The file is protected with owner-only permissions (0600), but avoid sharing or backing up your `~/.cs_tools/` directory. You can use the environment variable method below to avoid storing the key on disk entirely.

### Environment Variable Override

You can override the API key using an environment variable:

```bash
export CS_TOOLS_API_KEY="your-api-key-here"
```

## Usage

### Create an Asset

Run the interactive asset creation wizard:

```bash
cstool create-asset
```

Or use the full command:

```bash
cstool assets create
```

You will be guided through:
1. Selecting a blockchain type (EVM, TRON, Solana, Aptos, Cosmos, Stacks, Starknet, Sui, Ton, or Exchange)
2. Selecting or entering a network (chain-specific)
3. Entering the token address or identifier

### Refresh Vault Assets

Trigger a refresh of owned assets for vaults:

```bash
cstool refresh-vault
```

Or use the full command:

```bash
cstool vaults refresh
```

**Note:** This endpoint requires an **ephemeral bearer token**, not your regular API key. You will be prompted to enter it.

You will be guided through:
1. Specifying the number of vault IDs to enter (then entering each one)
2. Specifying the number of asset IDs to enter (optional)
3. Entering the organization ID (required)
4. Entering your ephemeral bearer token

**Non-interactive usage:**

```bash
# Single vault
cstool refresh-vault -t "your-ephemeral-token" -v vault-id

# Multiple vaults
cstool refresh-vault -t "your-ephemeral-token" -v vault-id-1 -v vault-id-2

# With asset and organization filter
cstool refresh-vault -t "your-ephemeral-token" -v vault-id -a asset-id -o org-id
```

## Mobile Logs Analysis

Analyze Fordefi mobile app diagnostic logs:

```bash
# Quick summary (device info, app version, error count)
cstool logs-summary logs.zip

# View sessions containing errors (shows full session context)
cstool logs-errors logs.zip
cstool logs-errors logs.zip --redact       # redact sensitive data
cstool logs-errors logs.zip --gap 60       # 1-minute session threshold
cstool logs-errors logs.zip -n 5           # limit to 5 sessions

# Search logs (grouped by session)
cstool logs-search logs.zip "token"        # text search
cstool logs-search logs.zip -m AuthBloc    # by module
cstool logs-search logs.zip -l error       # by level

# Export logs (auto-names based on source: logs.zip → logs.json)
cstool logs-export logs.zip                    # exports to logs.json
cstool logs-export logs.zip -f text            # exports to logs.txt  
cstool logs-export logs.zip -o custom.json     # custom filename
cstool logs-export logs.zip -l error --redact  # filtered + redacted
```

The `--redact` flag sanitizes sensitive data (emails, UUIDs, tokens) before output.

### Flexible Date/Time Filtering

The `logs-search` and `logs-export` commands support flexible date/time formats for the `--after` and `--before` options:

| Format | Example | Description |
|--------|---------|-------------|
| ISO date | `2026-01-15` | Full date |
| ISO datetime | `2026-01-15 10:30` | Date with time |
| Month-day | `01-15` or `1/15` | Assumes current year |
| Named month | `jan 15` or `january 15` | Assumes current year |
| With time | `jan 15 10pm` | Named month with time |

```bash
# Filter by date range
cstool logs-search logs.zip -a "jan 15" -b "jan 16"

# Filter by specific time window
cstool logs-search logs.zip -a "jan 15 10am" -b "jan 15 2pm"

# Export a specific day
cstool logs-export logs.zip -o jan15.txt -a "01-15" -b "01-16"
```

### Session Grouping

Log entries are automatically grouped into "sessions" based on time gaps between consecutive entries. By default, a new session starts when there's a gap of more than 5 minutes (300 seconds) between entries.

This makes it easier to identify distinct user activity periods in the logs:

```
━━━ Session 1 • Jan 15, 11:06 AM (23 entries, 3.1s) ━━━━━━━━━━━━━━━━━━━━━

⛔ 11:06:36.168 [generateRoute] ...
💡 11:06:36.175 [VaultSigner] ...

━━━ Session 2 • Jan 15, 11:45 AM (8 entries, 1.2s) ━━━━━━━━━━━━━━━━━━━━━━

⛔ 11:45:22.001 [AuthBloc] ...
```

**Session grouping options:**

```bash
# Disable session grouping
cstool logs-search logs.zip --no-group

# Custom gap threshold (e.g., 60 seconds)
cstool logs-search logs.zip --gap 60

# Works with errors and export too
cstool logs-export logs.zip --gap 120
cstool logs-export logs.zip                      # JSON includes session metadata
```

## Example Workflows

### Create an EVM (Ethereum) ERC20 Token

```
$ cstool create-asset
Select blockchain:
  1) EVM
  ...
> 1
Enter network (e.g., evm_1, evm_137): evm_1
Enter token address (hex): 0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48
Creating asset...
✅ Asset created successfully!
```

### Create a Solana SPL Token

```
$ cstool create-asset
Select blockchain:
  ...
  3) Solana
  ...
> 3
Select network:
  1) solana_mainnet
  2) solana_devnet
  ...
> 1
Enter token address (base58): EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v
Creating asset...
✅ Asset created successfully!
```

### Create an Exchange Asset

```
$ cstool create-asset
Select blockchain:
  ...
  10) Exchange
> 10
Select exchange:
  1) binance
  2) bybit
  ...
> 1
Enter asset symbol: USDT
Creating asset...
✅ Asset created successfully!
```

### Refresh Vault Assets

```
$ cstool refresh-vault

Refresh Vault Assets

How many vault IDs do you want to enter? [0]: 1
  Vault ID 1/1: 33bd9c1d-9908-4813-9963-753dce4b81e1

How many asset IDs do you want to enter? [0]: 0

Enter organization ID: abc123-org-id-here

Note: This endpoint requires an ephemeral bearer token, not your regular API key.

Enter ephemeral bearer token: [hidden]

Refreshing with payload:
{
  "vault_ids": ["33bd9c1d-9908-4813-9963-753dce4b81e1"]
}

Sending request...

✅ Refresh triggered successfully!
```

### Analyze Mobile Logs

```
$ cstool logs-errors logs.zip

⛔ Found 3 error(s) in 2 session(s)

━━━ Session 1 • Jan 14, 8:35 AM (47 entries, 12.3s, 2 errors) ━━━━━━━━━━

💡 08:35:17.505 [GoSDK] nativePort 1234572493260759 postCObject 4373816240
💡 08:35:17.520 INITIALIZE APPLICATION Version: v1.100.0.8...
💡 08:35:17.535 Fetching user record
⛔ 08:35:17.773 [generateRoute] generateRoute [name / , args: {approvalId: null...
💡 08:35:17.831 [VaultSigner] All Entries In Vault Keychain:
...
⛔ 08:35:29.445 [SyncBloc] can't sync - auth state=AuthPhase.processing...

━━━ Session 2 • Jan 15, 11:06 AM (23 entries, 3.2s, 1 error) ━━━━━━━━━━━

💡 11:06:33.048 Loaded 17 invite records into memory
💡 11:06:33.049 [KeysStorage] Init SecureStorageImpl
...
⛔ 11:06:36.168 [generateRoute] generateRoute [name / , args: {approvalId: null...
💡 11:06:36.175 [VaultSigner] All Entries In Vault Keychain:
```

## Supported Blockchains

| Blockchain | Token Standard | Address Format |
|------------|---------------|----------------|
| EVM | ERC20 | Hex (0x...) |
| TRON | TRC20 | Base58 (T...) |
| Solana | SPL Token | Base58 |
| Aptos | Coin / New Coin | Coin type string / Hex address |
| Cosmos | Token | Denom string |
| Stacks | SIP10 | Hex (S...) |
| Starknet | ERC20 | Hex (0x...) |
| Sui | Coin | Coin type string |
| Ton | Jetton | Address (-0:...) |
| Exchange | N/A | Symbol |

## Team Distribution

To distribute to your team:

1. Share the project folder
2. Have team members install using one of the methods above:

   **macOS (recommended):**
   ```bash
   brew install pipx
   pipx install /path/to/CS_Tool
   cstool configure
   ```

   **Virtual environment:**
   ```bash
   cd CS_Tool
   python3 -m venv venv
   source venv/bin/activate
   pip install -e .
   cstool configure
   ```

## Troubleshooting

### 401 Unauthorized
- Check that your API key is correct
- Ensure you're using a **TRADER** key, not a viewer key
- For `vaults refresh`: Make sure you're using an ephemeral bearer token

### 403 Forbidden
- Your API key may not have sufficient permissions
- Contact your admin to get a TRADER key

### 404 Not Found
- Double-check the token address and chain/network

### 422 Validation Error
- The API returned validation errors - check the error details for specifics

## License

Internal tool - not for public distribution.

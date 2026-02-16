"""Assets commands for CS_Tools CLI."""

import click

from ..constants import (
    BLOCKCHAIN_TYPES,
    NETWORKS,
    SINGLE_NETWORKS,
    EXCHANGES,
)
from ..payloads import (
    build_evm_payload,
    build_tron_payload,
    build_solana_payload,
    build_aptos_payload,
    build_aptos_new_coin_payload,
    build_cosmos_payload,
    build_stacks_payload,
    build_starknet_payload,
    build_sui_payload,
    build_ton_payload,
    build_exchange_payload,
)
from ..api import create_asset
from ..config import is_configured


@click.group()
def assets():
    """Asset management commands."""
    pass


@assets.command()
def create():
    """Create a new asset interactively."""
    # Check if configured
    if not is_configured():
        click.echo(click.style("❌ Not configured", fg="red", bold=True))
        click.echo("Please run 'cs_tools configure' first to set up your API key.")
        return
    
    click.echo(click.style("Create Asset", fg="cyan", bold=True))
    click.echo()
    
    # Step 1: Select blockchain type
    blockchain = select_blockchain()
    if not blockchain:
        return
    
    # Step 2: Handle based on blockchain type
    if blockchain == "exchange":
        handle_exchange()
    else:
        handle_blockchain(blockchain)


def select_blockchain() -> str:
    """Display blockchain selection menu and return choice."""
    click.echo("Select blockchain:")
    
    for i, chain in enumerate(BLOCKCHAIN_TYPES, 1):
        display_name = chain.upper() if chain != "exchange" else "Exchange"
        click.echo(f"  {i}) {display_name}")
    
    click.echo()
    
    while True:
        choice = click.prompt("Enter choice", type=int)
        
        if 1 <= choice <= len(BLOCKCHAIN_TYPES):
            return BLOCKCHAIN_TYPES[choice - 1]
        else:
            click.echo(click.style(f"Invalid choice. Enter 1-{len(BLOCKCHAIN_TYPES)}.", fg="yellow"))


def select_from_list(items: list, prompt_text: str) -> str:
    """Display a numbered menu and return the selected item."""
    click.echo(f"{prompt_text}:")
    
    for i, item in enumerate(items, 1):
        click.echo(f"  {i}) {item}")
    
    click.echo()
    
    while True:
        choice = click.prompt("Enter choice", type=int)
        
        if 1 <= choice <= len(items):
            return items[choice - 1]
        else:
            click.echo(click.style(f"Invalid choice. Enter 1-{len(items)}.", fg="yellow"))


def handle_exchange():
    """Handle exchange asset creation."""
    click.echo()
    
    # Select exchange
    exchange = select_from_list(EXCHANGES, "Select exchange")
    click.echo()
    
    # Get asset symbol
    symbol = click.prompt("Enter asset symbol")
    
    # Build and send
    click.echo()
    click.echo("Creating asset...")
    click.echo()
    
    payload = build_exchange_payload(exchange, symbol)
    create_asset(payload)


def handle_blockchain(blockchain: str):
    """Handle blockchain asset creation."""
    click.echo()
    
    # Special handling for Aptos (has multiple token types)
    if blockchain == "aptos":
        handle_aptos()
        return
    
    # Get network/chain
    chain = get_chain_for_blockchain(blockchain)
    click.echo()
    
    # Get address/identifier based on blockchain type
    address = get_address_for_blockchain(blockchain)
    
    # Build and send
    click.echo()
    click.echo("Creating asset...")
    click.echo()
    
    payload = build_payload(blockchain, chain, address)
    create_asset(payload)


APTOS_TOKEN_TYPES = ["coin", "new_coin (fungible asset)"]


def handle_aptos():
    """Handle Aptos asset creation with token type selection."""
    # Select token type
    token_type_choice = select_from_list(APTOS_TOKEN_TYPES, "Select token type")
    click.echo()
    
    # Get network
    chain = select_from_list(NETWORKS["aptos"], "Select network")
    click.echo()
    
    if token_type_choice == "coin":
        # Original coin type - uses coin_type_str
        coin_type = click.prompt("Enter coin type (e.g., 0x...::asset::USDC)")
        payload = build_aptos_payload(chain, coin_type)
    else:
        # New coin (fungible asset) - uses metadata_address
        metadata_address = click.prompt("Enter metadata address (hex)")
        payload = build_aptos_new_coin_payload(chain, metadata_address)
    
    # Build and send
    click.echo()
    click.echo("Creating asset...")
    click.echo()
    
    create_asset(payload)


def get_chain_for_blockchain(blockchain: str) -> str:
    """Get the chain/network for a blockchain type."""
    # Check if it's a single-network blockchain
    if blockchain in SINGLE_NETWORKS:
        chain = SINGLE_NETWORKS[blockchain]
        click.echo(f"Using network: {chain}")
        return chain
    
    # Check if it has a list of networks
    if blockchain in NETWORKS:
        return select_from_list(NETWORKS[blockchain], "Select network")
    
    # EVM is freeform input
    if blockchain == "evm":
        return click.prompt("Enter network (e.g., evm_1, evm_137)")
    
    # Default fallback (shouldn't reach here)
    return click.prompt("Enter network")


def get_address_for_blockchain(blockchain: str) -> str:
    """Get the address/identifier prompt based on blockchain type."""
    prompts = {
        "evm": "Enter token address (hex)",
        "tron": "Enter token address (base58)",
        "solana": "Enter token address (base58)",
        "aptos": "Enter coin type (e.g., 0x...::asset::USDC)",
        "cosmos": "Enter denom (e.g., uatom)",
        "stacks": "Enter contract address (hex)",
        "starknet": "Enter token address (hex)",
        "sui": "Enter coin type",
        "ton": "Enter jetton address (e.g., -0:...)",
    }
    
    prompt_text = prompts.get(blockchain, "Enter address")
    return click.prompt(prompt_text)


def build_payload(blockchain: str, chain: str, address: str) -> dict:
    """Build the appropriate payload for the blockchain type."""
    builders = {
        "evm": build_evm_payload,
        "tron": build_tron_payload,
        "solana": build_solana_payload,
        "aptos": build_aptos_payload,
        "cosmos": build_cosmos_payload,
        "stacks": build_stacks_payload,
        "starknet": build_starknet_payload,
        "sui": build_sui_payload,
        "ton": build_ton_payload,
    }
    
    builder = builders.get(blockchain)
    if builder:
        return builder(chain, address)
    
    # Shouldn't reach here
    raise ValueError(f"Unknown blockchain type: {blockchain}")

"""Constants for CS_Tools CLI."""

BLOCKCHAIN_TYPES = [
    "evm",
    "tron",
    "solana",
    "aptos",
    "cosmos",
    "stacks",
    "starknet",
    "sui",
    "ton",
    "exchange",
]

DEFAULT_STANDARDS = {
    "evm": "erc20",
    "tron": "trc20",
    "solana": "spl_token",
    "aptos": "coin",
    "stacks": "sip10",
    "starknet": "erc20",
    "sui": "coin",
    "ton": "jetton",
    "cosmos": "token",
}

NETWORKS = {
    "solana": [
        "solana_mainnet",
        "solana_devnet",
        "solana_eclipse_mainnet",
        "solana_fogo_mainnet",
        "solana_fogo_testnet",
    ],
    "tron": [
        "tron_mainnet",
        "tron_shasta",
    ],
    "aptos": [
        "aptos_mainnet",
        "aptos_testnet",
        "aptos_movement_mainnet",
        "aptos_movement_testnet",
    ],
    "sui": [
        "sui_mainnet",
        "sui_testnet",
    ],
    "cosmos": [
        "cosmos_agoric-3",
        "cosmos_akashnet-2",
        "cosmos_archway-1",
        "cosmos_axelar-dojo-1",
        "cosmos_bbn-1",
        "cosmos_celestia",
        "cosmos_cosmoshub-4",
        "cosmos_dydx-mainnet-1",
        "cosmos_dydx-testnet-4",
        "cosmos_dymension_1100-1",
        "cosmos_injective-1",
        "cosmos_neutron-1",
        "cosmos_nillion-1",
        "cosmos_noble-1",
        "cosmos_osmosis-1",
        "cosmos_ssc-1",
        "cosmos_pacific-1",
        "cosmos_stride-1",
        "cosmos_thorchain-1",
        "cosmos_mantra-1",
    ],
}

SINGLE_NETWORKS = {
    "stacks": "stacks_mainnet",
    "starknet": "starknet_mainnet",
    "ton": "ton_mainnet",
}

EXCHANGES = [
    "binance",
    "bybit",
    "coinbase_international",
    "coinbase_us",
    "okx",
    "kraken",
]

"""Payload builders for CS_Tools CLI."""

from typing import Dict, Any


def build_evm_payload(chain: str, address: str) -> Dict[str, Any]:
    """Build payload for EVM ERC20 token."""
    return {
        "asset_identifier": {
            "type": "evm",
            "details": {
                "type": "erc20",
                "token": {
                    "chain": chain,
                    "hex_repr": address
                }
            }
        }
    }


def build_tron_payload(chain: str, address: str) -> Dict[str, Any]:
    """Build payload for TRON TRC20 token."""
    return {
        "asset_identifier": {
            "type": "tron",
            "details": {
                "type": "trc20",
                "chain": chain,
                "trc20": {
                    "chain": chain,
                    "base58_repr": address
                }
            }
        }
    }


def build_solana_payload(chain: str, address: str) -> Dict[str, Any]:
    """Build payload for Solana SPL token."""
    return {
        "asset_identifier": {
            "type": "solana",
            "details": {
                "type": "spl_token",
                "chain": chain,
                "token": {
                    "chain": chain,
                    "base58_repr": address
                }
            }
        }
    }


def build_aptos_payload(chain: str, coin_type: str) -> Dict[str, Any]:
    """Build payload for Aptos Coin."""
    return {
        "asset_identifier": {
            "type": "aptos",
            "details": {
                "type": "coin",
                "coin_type": {
                    "chain": chain,
                    "coin_type_str": coin_type
                }
            }
        }
    }


def build_aptos_new_coin_payload(chain: str, metadata_address: str) -> Dict[str, Any]:
    """Build payload for Aptos New Coin (fungible asset)."""
    return {
        "asset_identifier": {
            "type": "aptos",
            "details": {
                "type": "new_coin",
                "new_coin_type": {
                    "chain": chain,
                    "metadata_address": metadata_address
                }
            }
        }
    }


def build_cosmos_payload(chain: str, denom: str) -> Dict[str, Any]:
    """Build payload for Cosmos Token."""
    return {
        "asset_identifier": {
            "type": "cosmos",
            "details": {
                "type": "token",
                "chain": chain,
                "denom": denom
            }
        }
    }


def build_stacks_payload(chain: str, address: str) -> Dict[str, Any]:
    """Build payload for Stacks SIP10 token."""
    return {
        "asset_identifier": {
            "type": "stacks",
            "details": {
                "type": "sip10",
                "sip10": {
                    "chain": chain,
                    "hex_repr": address
                }
            }
        }
    }


def build_starknet_payload(chain: str, address: str) -> Dict[str, Any]:
    """Build payload for Starknet ERC20 token."""
    return {
        "asset_identifier": {
            "type": "starknet",
            "details": {
                "type": "erc20",
                "erc20": {
                    "chain": chain,
                    "hex_repr": address
                }
            }
        }
    }


def build_sui_payload(chain: str, coin_type: str) -> Dict[str, Any]:
    """Build payload for Sui Coin."""
    return {
        "asset_identifier": {
            "type": "sui",
            "details": {
                "type": "coin",
                "coin_type": {
                    "chain": chain,
                    "coin_type_str": coin_type
                }
            }
        }
    }


def build_ton_payload(chain: str, address: str) -> Dict[str, Any]:
    """Build payload for Ton Jetton."""
    return {
        "asset_identifier": {
            "type": "ton",
            "details": {
                "type": "jetton",
                "jetton": {
                    "chain": chain,
                    "address": address
                }
            }
        }
    }


def build_exchange_payload(exchange: str, symbol: str) -> Dict[str, Any]:
    """Build payload for Exchange asset."""
    return {
        "asset_identifier": {
            "type": "exchange",
            "exchange_type": exchange,
            "asset_symbol": symbol
        }
    }

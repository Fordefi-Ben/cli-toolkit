"""Configuration management for CS_Tools CLI."""

import os
from pathlib import Path
from typing import Optional

import yaml


CONFIG_DIR = Path.home() / ".cs_tools"
CONFIG_FILE = CONFIG_DIR / "config.yaml"
API_BASE_URL = "https://api.fordefi.com"
ENV_API_KEY = "CS_TOOLS_API_KEY"


def ensure_config_dir() -> None:
    """Create config directory if it doesn't exist."""
    CONFIG_DIR.mkdir(mode=0o700, exist_ok=True)


def load_config() -> dict:
    """Load configuration from file."""
    if not CONFIG_FILE.exists():
        return {}
    
    with open(CONFIG_FILE, "r") as f:
        return yaml.safe_load(f) or {}


def save_config(config: dict) -> None:
    """Save configuration to file with secure permissions."""
    ensure_config_dir()
    
    with open(CONFIG_FILE, "w") as f:
        yaml.dump(config, f, default_flow_style=False)
    
    # Set file permissions to 0600 (owner read/write only)
    os.chmod(CONFIG_FILE, 0o600)


def get_api_key() -> Optional[str]:
    """Get API key from environment variable or config file.
    
    Environment variable takes precedence over config file.
    """
    # Check environment variable first
    env_key = os.environ.get(ENV_API_KEY)
    if env_key:
        return env_key
    
    # Fall back to config file
    config = load_config()
    return config.get("api_key")


def get_api_base_url() -> str:
    """Get the Fordefi API base URL."""
    return API_BASE_URL


def is_configured() -> bool:
    """Check if the tool has been configured with an API key."""
    return get_api_key() is not None

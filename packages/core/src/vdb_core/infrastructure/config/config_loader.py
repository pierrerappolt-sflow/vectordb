"""Configuration loader for VDB infrastructure."""

import os
from pathlib import Path

import yaml

from .config_models import AppConfig


def find_config_file() -> Path:
    """Find config.yaml in the project root.

    Searches upward from current directory until finding config.yaml.

    Returns:
        Path to config.yaml

    Raises:
        FileNotFoundError: If config.yaml not found

    """
    # Start from current directory
    current = Path.cwd()

    # Search upward through parent directories
    while current != current.parent:
        config_path = current / "config.yaml"
        if config_path.exists():
            return config_path
        current = current.parent

    # Check root directory
    config_path = current / "config.yaml"
    if config_path.exists():
        return config_path

    msg = "config.yaml not found in project root or any parent directory"
    raise FileNotFoundError(msg)


def load_config(config_path: str | Path | None = None) -> AppConfig:
    """Load configuration from YAML file.

    Args:
        config_path: Optional path to config file. If None, searches for config.yaml
                    in project root. Can also be set via VDB_CONFIG_PATH env var.

    Returns:
        Loaded and validated configuration

    Raises:
        FileNotFoundError: If config file not found
        yaml.YAMLError: If config file is invalid YAML
        pydantic.ValidationError: If config doesn't match schema

    Example:
        >>> config = load_config()
        >>> config.get_storage_type()
        StorageType.INMEMORY

    """
    # Check environment variable first
    if config_path is None:
        env_path = os.getenv("VDB_CONFIG_PATH")
        if env_path:
            config_path = Path(env_path)

    # If still None, search for config.yaml
    config_path = find_config_file() if config_path is None else Path(config_path)

    # Verify file exists
    if not config_path.exists():
        msg = f"Config file not found: {config_path}"
        raise FileNotFoundError(msg)

    # Load and parse YAML
    with open(config_path) as f:
        config_dict = yaml.safe_load(f)

    # Merge environment variables
    database_url = os.getenv("DATABASE_URL")
    if database_url:
        # Set storage database_url if not already set
        if "infrastructure" not in config_dict:
            config_dict["infrastructure"] = {}
        if "storage" not in config_dict["infrastructure"]:
            config_dict["infrastructure"]["storage"] = {}
        if "database_url" not in config_dict["infrastructure"]["storage"]:
            config_dict["infrastructure"]["storage"]["database_url"] = database_url

        # Set read_models database_url if not already set
        if "read_models" not in config_dict["infrastructure"]:
            config_dict["infrastructure"]["read_models"] = {}
        if "database_url" not in config_dict["infrastructure"]["read_models"]:
            config_dict["infrastructure"]["read_models"]["database_url"] = database_url

    # Validate and return
    return AppConfig(**config_dict)


def load_config_or_default() -> AppConfig:
    """Load configuration or return default if config.yaml not found.

    Returns:
        Loaded configuration or default AppConfig with inmemory backends

    """
    try:
        return load_config()
    except FileNotFoundError:
        # Return default config (all inmemory)
        return AppConfig()

"""knobs - Configuration Management.

Unified configuration system with typed settings, validation, and persistence.
Stores configuration as JSON files in product data directories.

Example:
    >>> from wickit import knobs
    >>> config = knobs.get_config("myapp")
    >>> config.ai.engine = "ollama"
    >>> knobs.save_config("myapp", config)

Classes:
    Config: Main configuration container with sync and AI settings.
    AIConfig: AI-specific settings (engine, model, timeout, retry).
    SyncConfig: Sync settings (provider, auto-sync, debounce).

Functions:
    get_config: Load configuration from file.
    save_config: Save configuration to file.
    get_ai_config: Get AI configuration.
    set_ai_config: Set AI configuration.
    get_sync_provider: Get sync provider.
    set_sync_provider: Set sync provider.
"""

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional

from .hideaway import get_config_path, ensure_data_dir


@dataclass
class AIConfig:
    """AI configuration for a product."""
    engine: str = "ollama"
    model: str = "llama3.2"
    timeout: int = 300
    retry_count: int = 3
    retry_delay: int = 5


@dataclass
class SyncConfig:
    """Sync configuration for a product."""
    provider: str = "none"
    local_folder: Optional[Path] = None
    auto_sync: bool = False
    debounce_seconds: float = 2.0
    access_token: str = ""


@dataclass
class Config:
    """Shared configuration for all products."""
    version: str = "1.0"
    project: str = ""
    sync: SyncConfig = field(default_factory=SyncConfig)
    ai: AIConfig = field(default_factory=AIConfig)


def get_config(product_name: str) -> Config:
    """Load configuration for a product."""
    config_path = get_config_path(product_name)

    if not config_path.exists():
        return Config(project=product_name)

    try:
        with open(config_path) as f:
            data = json.load(f)
    except (json.JSONDecodeError, IOError):
        return Config(project=product_name)

    config = Config(
        version=data.get("version", "1.0"),
        project=data.get("project", product_name),
    )

    if data.get("sync") and isinstance(data["sync"], dict):
        sync_data = data["sync"]
        config.sync = SyncConfig(
            provider=sync_data.get("provider", "none"),
            local_folder=Path(sync_data["local_folder"]) if sync_data.get("local_folder") else None,
            auto_sync=sync_data.get("auto_sync", False),
            debounce_seconds=sync_data.get("debounce_seconds", 2.0),
            access_token=sync_data.get("access_token", ""),
        )

    if data.get("ai") and isinstance(data["ai"], dict):
        ai_data = data["ai"]
        config.ai = AIConfig(
            engine=ai_data.get("engine", "ollama"),
            model=ai_data.get("model", "llama3.2"),
            timeout=ai_data.get("timeout", 300),
            retry_count=ai_data.get("retry_count", 3),
            retry_delay=ai_data.get("retry_delay", 5),
        )

    return config


def save_config(product_name: str, config: Config) -> None:
    """Save configuration for a product."""
    ensure_data_dir(product_name)
    config_path = get_config_path(product_name)

    data: dict[str, Any] = {
        "version": config.version,
        "project": config.project,
        "sync": {
            "provider": config.sync.provider,
            "local_folder": str(config.sync.local_folder) if config.sync.local_folder else None,
            "auto_sync": config.sync.auto_sync,
            "debounce_seconds": config.sync.debounce_seconds,
            "access_token": config.sync.access_token,
        },
        "ai": {
            "engine": config.ai.engine,
            "model": config.ai.model,
            "timeout": config.ai.timeout,
            "retry_count": config.ai.retry_count,
            "retry_delay": config.ai.retry_delay,
        },
    }

    with open(config_path, "w") as f:
        json.dump(data, f, indent=2)


def get_sync_provider(product_name: str) -> str:
    """Get the sync provider for a product."""
    config = get_config(product_name)
    return config.sync.provider


def set_sync_provider(product_name: str, provider: str) -> None:
    """Set the sync provider for a product."""
    config = get_config(product_name)
    config.sync.provider = provider
    save_config(product_name, config)


def get_ai_config(product_name: str) -> AIConfig:
    """Get AI configuration for a product."""
    config = get_config(product_name)
    return config.ai


def set_ai_config(product_name: str, ai_config: AIConfig) -> None:
    """Set AI configuration for a product."""
    config = get_config(product_name)
    config.ai = ai_config
    save_config(product_name, config)

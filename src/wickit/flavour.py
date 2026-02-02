"""
wickit.flavour - Environment Management and Self-Identification

Provides environment detection, configuration, and self-identification for wickit-based applications.

Environments: prod, dev, stage, local, mock (extensible for custom environments)

Usage:
    from wickit.flavour import get_environment, Environment
    
    # Get current environment
    env = get_environment()
    print(f"Running in: {env.name}")  # "dev", "prod", etc.
    
    # Check environment type
    if env.is_production:
        # Enable strict logging, error reporting
        pass
    
    # Get environment-specific config
    config = env.get_config()
    db_url = config.get("database", {}).get("url")
"""

import os
import json
from enum import Enum, auto
from pathlib import Path
from typing import Dict, Any, Optional, Callable
from dataclasses import dataclass, field


class EnvironmentType(Enum):
    """Standard environment types."""
    PRODUCTION = auto()
    DEVELOPMENT = auto()
    STAGING = auto()
    LOCAL = auto()
    MOCK = auto()
    TEST = auto()
    
    # Allow custom environments
    CUSTOM = auto()


@dataclass
class Environment:
    """Represents an application environment."""
    name: str
    type: EnvironmentType
    is_production: bool = False
    is_development: bool = False
    is_staging: bool = False
    is_local: bool = False
    is_mock: bool = False
    is_test: bool = False
    config_overrides: Dict[str, Any] = field(default_factory=dict)
    parent: Optional['Environment'] = None
    
    def __post_init__(self):
        """Set flags based on type."""
        if self.type == EnvironmentType.PRODUCTION:
            self.is_production = True
        elif self.type == EnvironmentType.DEVELOPMENT:
            self.is_development = True
        elif self.type == EnvironmentType.STAGING:
            self.is_staging = True
        elif self.type == EnvironmentType.LOCAL:
            self.is_local = True
        elif self.type == EnvironmentType.MOCK:
            self.is_mock = True
        elif self.type == EnvironmentType.TEST:
            self.is_test = True
    
    def get_config(self, product_name: str) -> Dict[str, Any]:
        """
        Get environment-specific configuration.
        
        Loads config from:
        1. Base config (config.json)
        2. Environment config (config.{env}.json)
        3. Environment variables (WICKIT_*)
        4. Runtime overrides
        
        Args:
            product_name: Name of the product (e.g., "ralfiepretzel")
            
        Returns:
            Merged configuration dictionary
        """
        from wickit.hideaway import get_config_path
        
        config = {}
        
        # 1. Load base config
        base_config_path = get_config_path(product_name)
        if base_config_path.exists():
            with open(base_config_path) as f:
                config = json.load(f)
        
        # 2. Load environment-specific config
        env_config_path = base_config_path.parent / f"config.{self.name}.json"
        if env_config_path.exists():
            with open(env_config_path) as f:
                env_config = json.load(f)
                # Deep merge
                config = self._deep_merge(config, env_config)
        
        # 3. Apply environment variables (WICKIT_*)
        config = self._apply_env_vars(config)
        
        # 4. Apply runtime overrides
        config = self._deep_merge(config, self.config_overrides)
        
        return config
    
    def _deep_merge(self, base: Dict, override: Dict) -> Dict:
        """Deep merge two dictionaries."""
        result = base.copy()
        for key, value in override.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._deep_merge(result[key], value)
            else:
                result[key] = value
        return result
    
    def _apply_env_vars(self, config: Dict) -> Dict:
        """Apply WICKIT_* environment variables to config."""
        result = config.copy()
        
        for key, value in os.environ.items():
            if key.startswith("WICKIT_"):
                # WICKIT_DATABASE_URL -> config["database"]["url"]
                config_key = key[7:].lower().replace("__", ".")
                self._set_nested_value(result, config_key, value)
        
        return result
    
    def _set_nested_value(self, config: Dict, key: str, value: Any):
        """Set a nested value in config using dot notation."""
        parts = key.split(".")
        current = config
        for part in parts[:-1]:
            if part not in current:
                current[part] = {}
            current = current[part]
        current[parts[-1]] = value
    
    def to_shuffle_context(self) -> Dict[str, Any]:
        """
        Convert environment to shuffle project_context format.
        
        Returns:
            Dictionary suitable for wickit.shuffle.ServiceRegistry
        """
        return {
            "environment": self.name,
            "type": self.type.name.lower(),
            "is_production": self.is_production,
            "is_development": self.is_development,
        }


# Registry of custom environments
_custom_environments: Dict[str, Environment] = {}


def register_environment(
    name: str,
    parent: Optional[Environment] = None,
    config_overrides: Optional[Dict[str, Any]] = None
) -> Environment:
    """
    Register a custom environment.
    
    Args:
        name: Environment name (e.g., "qa", "demo", "preview")
        parent: Parent environment to inherit from
        config_overrides: Configuration overrides for this environment
        
    Returns:
        Registered Environment instance
        
    Example:
        staging = register_environment(
            "staging",
            parent=get_environment("development"),
            config_overrides={"database": {"name": "staging_db"}}
        )
    """
    env = Environment(
        name=name,
        type=EnvironmentType.CUSTOM,
        parent=parent,
        config_overrides=config_overrides or {}
    )
    _custom_environments[name] = env
    return env


def get_environment(name: Optional[str] = None) -> Environment:
    """
    Get the current or specified environment.
    
    Detection order:
    1. Explicit name parameter
    2. WICKIT_ENV environment variable
    3. .env file (WICKIT_ENV=...)
    4. Git branch (main/master=prod, develop=staging)
    5. Hostname patterns (*.local=local, *-dev=dev)
    6. Default to "local"
    
    Args:
        name: Optional explicit environment name
        
    Returns:
        Environment instance
    """
    # 1. Explicit name
    if name:
        return _get_environment_by_name(name)
    
    # 2. WICKIT_ENV environment variable
    env_var = os.environ.get("WICKIT_ENV")
    if env_var:
        return _get_environment_by_name(env_var)
    
    # 3. .env file
    env_from_file = _read_env_file()
    if env_from_file:
        return _get_environment_by_name(env_from_file)
    
    # 4. Git branch
    git_env = _detect_from_git_branch()
    if git_env:
        return _get_environment_by_name(git_env)
    
    # 5. Hostname
    hostname_env = _detect_from_hostname()
    if hostname_env:
        return _get_environment_by_name(hostname_env)
    
    # 6. Default
    return _get_environment_by_name("local")


def _get_environment_by_name(name: str) -> Environment:
    """Get environment by name (standard or custom)."""
    # Check custom environments first
    if name in _custom_environments:
        return _custom_environments[name]
    
    # Standard environments
    name_lower = name.lower()
    
    if name_lower in ("prod", "production"):
        return Environment(
            name="production",
            type=EnvironmentType.PRODUCTION
        )
    elif name_lower in ("dev", "development"):
        return Environment(
            name="development",
            type=EnvironmentType.DEVELOPMENT
        )
    elif name_lower in ("stage", "staging"):
        return Environment(
            name="staging",
            type=EnvironmentType.STAGING
        )
    elif name_lower in ("local", "localhost"):
        return Environment(
            name="local",
            type=EnvironmentType.LOCAL
        )
    elif name_lower in ("mock", "test", "testing"):
        return Environment(
            name="mock",
            type=EnvironmentType.MOCK
        )
    
    # Unknown environment - create as custom
    return Environment(
        name=name_lower,
        type=EnvironmentType.CUSTOM
    )


def _read_env_file() -> Optional[str]:
    """Read WICKIT_ENV from .env file."""
    env_paths = [".env", ".env.local", ".env.development"]
    
    for path in env_paths:
        if os.path.exists(path):
            with open(path) as f:
                for line in f:
                    if line.startswith("WICKIT_ENV="):
                        return line.split("=", 1)[1].strip().strip('"\'')
    
    return None


def _detect_from_git_branch() -> Optional[str]:
    """Detect environment from git branch."""
    try:
        import subprocess
        result = subprocess.run(
            ["git", "branch", "--show-current"],
            capture_output=True,
            text=True,
            timeout=5
        )
        branch = result.stdout.strip()
        
        if branch in ("main", "master"):
            return "production"
        elif branch in ("develop", "development"):
            return "development"
        elif branch.startswith("staging"):
            return "staging"
        elif branch.startswith("feature/") or branch.startswith("dev-"):
            return "development"
    except Exception:
        pass
    
    return None


def _detect_from_hostname() -> Optional[str]:
    """Detect environment from hostname."""
    import socket
    hostname = socket.gethostname().lower()
    
    if ".local" in hostname or hostname == "localhost":
        return "local"
    elif "-dev" in hostname or "-development" in hostname:
        return "development"
    elif "-stage" in hostname or "-staging" in hostname:
        return "staging"
    elif "-prod" in hostname or "-production" in hostname:
        return "production"
    
    return None


# Convenience functions for common checks
def is_production() -> bool:
    """Check if running in production."""
    return get_environment().is_production


def is_development() -> bool:
    """Check if running in development."""
    return get_environment().is_development


def is_local() -> bool:
    """Check if running locally."""
    return get_environment().is_local


# Export public API
__all__ = [
    "Environment",
    "EnvironmentType",
    "get_environment",
    "register_environment",
    "is_production",
    "is_development",
    "is_local",
]

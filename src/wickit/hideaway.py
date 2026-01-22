"""Data directory management for products.

Provides common data directory paths for all products.
"""

from pathlib import Path
from typing import Protocol


class ProductName(Protocol):
    """Protocol for valid product names."""
    def __str__(self) -> str: ...


VALID_PRODUCTS = {
    "cv-studio": "cvstudio",
    "cvstudio": "cvstudio",
    "aixam": "aixam",
    "studya": "studya",
    "jobforge": "jobforge",
    "default": "default",
}


def get_data_dir(product_name: str) -> Path:
    """Get data directory for a product.

    Args:
        product_name: Name of the product (e.g., "cv-studio", "studya")

    Returns:
        Path to the data directory (e.g., ~/.studya/, ~/.jobforge/)
    """
    dir_name = VALID_PRODUCTS.get(product_name.lower(), product_name.lower())
    return Path.home() / f".{dir_name}"


def get_config_path(product_name: str) -> Path:
    """Get config file path for a product.

    Args:
        product_name: Name of the product

    Returns:
        Path to the config file (e.g., ~/.studya/config.json)
    """
    return get_data_dir(product_name) / "config.json"


def ensure_data_dir(product_name: str) -> Path:
    """Create data directory if it doesn't exist.

    Args:
        product_name: Name of the product

    Returns:
        Path to the data directory
    """
    data_dir = get_data_dir(product_name)
    data_dir.mkdir(parents=True, exist_ok=True)
    return data_dir


def get_project_names() -> list[str]:
    """List all known projects that have data directories."""
    home = Path.home()
    projects = []
    for path in home.iterdir():
        if path.name.startswith(".") and path.is_dir():
            product = path.name[1:]
            if product in VALID_PRODUCTS:
                projects.append(product)
    return sorted(projects)


def is_product_installed(product_name: str) -> bool:
    """Check if a product has a data directory."""
    return get_data_dir(product_name).exists()


def get_all_product_data_dirs() -> dict[str, Path]:
    """Get all product data directories."""
    return {name: get_data_dir(name) for name in VALID_PRODUCTS if is_product_installed(name)}

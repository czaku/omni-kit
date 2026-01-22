"""alter_egos - Profile Management.

Manage multiple named profiles for applications with defaults and metadata.
Profiles are stored as directories within the product data directory.

Example:
    >>> from wickit import alter_egos
    >>> profiles = alter_egos.list_profiles("myapp")
    >>> alter_egos.create_profile("myapp", "development", {"env": "dev"})
    >>> alter_egos.set_default_profile("myapp", "development")

Classes:
    Profile: Profile with id, name, path, is_default, created, modified.

Functions:
    list_profiles: List all profiles for a product.
    get_default_profile: Get default or first profile.
    create_profile: Create new profile.
    delete_profile: Delete a profile.
    copy_profile: Copy a profile.
    set_default_profile: Set default profile.
    profile_exists: Check if profile exists.
"""

import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Optional

from .hideaway import get_data_dir


@dataclass
class Profile:
    """Represents a product profile."""
    id: str
    name: str
    path: Path
    is_default: bool
    created: str
    modified: str


def list_profiles(product_name: str) -> list[Profile]:
    """List all profiles for a product."""
    data_dir = get_data_dir(product_name)
    if not data_dir.exists():
        return []

    profiles = []
    for entry in data_dir.iterdir():
        if entry.is_dir() and not entry.name.startswith("."):
            profile = _load_profile(entry, product_name)
            if profile:
                profiles.append(profile)

    return sorted(profiles, key=lambda p: p.name)


def get_default_profile(product_name: str) -> Optional[Profile]:
    """Get the default profile for a product."""
    profiles = list_profiles(product_name)
    for profile in profiles:
        if profile.is_default:
            return profile
    return profiles[0] if profiles else None


def _load_profile(path: Path, product_name: str) -> Optional[Profile]:
    """Load a profile from disk."""
    metadata_files = [
        path / f".{product_name.replace('-', '')}.json",
        path / ".profile.json",
        path / ".default",
    ]

    metadata_file = None
    for mf in metadata_files:
        if mf.exists():
            metadata_file = mf
            break

    is_default = (path / ".default").exists()

    if metadata_file and metadata_file.exists():
        try:
            with open(metadata_file) as f:
                data = json.load(f)
            return Profile(
                id=path.name,
                name=data.get("name", path.name),
                path=path,
                is_default=is_default,
                created=data.get("created", ""),
                modified=data.get("modified", ""),
            )
        except (json.JSONDecodeError, IOError):
            pass

    return Profile(
        id=path.name,
        name=path.name,
        path=path,
        is_default=is_default,
        created="",
        modified="",
    )


def create_profile(product_name: str, profile_name: str) -> Profile:
    """Create a new profile."""
    data_dir = get_data_dir(product_name)
    profile_path = data_dir / profile_name.lower().replace(" ", "-")

    profile_path.mkdir(parents=True, exist_ok=True)
    (profile_path / "data").mkdir(exist_ok=True)

    now = datetime.utcnow().isoformat()

    metadata_file = profile_path / f".{product_name.replace('-', '')}.json"
    metadata = {
        "name": profile_name,
        "created": now,
        "modified": now,
    }
    with open(metadata_file, "w") as f:
        json.dump(metadata, f, indent=2)

    return Profile(
        id=profile_path.name,
        name=profile_name,
        path=profile_path,
        is_default=False,
        created=now,
        modified=now,
    )


def delete_profile(product_name: str, profile_id: str) -> bool:
    """Delete a profile."""
    import shutil
    data_dir = get_data_dir(product_name)
    profile_path = data_dir / profile_id

    if not profile_path.exists():
        return False

    shutil.rmtree(profile_path)
    return True


def copy_profile(product_name: str, source_id: str, target_name: str) -> Optional[Profile]:
    """Copy a profile to a new profile."""
    import shutil
    data_dir = get_data_dir(product_name)
    source_path = data_dir / source_id

    if not source_path.exists():
        return None

    target_path = data_dir / target_name.lower().replace(" ", "-")
    shutil.copytree(source_path, target_path)

    now = datetime.utcnow().isoformat()
    metadata_file = target_path / f".{product_name.replace('-', '')}.json"

    if metadata_file.exists():
        with open(metadata_file) as f:
            metadata = json.load(f)
        metadata["name"] = target_name
        metadata["modified"] = now
        with open(metadata_file, "w") as f:
            json.dump(metadata, f, indent=2)

    return _load_profile(target_path, product_name)


def set_default_profile(product_name: str, profile_id: str) -> bool:
    """Set a profile as default."""
    data_dir = get_data_dir(product_name)

    for entry in data_dir.iterdir():
        if entry.is_dir():
            default_marker = entry / ".default"
            if default_marker.exists():
                default_marker.unlink()

    profile_path = data_dir / profile_id
    if profile_path.exists():
        (profile_path / ".default").touch()
        return True

    return False


def profile_exists(product_name: str, profile_id: str) -> bool:
    """Check if a profile exists."""
    data_dir = get_data_dir(product_name)
    return (data_dir / profile_id).exists()

"""dropzone - Cloud Folder Detection.

Detect cloud storage folders on the system (Dropbox, Google Drive, OneDrive,
iCloud). Scans common locations across platforms.

Example:
    >>> from wickit import dropzone
    >>> folders = dropzone.detect_cloud_folders()
    >>> dropbox = dropzone.get_dropbox_folder()

Classes:
    CloudProvider: Enum for cloud providers.
    SyncFolder: Sync folder configuration.
    SyncStatus: Sync status enum.
    LocalFolderSync: Local folder sync manager.

Functions:
    detect_cloud_folders: Find all cloud folders on system.
    get_dropbox_folder: Get Dropbox folder path.
    get_google_drive_folder: Get Google Drive folder path.
    get_onedrive_folder: Get OneDrive folder path.
    get_icloud_folder: Get iCloud folder path.
    get_default_sync_folder: Get default sync folder.
    create_sync_folder: Create sync folder configuration.
"""

from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Optional


class CloudProvider(Enum):
    """Cloud providers with local sync folders."""
    DROPBOX = "dropbox"
    GOOGLE_DRIVE = "google_drive"
    ONEDRIVE = "onedrive"
    ICLOUD = "icloud"
    MANUAL = "manual"


@dataclass
class SyncFolder:
    """Represents a detected sync folder."""
    provider: CloudProvider
    path: Path
    available: bool
    project_path: Optional[Path] = None


@dataclass
class SyncStatus:
    """Sync status for a provider."""
    provider: CloudProvider
    available: bool
    folder_exists: bool
    product_exists: bool
    last_sync: Optional[str]


def get_dropbox_folder() -> Optional[Path]:
    """Find Dropbox sync folder."""
    home = Path.home()
    candidates = [
        home / "Dropbox",
        home / "Documents" / "Dropbox",
        home / "Library" / "CloudStorage" / "Dropbox",
    ]
    for path in candidates:
        if path.exists() and (path / "Dropbox").exists():
            return path / "Dropbox"
        if path.exists():
            return path
    return None


def get_google_drive_folder() -> Optional[Path]:
    """Find Google Drive sync folder."""
    home = Path.home()
    candidates = [
        home / "Google Drive",
        home / "My Drive",
        home / "Library" / "CloudStorage" / "GoogleDrive",
    ]
    for path in candidates:
        if path.exists():
            return path
    return None


def get_onedrive_folder() -> Optional[Path]:
    """Find OneDrive sync folder."""
    home = Path.home()
    candidates = [
        home / "OneDrive",
        home / "Library" / "CloudStorage" / "OneDrive",
    ]
    for path in candidates:
        if path.exists():
            return path
    return None


def get_icloud_folder() -> Optional[Path]:
    """Find iCloud Drive sync folder."""
    home = Path.home()
    candidates = [
        home / "Library" / "Mobile Documents" / "com~apple~CloudDocs",
    ]
    for path in candidates:
        if path.exists():
            return path
    return None


def detect_cloud_folders() -> list[SyncFolder]:
    """Detect all available cloud sync folders."""
    folders = []
    if dropbox := get_dropbox_folder():
        folders.append(SyncFolder(CloudProvider.DROPBOX, dropbox, True, None))
    if gdrive := get_google_drive_folder():
        folders.append(SyncFolder(CloudProvider.GOOGLE_DRIVE, gdrive, True, None))
    if onedrive := get_onedrive_folder():
        folders.append(SyncFolder(CloudProvider.ONEDRIVE, onedrive, True, None))
    if icloud := get_icloud_folder():
        folders.append(SyncFolder(CloudProvider.ICLOUD, icloud, True, None))
    return folders


def get_default_sync_folder(provider: CloudProvider, product_name: str) -> Optional[Path]:
    """Get default sync folder for a provider."""
    folder_getters = {
        CloudProvider.DROPBOX: get_dropbox_folder,
        CloudProvider.GOOGLE_DRIVE: get_google_drive_folder,
        CloudProvider.ONEDRIVE: get_onedrive_folder,
        CloudProvider.ICLOUD: get_icloud_folder,
    }

    getter = folder_getters.get(provider)
    if not getter:
        return None

    if folder := getter():
        product_folder_name = product_name.replace("-", " ").title().replace(" ", "")
        return folder / product_folder_name
    return None


def create_sync_folder(provider: CloudProvider, product_name: str) -> Optional[Path]:
    """Create product folder in cloud sync directory."""
    folder = get_default_sync_folder(provider, product_name)
    if folder:
        folder.mkdir(parents=True, exist_ok=True)
    return folder


class LocalFolderSync:
    """Local folder sync for browser extensions."""

    def __init__(self, product_name: str):
        self.product_name = product_name
        self.sync_folder: Optional[Path] = None
        self.sync_provider: Optional[str] = None

    def get_default_folders(self) -> dict:
        """Get default sync folders for all providers."""
        return {
            "dropbox": get_default_sync_folder(CloudProvider.DROPBOX, self.product_name),
            "drive": get_default_sync_folder(CloudProvider.GOOGLE_DRIVE, self.product_name),
            "custom": None,
        }

    def set_folder(self, path: str, provider: str = "custom") -> bool:
        """Set the sync folder."""
        self.sync_folder = Path(path)
        self.sync_provider = provider
        return self.sync_folder.exists()

    def disconnect(self) -> None:
        """Disconnect from sync folder."""
        self.sync_folder = None
        self.sync_provider = None

    def get_status(self) -> dict:
        """Get current sync status."""
        return {
            "provider": self.sync_provider,
            "folder": str(self.sync_folder) if self.sync_folder else None,
            "connected": self.sync_folder is not None,
        }

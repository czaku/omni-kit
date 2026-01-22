"""cloudbridge - Cloud API Sync.

Cloud storage synchronization with Dropbox and Google Drive APIs.
Provides OAuth-based authentication and file operations.

Example:
    >>> from wickit import cloudbridge
    >>> sync = cloudbridge.DropboxSync(access_token="your-token")
    >>> result = cloudbridge.sync_to_cloud(sync, local_file, "/remote/path")

Classes:
    SyncResult: Result of sync operation.
    CloudSync: Abstract base class for cloud providers.
    DropboxSync: Dropbox synchronization.
    GoogleDriveSync: Google Drive synchronization.

Functions:
    get_cloud_sync_provider: Get configured sync provider.
    sync_to_cloud: Upload to cloud storage.
    restore_from_cloud: Download from cloud storage.
"""

import json
import os
from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import Optional


@dataclass
class SyncResult:
    """Result of a sync operation."""
    success: bool
    message: str
    files_synced: int = 0
    error: Optional[str] = None


class CloudSync(ABC):
    """Abstract base class for cloud sync providers."""

    @abstractmethod
    def connect(self, access_token: str) -> bool:
        pass

    @abstractmethod
    def upload(self, local_path: Path, remote_path: str) -> bool:
        pass

    @abstractmethod
    def download(self, remote_path: str, local_path: Path) -> bool:
        pass

    @abstractmethod
    def list_files(self, folder_path: str) -> list[str]:
        pass

    @abstractmethod
    def disconnect(self) -> None:
        pass


class DropboxSync(CloudSync):
    """Dropbox sync implementation."""

    def __init__(self):
        self._access_token: Optional[str] = None
        self._base_url = "https://api.dropboxapi.com/2"
        self._content_url = "https://content.dropboxapi.com/2"

    def connect(self, access_token: str) -> bool:
        self._access_token = access_token
        return self._verify_connection()

    def _verify_connection(self) -> bool:
        try:
            import requests
            response = requests.post(
                f"{self._base_url}/users/get_current_account",
                headers={"Authorization": f"Bearer {self._access_token}"},
                data="null"
            )
            return response.status_code == 200
        except Exception:
            return False

    def upload(self, local_path: Path, remote_path: str) -> bool:
        try:
            import requests
            if not self._access_token:
                raise ValueError("Not connected to Dropbox")

            with open(local_path, "rb") as f:
                data = f.read()

            response = requests.post(
                f"{self._content_url}/files/upload",
                headers={
                    "Authorization": f"Bearer {self._access_token}",
                    "Content-Type": "application/octet-stream",
                    "Dropbox-API-Arg": json.dumps({
                        "path": remote_path,
                        "mode": "overwrite",
                        "autorename": False,
                        "mute": False
                    })
                },
                data=data
            )
            return response.status_code == 200
        except Exception:
            return False

    def download(self, remote_path: str, local_path: Path) -> bool:
        try:
            import requests
            if not self._access_token:
                raise ValueError("Not connected to Dropbox")

            response = requests.post(
                f"{self._content_url}/files/download",
                headers={
                    "Authorization": f"Bearer {self._access_token}",
                    "Dropbox-API-Arg": json.dumps({"path": remote_path})
                }
            )
            if response.status_code == 200:
                local_path.parent.mkdir(parents=True, exist_ok=True)
                with open(local_path, "wb") as f:
                    f.write(response.content)
                return True
            return False
        except Exception:
            return False

    def list_files(self, folder_path: str) -> list[str]:
        try:
            import requests
            if not self._access_token:
                raise ValueError("Not connected to Dropbox")

            response = requests.post(
                f"{self._base_url}/files/list_folder",
                headers={
                    "Authorization": f"Bearer {self._access_token}",
                    "Content-Type": "application/json"
                },
                data=json.dumps({"path": folder_path, "recursive": False})
            )
            if response.status_code == 200:
                data = response.json()
                return [entry["path_lower"] for entry in data.get("entries", [])]
            return []
        except Exception:
            return []

    def disconnect(self) -> None:
        self._access_token = None


class GoogleDriveSync(CloudSync):
    """Google Drive sync implementation."""

    def __init__(self):
        self._access_token: Optional[str] = None
        self._base_url = "https://www.googleapis.com/drive/v3"

    def connect(self, access_token: str) -> bool:
        self._access_token = access_token
        return self._verify_connection()

    def _verify_connection(self) -> bool:
        try:
            import requests
            response = requests.get(
                f"{self._base_url}/about",
                headers={"Authorization": f"Bearer {self._access_token}"}
            )
            return response.status_code == 200
        except Exception:
            return False

    def upload(self, local_path: Path, remote_path: str) -> bool:
        try:
            import requests
            if not self._access_token:
                raise ValueError("Not connected to Google Drive")

            with open(local_path, "rb") as f:
                files = {"file": f}
                data = {"fields": "id,name"}

            response = requests.post(
                f"{self._base_url}/files",
                headers={"Authorization": f"Bearer {self._access_token}"},
                files=files,
                data=data
            )
            return response.status_code in [200, 201]
        except Exception:
            return False

    def download(self, remote_path: str, local_path: Path) -> bool:
        try:
            import requests
            if not self._access_token:
                raise ValueError("Not connected to Google Drive")

            file_id = remote_path
            response = requests.get(
                f"{self._base_url}/files/{file_id}?alt=media",
                headers={"Authorization": f"Bearer {self._access_token}"}
            )
            if response.status_code == 200:
                local_path.parent.mkdir(parents=True, exist_ok=True)
                with open(local_path, "wb") as f:
                    f.write(response.content)
                return True
            return False
        except Exception:
            return False

    def list_files(self, folder_path: str) -> list[str]:
        try:
            import requests
            if not self._access_token:
                raise ValueError("Not connected to Google Drive")

            response = requests.get(
                f"{self._base_url}/files",
                headers={"Authorization": f"Bearer {self._access_token}"},
                params={
                    "q": f"'{folder_path}' in parents",
                    "fields": "files(id,name)"
                }
            )
            if response.status_code == 200:
                data = response.json()
                return [f["id"] for f in data.get("files", [])]
            return []
        except Exception:
            return []

    def disconnect(self) -> None:
        self._access_token = None


def get_cloud_sync_provider(provider_name: str) -> CloudSync:
    """Get a cloud sync provider instance."""
    if provider_name == "dropbox":
        return DropboxSync()
    elif provider_name == "google_drive":
        return GoogleDriveSync()
    else:
        raise ValueError(f"Unknown provider: {provider_name}")


def sync_to_cloud(
    product_name: str,
    provider_name: str,
    access_token: str,
    cloud_folder: str = "/"
) -> SyncResult:
    """Sync a product to cloud storage."""
    from .hideaway import get_data_dir

    sync = get_cloud_sync_provider(provider_name)

    try:
        if not sync.connect(access_token):
            return SyncResult(success=False, message="Failed to connect to cloud provider")

        product_dir = get_data_dir(product_name)
        files_synced = 0

        for root, dirs, files in os.walk(product_dir):
            dirs[:] = [d for d in dirs if d != ".backups" and not d.startswith(".")]
            for file in files:
                if file.endswith(".zip"):
                    continue
                local_path = Path(root) / file
                rel_path = local_path.relative_to(product_dir)
                remote_path = f"{cloud_folder}/{rel_path}"
                if sync.upload(local_path, remote_path):
                    files_synced += 1

        sync.disconnect()
        return SyncResult(success=True, message=f"Synced {files_synced} files", files_synced=files_synced)

    except Exception as e:
        return SyncResult(success=False, message=str(e))


def restore_from_cloud(
    product_name: str,
    provider_name: str,
    access_token: str,
    cloud_folder: str = "/"
) -> SyncResult:
    """Restore a product from cloud storage."""
    from .hideaway import get_data_dir, ensure_data_dir

    sync = get_cloud_sync_provider(provider_name)

    try:
        if not sync.connect(access_token):
            return SyncResult(success=False, message="Failed to connect to cloud provider")

        files_synced = 0
        product_dir = ensure_data_dir(product_name)
        remote_files = sync.list_files(cloud_folder)

        for remote_path in remote_files:
            filename = remote_path.split("/")[-1]
            if filename.endswith(".zip"):
                continue
            local_path = product_dir / filename
            if sync.download(remote_path, local_path):
                files_synced += 1

        sync.disconnect()
        return SyncResult(success=True, message=f"Restored {files_synced} files", files_synced=files_synced)

    except Exception as e:
        return SyncResult(success=False, message=str(e))

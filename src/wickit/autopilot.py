"""autopilot - Auto-Sync Watcher.

Automatic file synchronization with directory watching and change detection.
Watches for file modifications and syncs to cloud storage.

Example:
    >>> from wickit import autopilot
    >>> manager = autopilot.AutoSyncManager()
    >>> manager.add_folder("/path/to/watch", cloud_provider="dropbox")
    >>> manager.start()

Classes:
    AutoSyncConfig: Configuration for auto-sync.
    AutoSync: Single folder auto-sync watcher.
    AutoSyncManager: Manages multiple auto-sync folders.

Functions:
    AutoSyncManager.add_folder: Add folder to auto-sync.
    AutoSyncManager.start: Start watching.
    AutoSyncManager.stop: Stop watching.
    AutoSyncManager.get_status: Get sync status.
"""

import hashlib
import os
import threading
import time
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Optional


@dataclass
class AutoSyncConfig:
    """Configuration for auto-sync."""
    product_name: str
    provider: str
    access_token: Optional[str] = None
    debounce_seconds: float = 2.0
    poll_interval: float = 0.5


class AutoSync:
    """Auto-sync manager that watches for file changes and syncs to cloud."""

    def __init__(
        self,
        product_dir: Path,
        provider: str = "dropbox",
        access_token: Optional[str] = None,
        debounce_seconds: float = 2.0,
        on_sync: Optional[Callable] = None
    ):
        self.product_dir = product_dir
        self.provider = provider
        self._access_token = access_token
        self.debounce_seconds = debounce_seconds
        self.on_sync = on_sync

        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._file_hashes: dict[str, str] = {}
        self._callbacks: set[Callable] = set()

    def set_access_token(self, token: str) -> None:
        """Set the cloud provider access token."""
        self._access_token = token

    def start(self) -> None:
        """Start the auto-sync watcher."""
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._watch_loop, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        """Stop the auto-sync watcher."""
        self._running = False
        if self._thread:
            self._thread.join(timeout=5.0)
            self._thread = None

    def add_callback(self, callback: Callable) -> None:
        """Add a callback to be called after sync."""
        self._callbacks.add(callback)

    def remove_callback(self, callback: Callable) -> None:
        """Remove a sync callback."""
        self._callbacks.discard(callback)

    def _compute_hash(self, file_path: Path) -> str:
        """Compute a simple hash for file content."""
        content = file_path.read_bytes()
        return hashlib.md5(content).hexdigest()

    def _get_tracked_files(self) -> list[Path]:
        """Get list of files to track for changes."""
        files = []
        for root, dirs, filenames in os.walk(self.product_dir):
            dirs[:] = [d for d in dirs if d != ".backups" and not d.startswith(".")]
            for filename in filenames:
                if filename.endswith(".json") and not filename.endswith(".zip"):
                    files.append(Path(root) / filename)
        return files

    def _sync_now(self) -> dict:
        """Perform sync now."""
        if not self._access_token:
            return {"success": False, "message": "No access token set"}

        from .cloudbridge import sync_to_cloud
        product_name = self.product_dir.name.replace(".", "").replace("-", " ")
        result = sync_to_cloud(
            product_name=product_name,
            provider_name=self.provider,
            access_token=self._access_token
        )
        return {
            "success": result.success,
            "message": result.message,
            "files_synced": result.files_synced,
            "error": result.error
        }

    def _watch_loop(self) -> None:
        """Main watch loop."""
        initial_files = self._get_tracked_files()
        for f in initial_files:
            if f.exists():
                self._file_hashes[str(f)] = self._compute_hash(f)

        while self._running:
            time.sleep(0.5)
            current_files = self._get_tracked_files()
            changed_files = []

            for f in current_files:
                f_str = str(f)
                if not f.exists():
                    continue
                current_hash = self._compute_hash(f)
                if f_str not in self._file_hashes:
                    changed_files.append(f)
                elif self._file_hashes[f_str] != current_hash:
                    changed_files.append(f)

            if changed_files:
                for f in changed_files:
                    self._file_hashes[str(f)] = self._compute_hash(f)
                time.sleep(self.debounce_seconds)
                still_changing = False
                for f in changed_files:
                    if f.exists():
                        new_hash = self._compute_hash(f)
                        if new_hash != self._file_hashes.get(str(f), ""):
                            still_changing = True
                            break
                if not still_changing:
                    result = self._sync_now()
                    if self.on_sync:
                        self.on_sync(result)
                    for cb in self._callbacks:
                        cb()

    def sync_once(self) -> dict:
        """Perform a single sync."""
        return self._sync_now()

    def is_running(self) -> bool:
        """Check if auto-sync is running."""
        return self._running


class AutoSyncManager:
    """Global auto-sync manager for the application."""

    _instance: Optional["AutoSyncManager"] = None
    _sync: Optional[AutoSync] = None

    @classmethod
    def get_instance(cls) -> "AutoSyncManager":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    @classmethod
    def reset(cls) -> None:
        if cls._instance and cls._instance._sync:
            cls._instance._sync.stop()
        cls._instance = None
        cls._sync = None

    def start_autosync(
        self,
        product_dir: Path,
        provider: str = "dropbox",
        access_token: Optional[str] = None,
        debounce_seconds: float = 2.0,
        on_sync: Optional[Callable] = None
    ) -> bool:
        """Start auto-sync for a product."""
        if provider not in ["dropbox", "google_drive"]:
            return False

        self.stop_autosync()
        self._sync = AutoSync(
            product_dir=product_dir,
            provider=provider,
            access_token=access_token,
            debounce_seconds=debounce_seconds,
            on_sync=on_sync
        )
        self._sync.start()
        return True

    def stop_autosync(self) -> None:
        """Stop auto-sync."""
        if self._sync:
            self._sync.stop()
            self._sync = None

    def set_token(self, token: str) -> None:
        """Set access token for auto-sync."""
        if self._sync:
            self._sync.set_access_token(token)

    def sync_now(self) -> dict:
        """Trigger immediate sync."""
        if self._sync:
            return self._sync.sync_once()
        return {"success": False, "message": "Auto-sync not running"}

    def is_running(self) -> bool:
        """Check if auto-sync is running."""
        return self._sync is not None and self._sync.is_running()

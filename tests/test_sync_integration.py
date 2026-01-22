"""Tests for omni-kit sync integration with products."""

import json
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest


class TestSyncLocalIntegration:
    """Tests for local sync folder integration."""

    def test_detect_dropbox_folder(self, tmp_path, monkeypatch):
        """Test Dropbox folder detection."""
        monkeypatch.setattr("pathlib.Path.home", lambda: tmp_path)
        (tmp_path / "Dropbox").mkdir()

        from wickit import get_dropbox_folder

        result = get_dropbox_folder()
        assert result == tmp_path / "Dropbox"

    def test_detect_google_drive_folder(self, tmp_path, monkeypatch):
        """Test Google Drive folder detection."""
        monkeypatch.setattr("pathlib.Path.home", lambda: tmp_path)
        (tmp_path / "Google Drive").mkdir()

        from wickit import get_google_drive_folder

        result = get_google_drive_folder()
        assert result == tmp_path / "Google Drive"

    def test_detect_onedrive_folder(self, tmp_path, monkeypatch):
        """Test OneDrive folder detection."""
        monkeypatch.setattr("pathlib.Path.home", lambda: tmp_path)
        (tmp_path / "OneDrive").mkdir()

        from wickit import get_onedrive_folder

        result = get_onedrive_folder()
        assert result == tmp_path / "OneDrive"

    def test_detect_no_folders(self, tmp_path, monkeypatch):
        """Test when no cloud folders exist."""
        monkeypatch.setattr("pathlib.Path.home", lambda: tmp_path)

        from wickit import detect_cloud_folders

        result = detect_cloud_folders()
        assert result == []

    def test_detect_multiple_folders(self, tmp_path, monkeypatch):
        """Test detecting multiple cloud folders."""
        monkeypatch.setattr("pathlib.Path.home", lambda: tmp_path)
        (tmp_path / "Dropbox").mkdir()
        (tmp_path / "Google Drive").mkdir()
        (tmp_path / "OneDrive").mkdir()

        from wickit import detect_cloud_folders

        result = detect_cloud_folders()
        assert len(result) == 3

        providers = [f.provider.value for f in result]
        assert "dropbox" in providers
        assert "google_drive" in providers
        assert "onedrive" in providers


class TestSyncDefaultFolders:
    """Tests for default sync folder generation."""

    def test_jobforge_dropbox_folder(self, tmp_path, monkeypatch):
        """Test jobforge Dropbox folder path."""
        monkeypatch.setattr("pathlib.Path.home", lambda: tmp_path)
        (tmp_path / "Dropbox").mkdir()

        from wickit import get_default_sync_folder, CloudProvider

        result = get_default_sync_folder(CloudProvider.DROPBOX, "jobforge")
        expected = tmp_path / "Dropbox" / "Jobforge"
        assert result == expected

    def test_studya_dropbox_folder(self, tmp_path, monkeypatch):
        """Test studya Dropbox folder path."""
        monkeypatch.setattr("pathlib.Path.home", lambda: tmp_path)
        (tmp_path / "Dropbox").mkdir()

        from wickit import get_default_sync_folder, CloudProvider

        result = get_default_sync_folder(CloudProvider.DROPBOX, "studya")
        expected = tmp_path / "Dropbox" / "Studya"
        assert result == expected

    def test_create_sync_folder(self, tmp_path, monkeypatch):
        """Test creating sync folder."""
        monkeypatch.setattr("pathlib.Path.home", lambda: tmp_path)
        (tmp_path / "Dropbox").mkdir()

        from wickit import create_sync_folder, CloudProvider

        result = create_sync_folder(CloudProvider.DROPBOX, "jobforge")
        expected = tmp_path / "Dropbox" / "Jobforge"
        assert result == expected
        assert expected.exists()


class TestSyncLocalFolderSync:
    """Tests for LocalFolderSync class."""

    def test_local_folder_sync_init(self):
        """Test LocalFolderSync initialization."""
        from wickit import LocalFolderSync

        sync = LocalFolderSync("jobforge")
        assert sync.product_name == "jobforge"
        assert sync.sync_folder is None
        assert sync.sync_provider is None

    def test_local_folder_sync_set_folder(self, tmp_path):
        """Test setting sync folder."""
        from wickit import LocalFolderSync

        sync = LocalFolderSync("jobforge")
        test_folder = tmp_path / "test_sync"
        test_folder.mkdir()

        result = sync.set_folder(str(test_folder), "dropbox")

        assert result is True
        assert sync.sync_folder == test_folder
        assert sync.sync_provider == "dropbox"

    def test_local_folder_sync_disconnect(self):
        """Test disconnecting sync."""
        from wickit import LocalFolderSync

        sync = LocalFolderSync("jobforge")
        sync.sync_folder = Path("/test")
        sync.sync_provider = "dropbox"

        sync.disconnect()

        assert sync.sync_folder is None
        assert sync.sync_provider is None

    def test_local_folder_sync_status(self):
        """Test getting sync status."""
        from wickit import LocalFolderSync

        sync = LocalFolderSync("jobforge")
        status = sync.get_status()

        assert status["provider"] is None
        assert status["folder"] is None
        assert status["connected"] is False

    def test_local_folder_sync_get_defaults(self, tmp_path, monkeypatch):
        """Test getting default folders."""
        monkeypatch.setattr("pathlib.Path.home", lambda: tmp_path)
        (tmp_path / "Dropbox").mkdir()
        (tmp_path / "Google Drive").mkdir()

        from wickit import LocalFolderSync

        sync = LocalFolderSync("jobforge")
        defaults = sync.get_default_folders()

        assert "dropbox" in defaults
        assert "drive" in defaults
        assert defaults["dropbox"] == tmp_path / "Dropbox" / "Jobforge"


class TestSyncStatus:
    """Tests for SyncStatus dataclass."""

    def test_sync_status_available(self):
        """Test SyncStatus with available provider."""
        from wickit import SyncStatus, CloudProvider

        status = SyncStatus(
            provider=CloudProvider.DROPBOX,
            available=True,
            folder_exists=True,
            product_exists=True,
            last_sync="2024-01-01T00:00:00"
        )

        assert status.provider == CloudProvider.DROPBOX
        assert status.available is True
        assert status.folder_exists is True
        assert status.product_exists is True

    def test_sync_status_unavailable(self):
        """Test SyncStatus with unavailable provider."""
        from wickit import SyncStatus, CloudProvider

        status = SyncStatus(
            provider=CloudProvider.GOOGLE_DRIVE,
            available=False,
            folder_exists=False,
            product_exists=False,
            last_sync=None
        )

        assert status.available is False
        assert status.folder_exists is False
        assert status.product_exists is False
        assert status.last_sync is None


class TestSyncCloudProvider:
    """Tests for CloudProvider enum."""

    def test_provider_values(self):
        """Test all provider values."""
        from wickit import CloudProvider

        assert CloudProvider.DROPBOX.value == "dropbox"
        assert CloudProvider.GOOGLE_DRIVE.value == "google_drive"
        assert CloudProvider.ONEDRIVE.value == "onedrive"
        assert CloudProvider.ICLOUD.value == "icloud"
        assert CloudProvider.MANUAL.value == "manual"

    def test_provider_equality(self):
        """Test provider equality."""
        from wickit import CloudProvider

        assert CloudProvider.DROPBOX == CloudProvider.DROPBOX
        assert CloudProvider.DROPBOX != CloudProvider.GOOGLE_DRIVE


class TestSyncFolder:
    """Tests for SyncFolder dataclass."""

    def test_sync_folder_creation(self):
        """Test creating SyncFolder."""
        from wickit import SyncFolder, CloudProvider

        folder = SyncFolder(
            provider=CloudProvider.DROPBOX,
            path=Path("/Dropbox"),
            available=True,
            project_path=Path("/Dropbox/Jobforge")
        )

        assert folder.provider == CloudProvider.DROPBOX
        assert folder.path == Path("/Dropbox")
        assert folder.available is True
        assert folder.project_path == Path("/Dropbox/Jobforge")

    def test_sync_folder_without_project(self):
        """Test SyncFolder without project path."""
        from wickit import SyncFolder, CloudProvider

        folder = SyncFolder(
            provider=CloudProvider.DROPBOX,
            path=Path("/Dropbox"),
            available=True,
            project_path=None
        )

        assert folder.project_path is None


class TestSyncCloudSync:
    """Tests for cloud sync classes (connection tests mocked)."""

    def test_dropbox_sync_init(self):
        """Test DropboxSync initialization."""
        from wickit import DropboxSync

        sync = DropboxSync()
        assert sync._access_token is None

    def test_google_drive_sync_init(self):
        """Test GoogleDriveSync initialization."""
        from wickit import GoogleDriveSync

        sync = GoogleDriveSync()
        assert sync._access_token is None

    def test_get_cloud_provider(self):
        """Test getting cloud sync provider."""
        from wickit import get_cloud_sync_provider, DropboxSync, GoogleDriveSync

        dropbox = get_cloud_sync_provider("dropbox")
        assert isinstance(dropbox, DropboxSync)

        gdrive = get_cloud_sync_provider("google_drive")
        assert isinstance(gdrive, GoogleDriveSync)


class TestSyncIntegration:
    """Integration tests for sync with products."""

    def test_omni_kit_cloud_sync_imports(self):
        """Test omni-kit can import cloud sync classes."""
        from wickit import DropboxSync, GoogleDriveSync, SyncResult

        dropbox = DropboxSync()
        assert dropbox is not None

        gdrive = GoogleDriveSync()
        assert gdrive is not None

    def test_omni_kit_local_sync_imports(self):
        """Test omni-kit can import local sync functions."""
        from wickit import detect_cloud_folders, get_default_sync_folder

        folders = detect_cloud_folders()
        assert isinstance(folders, list)

    def test_studya_cloud_sync_imports(self):
        """Test studya can import cloud sync functions."""
        from wickit import detect_cloud_folders, get_default_sync_folder

        folders = detect_cloud_folders()
        assert isinstance(folders, list)

    def test_full_sync_path(self, tmp_path, monkeypatch):
        """Test complete sync path from detection to status."""
        monkeypatch.setattr("pathlib.Path.home", lambda: tmp_path)
        dropbox = tmp_path / "Dropbox"
        dropbox.mkdir()
        jobforge_folder = dropbox / "Jobforge"
        jobforge_folder.mkdir()

        from wickit import detect_cloud_folders, CloudProvider

        folders = detect_cloud_folders()
        dropbox_folder = next((f for f in folders if f.provider == CloudProvider.DROPBOX), None)

        assert dropbox_folder is not None
        assert dropbox_folder.available is True


class TestSyncEdgeCases:
    """Edge case tests for sync."""

    def test_provider_from_string(self):
        """Test creating CloudProvider from string."""
        from wickit import CloudProvider

        dropbox = CloudProvider("dropbox")
        assert dropbox == CloudProvider.DROPBOX

    def test_nonexistent_provider(self):
        """Test handling of nonexistent provider."""
        from wickit import get_cloud_sync_provider

        try:
            get_cloud_sync_provider("nonexistent")
            assert False, "Should have raised ValueError"
        except ValueError as e:
            assert "Unknown provider" in str(e)

    def test_sync_status_with_none_values(self):
        """Test SyncStatus with None values."""
        from wickit import SyncStatus, CloudProvider

        status = SyncStatus(
            provider=CloudProvider.DROPBOX,
            available=True,
            folder_exists=True,
            product_exists=True,
            last_sync=None
        )

        assert status.last_sync is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

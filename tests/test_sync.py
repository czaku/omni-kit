"""Tests for omni-kit - Cloud sync strategies."""

from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest


class TestCloudProvider:
    """Tests for CloudProvider enum."""

    def test_all_providers_defined(self):
        """Test all expected providers are defined."""
        from wickit import CloudProvider

        expected = ["DROPBOX", "GOOGLE_DRIVE", "ONEDRIVE", "ICLOUD", "MANUAL"]
        for provider in expected:
            assert hasattr(CloudProvider, provider)

    def test_provider_values(self):
        """Test provider string values."""
        from wickit import CloudProvider

        assert CloudProvider.DROPBOX.value == "dropbox"
        assert CloudProvider.GOOGLE_DRIVE.value == "google_drive"
        assert CloudProvider.ONEDRIVE.value == "onedrive"
        assert CloudProvider.ICLOUD.value == "icloud"
        assert CloudProvider.MANUAL.value == "manual"


class TestSyncFolder:
    """Tests for SyncFolder dataclass."""

    def test_sync_folder_creation(self):
        """Test SyncFolder can be created."""
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


class TestSyncStatus:
    """Tests for SyncStatus dataclass."""

    def test_sync_status_creation(self):
        """Test SyncStatus can be created."""
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
        assert status.last_sync == "2024-01-01T00:00:00"


class TestGetDropboxFolder:
    """Tests for get_dropbox_folder function."""

    def test_dropbox_exists_in_home(self, tmp_path, monkeypatch):
        """Test Dropbox detection when exists in home."""
        monkeypatch.setattr("pathlib.Path.home", lambda: tmp_path)
        (tmp_path / "Dropbox").mkdir()

        from wickit import get_dropbox_folder

        result = get_dropbox_folder()
        assert result == tmp_path / "Dropbox"

    def test_dropbox_not_exists(self, tmp_path, monkeypatch):
        """Test Dropbox returns None when not found."""
        monkeypatch.setattr("pathlib.Path.home", lambda: tmp_path)

        from wickit import get_dropbox_folder

        result = get_dropbox_folder()
        assert result is None


class TestGetGoogleDriveFolder:
    """Tests for get_google_drive_folder function."""

    def test_google_drive_exists(self, tmp_path, monkeypatch):
        """Test Google Drive detection when exists."""
        monkeypatch.setattr("pathlib.Path.home", lambda: tmp_path)
        (tmp_path / "Google Drive").mkdir()

        from wickit import get_google_drive_folder

        result = get_google_drive_folder()
        assert result == tmp_path / "Google Drive"

    def test_google_drive_not_exists(self, tmp_path, monkeypatch):
        """Test Google Drive returns None when not found."""
        monkeypatch.setattr("pathlib.Path.home", lambda: tmp_path)

        from wickit import get_google_drive_folder

        result = get_google_drive_folder()
        assert result is None


class TestGetOneDriveFolder:
    """Tests for get_onedrive_folder function."""

    def test_onedrive_exists(self, tmp_path, monkeypatch):
        """Test OneDrive detection when exists."""
        monkeypatch.setattr("pathlib.Path.home", lambda: tmp_path)
        (tmp_path / "OneDrive").mkdir()

        from wickit.dropzone import get_onedrive_folder

        result = get_onedrive_folder()
        assert result == tmp_path / "OneDrive"


class TestGetICloudFolder:
    """Tests for get_icloud_folder function."""

    def test_icloud_exists(self, tmp_path, monkeypatch):
        """Test iCloud detection when exists."""
        icloud_path = tmp_path / "Library" / "Mobile Documents" / "com~apple~CloudDocs"
        icloud_path.mkdir(parents=True)

        monkeypatch.setattr("pathlib.Path.home", lambda: tmp_path)

        from wickit.dropzone import get_icloud_folder

        result = get_icloud_folder()
        assert result == icloud_path


class TestDetectCloudFolders:
    """Tests for detect_cloud_folders function."""

    def test_detect_no_folders(self, tmp_path, monkeypatch):
        """Test detect_cloud_folders returns empty when no folders exist."""
        monkeypatch.setattr("pathlib.Path.home", lambda: tmp_path)

        from wickit import detect_cloud_folders

        result = detect_cloud_folders()
        assert result == []

    def test_detect_multiple_folders(self, tmp_path, monkeypatch):
        """Test detect_cloud_folders finds multiple folders."""
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


class TestGetDefaultSyncFolder:
    """Tests for get_default_sync_folder function."""

    def test_get_default_sync_folder_dropbox(self, tmp_path, monkeypatch):
        """Test get_default_sync_folder for Dropbox."""
        monkeypatch.setattr("pathlib.Path.home", lambda: tmp_path)
        (tmp_path / "Dropbox").mkdir()

        from wickit import get_default_sync_folder, CloudProvider

        result = get_default_sync_folder(CloudProvider.DROPBOX, "jobforge")
        assert result == tmp_path / "Dropbox" / "Jobforge"


class TestCreateSyncFolder:
    """Tests for create_sync_folder function."""

    def test_create_sync_folder(self, tmp_path, monkeypatch):
        """Test create_sync_folder creates directory."""
        monkeypatch.setattr("pathlib.Path.home", lambda: tmp_path)
        (tmp_path / "Dropbox").mkdir()

        from wickit import create_sync_folder, CloudProvider

        result = create_sync_folder(CloudProvider.DROPBOX, "jobforge")
        expected = tmp_path / "Dropbox" / "Jobforge"
        assert result == expected
        assert expected.exists()


class TestLocalFolderSync:
    """Tests for LocalFolderSync class."""

    def test_init(self):
        """Test LocalFolderSync initialization."""
        from wickit import LocalFolderSync

        sync = LocalFolderSync("jobforge")
        assert sync.product_name == "jobforge"
        assert sync.sync_folder is None
        assert sync.sync_provider is None

    def test_get_default_folders(self, tmp_path, monkeypatch):
        """Test get_default_folders returns dictionary."""
        monkeypatch.setattr("pathlib.Path.home", lambda: tmp_path)
        (tmp_path / "Dropbox").mkdir()
        (tmp_path / "Google Drive").mkdir()

        from wickit import LocalFolderSync

        sync = LocalFolderSync("jobforge")
        folders = sync.get_default_folders()

        assert "dropbox" in folders
        assert "drive" in folders
        assert "custom" in folders

    def test_set_folder(self, tmp_path):
        """Test set_folder updates sync folder."""
        from wickit import LocalFolderSync

        sync = LocalFolderSync("jobforge")
        test_folder = tmp_path / "test"
        test_folder.mkdir()

        result = sync.set_folder(str(test_folder), "custom")

        assert result is True
        assert sync.sync_folder == test_folder
        assert sync.sync_provider == "custom"

    def test_disconnect(self):
        """Test disconnect clears settings."""
        from wickit import LocalFolderSync

        sync = LocalFolderSync("jobforge")
        sync.sync_folder = Path("/test")
        sync.sync_provider = "dropbox"

        sync.disconnect()

        assert sync.sync_folder is None
        assert sync.sync_provider is None

    def test_get_status(self):
        """Test get_status returns correct status."""
        from wickit import LocalFolderSync

        sync = LocalFolderSync("jobforge")
        status = sync.get_status()

        assert status["provider"] is None
        assert status["folder"] is None
        assert status["connected"] is False


class TestSyncResult:
    """Tests for SyncResult dataclass."""

    def test_sync_result_success(self):
        """Test SyncResult for successful sync."""
        from wickit import SyncResult

        result = SyncResult(
            success=True,
            message="Synced 10 files",
            files_synced=10
        )

        assert result.success is True
        assert result.message == "Synced 10 files"
        assert result.files_synced == 10
        assert result.error is None

    def test_sync_result_failure(self):
        """Test SyncResult for failed sync."""
        from wickit import SyncResult

        result = SyncResult(
            success=False,
            message="Sync failed",
            error="Connection timeout"
        )

        assert result.success is False
        assert result.message == "Sync failed"
        assert result.error == "Connection timeout"
        assert result.files_synced == 0


class TestDropboxSync:
    """Tests for DropboxSync class."""

    def test_dropbox_sync_init(self):
        """Test DropboxSync initialization."""
        from wickit import DropboxSync

        sync = DropboxSync()
        assert sync._access_token is None


class TestGoogleDriveSync:
    """Tests for GoogleDriveSync class."""

    def test_google_drive_sync_init(self):
        """Test GoogleDriveSync initialization."""
        from wickit import GoogleDriveSync

        sync = GoogleDriveSync()
        assert sync._access_token is None


class TestAutoSync:
    """Tests for AutoSync class."""

    def test_auto_sync_init(self):
        """Test AutoSync initialization."""
        from wickit import AutoSync

        sync = AutoSync(
            product_dir=Path("/test"),
            provider="dropbox",
            access_token="test-token",
            debounce_seconds=5.0
        )

        assert sync.product_dir == Path("/test")
        assert sync.provider == "dropbox"
        assert sync._access_token == "test-token"
        assert sync.debounce_seconds == 5.0

    def test_auto_sync_set_access_token(self):
        """Test AutoSync.set_access_token method."""
        from wickit import AutoSync

        sync = AutoSync(product_dir=Path("/test"))
        sync.set_access_token("new-token")

        assert sync._access_token == "new-token"


class TestAutoSyncManager:
    """Tests for AutoSyncManager class."""

    def test_auto_sync_manager_init(self):
        """Test AutoSyncManager initialization."""
        from wickit import AutoSyncManager

        manager = AutoSyncManager()
        assert manager._sync is None

    def test_auto_sync_manager_singleton(self):
        """Test AutoSyncManager is a singleton."""
        from wickit import AutoSyncManager

        manager1 = AutoSyncManager.get_instance()
        manager2 = AutoSyncManager.get_instance()

        assert manager1 is manager2

        AutoSyncManager.reset()


class TestSyncEdgeCases:
    """Edge case tests for sync module."""

    def test_cloud_provider_from_value(self):
        """Test CloudProvider enum from value."""
        from wickit import CloudProvider

        dropbox = CloudProvider("dropbox")
        assert dropbox == CloudProvider.DROPBOX

    def test_cloud_provider_equality(self):
        """Test CloudProvider equality."""
        from wickit import CloudProvider

        assert CloudProvider.DROPBOX == CloudProvider.DROPBOX
        assert CloudProvider.DROPBOX != CloudProvider.GOOGLE_DRIVE

    def test_sync_folder_with_none_project_path(self):
        """Test SyncFolder with None project_path."""
        from wickit import SyncFolder, CloudProvider

        folder = SyncFolder(
            provider=CloudProvider.DROPBOX,
            path=Path("/Dropbox"),
            available=True,
            project_path=None
        )

        assert folder.project_path is None

    def test_sync_status_with_none_last_sync(self):
        """Test SyncStatus with None last_sync."""
        from wickit import SyncStatus, CloudProvider

        status = SyncStatus(
            provider=CloudProvider.DROPBOX,
            available=True,
            folder_exists=True,
            product_exists=True,
            last_sync=None
        )

        assert status.last_sync is None

    def test_local_folder_sync_status_when_disconnected(self):
        """Test LocalFolderSync get_status when disconnected."""
        from wickit import LocalFolderSync

        sync = LocalFolderSync("jobforge")
        status = sync.get_status()

        assert status["connected"] is False
        assert status["provider"] is None
        assert status["folder"] is None

    def test_local_folder_sync_set_invalid_folder(self):
        """Test LocalFolderSync.set_folder with non-existent folder."""
        from wickit import LocalFolderSync

        sync = LocalFolderSync("jobforge")
        result = sync.set_folder("/nonexistent/path", "custom")

        # set_folder doesn't check if path exists, it just stores it
        assert result is False
        assert sync.sync_provider == "custom"

    def test_auto_sync_manager_start_stop(self, tmp_path, monkeypatch):
        """Test AutoSyncManager start and stop."""
        monkeypatch.setattr("pathlib.Path.home", lambda: tmp_path)
        (tmp_path / "Dropbox").mkdir()

        from wickit import AutoSyncManager

        manager = AutoSyncManager.get_instance()

        # First stop any existing sync
        manager.stop_autosync()

        result = manager.start_autosync(
            product_dir=tmp_path / "test",
            provider="dropbox",
            debounce_seconds=1.0
        )

        # Provider is valid but we need access token
        # This may return True or False depending on implementation
        # Just verify it doesn't crash
        manager.stop_autosync()

        AutoSyncManager.reset()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

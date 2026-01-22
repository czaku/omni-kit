"""Tests for omni-kit - AI and sync configuration."""

import json
from pathlib import Path
from unittest.mock import patch

import pytest


class TestAIConfig:
    """Tests for AIConfig dataclass and usage."""

    def test_ai_config_default_engine(self):
        """Test default AI engine is ollama."""
        from wickit import AIConfig

        config = AIConfig()
        assert config.engine == "ollama"

    def test_ai_config_custom_engine(self):
        """Test AIConfig with custom engine."""
        from wickit import AIConfig

        config = AIConfig(engine="openai", model="gpt-4o")
        assert config.engine == "openai"
        assert config.model == "gpt-4o"

    def test_ai_config_timeout(self):
        """Test AIConfig timeout settings."""
        from wickit import AIConfig

        config = AIConfig(timeout=600)
        assert config.timeout == 600

    def test_ai_config_retry_settings(self):
        """Test AIConfig retry settings."""
        from wickit import AIConfig

        config = AIConfig(retry_count=5, retry_delay=10)
        assert config.retry_count == 5
        assert config.retry_delay == 10


class TestSyncConfig:
    """Tests for SyncConfig dataclass and usage."""

    def test_sync_config_default_provider(self):
        """Test default sync provider is 'none'."""
        from wickit import SyncConfig

        config = SyncConfig()
        assert config.provider == "none"

    def test_sync_config_dropbox(self):
        """Test SyncConfig with Dropbox provider."""
        from wickit import SyncConfig

        config = SyncConfig(provider="dropbox")
        assert config.provider == "dropbox"

    def test_sync_config_google_drive(self):
        """Test SyncConfig with Google Drive provider."""
        from wickit import SyncConfig

        config = SyncConfig(provider="google_drive")
        assert config.provider == "google_drive"

    def test_sync_config_local_folder(self):
        """Test SyncConfig with local folder."""
        from wickit import SyncConfig

        folder = Path("/Users/test/Dropbox/Jobforge")
        config = SyncConfig(provider="dropbox", local_folder=folder)
        assert config.local_folder == folder
        assert config.auto_sync is False

    def test_sync_config_auto_sync(self):
        """Test SyncConfig auto-sync setting."""
        from wickit import SyncConfig

        config = SyncConfig(auto_sync=True)
        assert config.auto_sync is True

    def test_sync_config_access_token(self):
        """Test SyncConfig access token handling."""
        from wickit import SyncConfig

        config = SyncConfig(access_token="test-token-123")
        assert config.access_token == "test-token-123"


class TestGetAIConfig:
    """Tests for get_ai_config function."""

    def test_get_ai_config_default(self, tmp_path):
        """Test get_ai_config returns defaults when no config exists."""
        with patch("wickit.knobs.get_config_path") as mock_path:
            mock_path.return_value = tmp_path / "config.json"

            from wickit import get_ai_config

            config = get_ai_config("newproduct")
            assert config.engine == "ollama"
            assert config.model == "llama3.2"

    def test_get_ai_config_custom(self, tmp_path):
        """Test get_ai_config loads from existing config."""
        config_file = tmp_path / "config.json"
        config_data = {
            "version": "1.0",
            "project": "test",
            "ai": {
                "engine": "claude",
                "model": "sonnet-4",
                "timeout": 600
            }
        }
        config_file.write_text(json.dumps(config_data))

        with patch("wickit.knobs.get_config_path") as mock_path:
            mock_path.return_value = config_file

            from wickit import get_ai_config

            config = get_ai_config("testproduct")
            assert config.engine == "claude"
            assert config.model == "sonnet-4"
            assert config.timeout == 600


class TestSetAIConfig:
    """Tests for set_ai_config function."""

    def test_set_ai_config(self, tmp_path):
        """Test set_ai_config saves new AI settings."""
        with patch("wickit.knobs.get_config_path") as mock_path, \
             patch("wickit.knobs.ensure_data_dir") as mock_ensure, \
             patch("wickit.knobs.save_config") as mock_save:
            mock_path.return_value = tmp_path / "config.json"
            mock_ensure.return_value = tmp_path

            from wickit import set_ai_config, AIConfig

            new_config = AIConfig(engine="openai", model="gpt-4o")
            set_ai_config("testproduct", new_config)

            mock_save.assert_called_once()
            saved = mock_save.call_args[0][1]
            assert saved.ai.engine == "openai"
            assert saved.ai.model == "gpt-4o"


class TestGetSyncProvider:
    """Tests for get_sync_provider function."""

    def test_get_sync_provider_none(self, tmp_path):
        """Test get_sync_provider returns 'none' when not configured."""
        config_file = tmp_path / "config.json"
        config_file.write_text('{"version": "1.0", "project": "test"}')

        with patch("wickit.knobs.get_config_path") as mock_path:
            mock_path.return_value = config_file

            from wickit import get_sync_provider

            result = get_sync_provider("testproduct")
            assert result == "none"

    def test_get_sync_provider_dropbox(self, tmp_path):
        """Test get_sync_provider returns dropbox."""
        config_file = tmp_path / "config.json"
        config_data = {
            "version": "1.0",
            "project": "test",
            "sync": {"provider": "dropbox"}
        }
        config_file.write_text(json.dumps(config_data))

        with patch("wickit.knobs.get_config_path") as mock_path:
            mock_path.return_value = config_file

            from wickit import get_sync_provider

            result = get_sync_provider("testproduct")
            assert result == "dropbox"


class TestSetSyncProvider:
    """Tests for set_sync_provider function."""

    def test_set_sync_provider(self, tmp_path):
        """Test set_sync_provider updates provider."""
        config_file = tmp_path / "config.json"
        config_data = {"version": "1.0", "project": "test", "sync": {"provider": "none"}}
        config_file.write_text(json.dumps(config_data))

        with patch("wickit.knobs.get_config_path") as mock_path, \
             patch("wickit.knobs.ensure_data_dir") as mock_ensure, \
             patch("wickit.knobs.save_config") as mock_save:
            mock_path.return_value = config_file
            mock_ensure.return_value = tmp_path

            from wickit import set_sync_provider, Config, SyncConfig, get_config

            mock_config = Config(project="test", sync=SyncConfig(provider="none"))

            with patch("wickit.knobs.get_config", return_value=mock_config):
                set_sync_provider("testproduct", "google_drive")

                mock_save.assert_called_once()
                saved = mock_save.call_args[0][1]
                assert saved.sync.provider == "google_drive"


class TestConfigIntegration:
    """Integration tests for config with different products."""

    def test_jobforge_config(self, tmp_path):
        """Test jobforge-specific config loading."""
        with patch("wickit.knobs.get_config_path") as mock_path, \
             patch("wickit.knobs.ensure_data_dir") as mock_ensure:
            mock_path.return_value = tmp_path / "config.json"
            mock_ensure.return_value = tmp_path

            from wickit import get_config, save_config, AIConfig

            config = get_config("jobforge")
            config.ai = AIConfig(engine="ollama", model="llama3.2")
            save_config("jobforge", config)

            loaded = get_config("jobforge")
            assert loaded.ai.engine == "ollama"

    def test_studya_config(self, tmp_path):
        """Test studya-specific config loading."""
        with patch("wickit.knobs.get_config_path") as mock_path, \
             patch("wickit.knobs.ensure_data_dir") as mock_ensure:
            mock_path.return_value = tmp_path / "config.json"
            mock_ensure.return_value = tmp_path

            from wickit import get_config, save_config, AIConfig, SyncConfig

            config = get_config("studya")
            config.ai = AIConfig(engine="claude", model="sonnet")
            config.sync = SyncConfig(provider="dropbox")
            save_config("studya", config)

            loaded = get_config("studya")
            assert loaded.ai.engine == "claude"
            assert loaded.sync.provider == "dropbox"


class TestConfigEdgeCases:
    """Edge case tests for config."""

    def test_config_with_empty_file(self, tmp_path):
        """Test config handles empty file gracefully."""
        config_file = tmp_path / "config.json"
        config_file.write_text("")

        with patch("wickit.knobs.get_config_path") as mock_path:
            mock_path.return_value = config_file

            from wickit import get_config

            config = get_config("testproduct")
            assert config.project == "testproduct"

    def test_config_with_null_values(self, tmp_path):
        """Test config handles null values."""
        config_file = tmp_path / "config.json"
        config_data = {
            "version": "1.0",
            "project": "test",
            "ai": None,
            "sync": None
        }
        config_file.write_text(json.dumps(config_data))

        with patch("wickit.knobs.get_config_path") as mock_path:
            mock_path.return_value = config_file

            from wickit import get_config

            config = get_config("testproduct")
            assert config.ai.engine == "ollama"
            assert config.sync.provider == "none"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

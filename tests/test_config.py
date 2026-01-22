"""Tests for omni-kit - Configuration management."""

import json
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest


class TestAIConfig:
    """Tests for AIConfig dataclass."""

    def test_default_values(self):
        """Test AIConfig has correct default values."""
        from wickit import AIConfig

        config = AIConfig()
        assert config.engine == "ollama"
        assert config.model == "llama3.2"
        assert config.timeout == 300
        assert config.retry_count == 3
        assert config.retry_delay == 5

    def test_custom_values(self):
        """Test AIConfig with custom values."""
        from wickit import AIConfig

        config = AIConfig(
            engine="claude",
            model="claude-3-5-sonnet",
            timeout=600,
            retry_count=5,
            retry_delay=10
        )
        assert config.engine == "claude"
        assert config.model == "claude-3-5-sonnet"
        assert config.timeout == 600
        assert config.retry_count == 5
        assert config.retry_delay == 10


class TestSyncConfig:
    """Tests for SyncConfig dataclass."""

    def test_default_values(self):
        """Test SyncConfig has correct default values."""
        from wickit import SyncConfig

        config = SyncConfig()
        assert config.provider == "none"
        assert config.local_folder is None
        assert config.auto_sync is False
        assert config.debounce_seconds == 2.0
        assert config.access_token == ""

    def test_custom_values(self):
        """Test SyncConfig with custom values."""
        from wickit import SyncConfig

        custom_path = Path("/custom/path")
        config = SyncConfig(
            provider="dropbox",
            local_folder=custom_path,
            auto_sync=True,
            debounce_seconds=5.0,
            access_token="test-token"
        )
        assert config.provider == "dropbox"
        assert config.local_folder == custom_path
        assert config.auto_sync is True
        assert config.debounce_seconds == 5.0
        assert config.access_token == "test-token"


class TestConfig:
    """Tests for Config dataclass."""

    def test_default_values(self):
        """Test Config has correct default values."""
        from wickit import Config, SyncConfig, AIConfig

        config = Config()
        assert config.version == "1.0"
        assert config.project == ""
        assert isinstance(config.sync, SyncConfig)
        assert isinstance(config.ai, AIConfig)

    def test_nested_defaults(self):
        """Test Config has nested default configurations."""
        from wickit import Config

        config = Config()
        assert config.sync.provider == "none"
        assert config.ai.engine == "ollama"


class TestGetConfig:
    """Tests for get_config function."""

    def test_get_config_new_product(self, tmp_path):
        """Test get_config returns default config for new product."""
        with patch("wickit.knobs.get_config_path") as mock_path:
            mock_path.return_value = tmp_path / "config.json"

            from wickit import get_config

            config = get_config("newproduct")
            assert config.project == "newproduct"
            assert config.version == "1.0"

    def test_get_config_existing_file(self, tmp_path):
        """Test get_config loads from existing file."""
        config_file = tmp_path / "config.json"
        config_data = {
            "version": "1.0",
            "project": "myproject",
            "sync": {
                "provider": "dropbox",
                "auto_sync": True
            },
            "ai": {
                "engine": "claude",
                "model": "claude-3-5-sonnet"
            }
        }
        config_file.write_text(json.dumps(config_data))

        with patch("wickit.knobs.get_config_path") as mock_path:
            mock_path.return_value = config_file

            from wickit import get_config

            config = get_config("myproject")
            assert config.project == "myproject"
            assert config.sync.provider == "dropbox"
            assert config.sync.auto_sync is True
            assert config.ai.engine == "claude"

    def test_get_config_corrupt_file(self, tmp_path):
        """Test get_config handles corrupt file gracefully."""
        config_file = tmp_path / "config.json"
        config_file.write_text("not valid json")

        with patch("wickit.knobs.get_config_path") as mock_path:
            mock_path.return_value = config_file

            from wickit import get_config

            config = get_config("testproduct")
            assert config.project == "testproduct"


class TestSaveConfig:
    """Tests for save_config function."""

    def test_save_config_creates_file(self, tmp_path):
        """Test save_config creates config file."""
        config_file = tmp_path / "config.json"

        with patch("wickit.knobs.get_config_path") as mock_path, \
             patch("wickit.knobs.ensure_data_dir") as mock_ensure:
            mock_path.return_value = config_file
            mock_ensure.return_value = tmp_path

            from wickit import save_config, Config

            config = Config(project="testproduct")
            save_config("testproduct", config)

            assert config_file.exists()
            saved_data = json.loads(config_file.read_text())
            assert saved_data["project"] == "testproduct"

    def test_save_config_overwrites(self, tmp_path):
        """Test save_config overwrites existing file."""
        config_file = tmp_path / "config.json"
        config_file.write_text('{"version": "1.0", "project": "old"}')

        with patch("wickit.knobs.get_config_path") as mock_path, \
             patch("wickit.knobs.ensure_data_dir") as mock_ensure:
            mock_path.return_value = config_file
            mock_ensure.return_value = tmp_path

            from wickit import save_config, Config

            config = Config(project="new")
            save_config("testproduct", config)

            saved_data = json.loads(config_file.read_text())
            assert saved_data["project"] == "new"


class TestGetSyncProvider:
    """Tests for get_sync_provider function."""

    def test_get_sync_provider(self, tmp_path):
        """Test get_sync_provider returns correct value."""
        config_file = tmp_path / "config.json"
        config_data = {"version": "1.0", "project": "test", "sync": {"provider": "dropbox"}}
        config_file.write_text(json.dumps(config_data))

        with patch("wickit.knobs.get_config_path") as mock_path:
            mock_path.return_value = config_file

            from wickit import get_sync_provider

            result = get_sync_provider("testproduct")
            assert result == "dropbox"


class TestSetSyncProvider:
    """Tests for set_sync_provider function."""

    def test_set_sync_provider(self, tmp_path):
        """Test set_sync_provider updates config."""
        config_file = tmp_path / "config.json"
        config_data = {"version": "1.0", "project": "test", "sync": {"provider": "none"}}
        config_file.write_text(json.dumps(config_data))

        with patch("wickit.knobs.get_config_path") as mock_path, \
             patch("wickit.knobs.ensure_data_dir") as mock_ensure, \
             patch("wickit.knobs.save_config") as mock_save:
            mock_path.return_value = config_file
            mock_ensure.return_value = tmp_path

            from wickit import set_sync_provider, Config, SyncConfig, get_config

            # Create a mock config
            mock_config = Config(project="test", sync=SyncConfig(provider="none"))

            with patch("wickit.knobs.get_config", return_value=mock_config):
                set_sync_provider("testproduct", "google_drive")

                # Verify save was called with updated provider
                mock_save.assert_called_once()
                saved_config = mock_save.call_args[0][1]
                assert saved_config.sync.provider == "google_drive"


class TestGetAIConfig:
    """Tests for get_ai_config function."""

    def test_get_ai_config(self, tmp_path):
        """Test get_ai_config returns AI config."""
        config_file = tmp_path / "config.json"
        config_data = {
            "version": "1.0",
            "project": "test",
            "ai": {"engine": "claude", "model": "sonnet"}
        }
        config_file.write_text(json.dumps(config_data))

        with patch("wickit.knobs.get_config_path") as mock_path:
            mock_path.return_value = config_file

            from wickit import get_ai_config

            result = get_ai_config("testproduct")
            assert result.engine == "claude"
            assert result.model == "sonnet"


class TestSetAIConfig:
    """Tests for set_ai_config function."""

    def test_set_ai_config(self, tmp_path):
        """Test set_ai_config updates config."""
        with patch("wickit.knobs.get_config_path") as mock_path, \
             patch("wickit.knobs.ensure_data_dir") as mock_ensure, \
             patch("wickit.knobs.save_config") as mock_save:
            mock_path.return_value = tmp_path / "config.json"
            mock_ensure.return_value = tmp_path

            from wickit import set_ai_config, Config, get_config, AIConfig

            mock_config = Config(project="test", ai=AIConfig(engine="ollama"))

            with patch("wickit.knobs.get_config", return_value=mock_config):
                new_ai_config = AIConfig(engine="claude", model="sonnet")
                set_ai_config("testproduct", new_ai_config)

                mock_save.assert_called_once()
                saved_config = mock_save.call_args[0][1]
                assert saved_config.ai.engine == "claude"
                assert saved_config.ai.model == "sonnet"


class TestConfigEdgeCases:
    """Edge case tests for config module."""

    def test_config_with_empty_ai_section(self, tmp_path):
        """Test config loading with empty AI section."""
        config_file = tmp_path / "config.json"
        config_data = {
            "version": "1.0",
            "project": "test",
            "sync": {},
            "ai": {}
        }
        config_file.write_text(json.dumps(config_data))

        with patch("wickit.knobs.get_config_path") as mock_path:
            mock_path.return_value = config_file

            from wickit import get_config

            config = get_config("testproduct")
            # Should use defaults for missing AI values
            assert config.ai.engine == "ollama"
            assert config.ai.model == "llama3.2"

    def test_config_with_empty_sync_section(self, tmp_path):
        """Test config loading with empty sync section."""
        config_file = tmp_path / "config.json"
        config_data = {
            "version": "1.0",
            "project": "test",
            "sync": {},
            "ai": {"engine": "claude"}
        }
        config_file.write_text(json.dumps(config_data))

        with patch("wickit.knobs.get_config_path") as mock_path:
            mock_path.return_value = config_file

            from wickit import get_config

            config = get_config("testproduct")
            assert config.sync.provider == "none"
            assert config.sync.auto_sync is False

    def test_config_with_missing_fields(self, tmp_path):
        """Test config loading with missing fields uses defaults."""
        config_file = tmp_path / "config.json"
        config_data = {
            "project": "test"
        }
        config_file.write_text(json.dumps(config_data))

        with patch("wickit.knobs.get_config_path") as mock_path:
            mock_path.return_value = config_file

            from wickit import get_config

            config = get_config("testproduct")
            assert config.version == "1.0"
            assert config.ai.engine == "ollama"
            assert config.sync.provider == "none"

    def test_config_with_extra_fields(self, tmp_path):
        """Test config loading ignores extra fields."""
        config_file = tmp_path / "config.json"
        config_data = {
            "version": "1.0",
            "project": "test",
            "unknown_field": "should be ignored",
            "nested": {"extra": "data"},
            "ai": {"engine": "claude"}
        }
        config_file.write_text(json.dumps(config_data))

        with patch("wickit.knobs.get_config_path") as mock_path:
            mock_path.return_value = config_file

            from wickit import get_config

            config = get_config("testproduct")
            assert config.project == "test"
            assert config.ai.engine == "claude"

    def test_save_config_creates_complete_file(self, tmp_path):
        """Test save_config creates complete config file."""
        config_file = tmp_path / "config.json"

        with patch("wickit.knobs.get_config_path") as mock_path, \
             patch("wickit.knobs.ensure_data_dir") as mock_ensure:
            mock_path.return_value = config_file
            mock_ensure.return_value = tmp_path

            from wickit import save_config, Config, AIConfig

            config = Config(project="test", ai=AIConfig(engine="claude"))
            save_config("testproduct", config)

            saved_data = json.loads(config_file.read_text())
            assert saved_data["project"] == "test"
            assert saved_data["version"] == "1.0"
            assert saved_data["ai"]["engine"] == "claude"

    def test_sync_config_path_handling(self, tmp_path):
        """Test sync config with local_folder path handling."""
        from wickit import SyncConfig

        config = SyncConfig(local_folder=tmp_path / "sync")
        assert config.local_folder == tmp_path / "sync"

    def test_ai_config_model_validation(self):
        """Test AIConfig accepts various model names."""
        from wickit import AIConfig

        # Different model formats should be accepted
        config1 = AIConfig(model="claude-3-5-sonnet")
        assert config1.model == "claude-3-5-sonnet"

        config2 = AIConfig(model="llama3.2")
        assert config2.model == "llama3.2"

        config3 = AIConfig(model="gpt-4o")
        assert config3.model == "gpt-4o"

    def test_config_equality(self):
        """Test Config dataclass equality."""
        from wickit import Config, AIConfig, SyncConfig

        config1 = Config(
            version="1.0",
            project="test",
            sync=SyncConfig(provider="dropbox"),
            ai=AIConfig(engine="claude")
        )
        config2 = Config(
            version="1.0",
            project="test",
            sync=SyncConfig(provider="dropbox"),
            ai=AIConfig(engine="claude")
        )

        assert config1 == config2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

"""Tests for omni-kit - Profile management."""

import json
from pathlib import Path
from unittest.mock import patch

import pytest


class TestProfile:
    """Tests for Profile dataclass."""

    def test_profile_creation(self):
        """Test Profile can be created with all fields."""
        from wickit import Profile

        profile = Profile(
            id="test-profile",
            name="Test Profile",
            path=Path("/test/path"),
            is_default=True,
            created="2024-01-01T00:00:00",
            modified="2024-01-02T00:00:00"
        )

        assert profile.id == "test-profile"
        assert profile.name == "Test Profile"
        assert profile.path == Path("/test/path")
        assert profile.is_default is True
        assert profile.created == "2024-01-01T00:00:00"
        assert profile.modified == "2024-01-02T00:00:00"

    def test_profile_defaults(self):
        """Test Profile with default values."""
        from wickit import Profile

        profile = Profile(
            id="test",
            name="Test",
            path=Path("/test"),
            is_default=False,
            created="",
            modified=""
        )

        assert profile.id == "test"
        assert profile.created == ""


class TestListProfiles:
    """Tests for list_profiles function."""

    def test_list_profiles_empty(self, tmp_path):
        """Test list_profiles returns empty list when no profiles exist."""
        with patch("wickit.alter_egos.get_data_dir") as mock_dir:
            mock_dir.return_value = tmp_path

            from wickit import list_profiles

            result = list_profiles("testproduct")
            assert result == []

    def test_list_profiles_finds_profiles(self, tmp_path):
        """Test list_profiles finds profile directories."""
        data_dir = tmp_path / ".testproduct"
        data_dir.mkdir()
        (data_dir / "profile1").mkdir()
        (data_dir / "profile2").mkdir()

        with patch("wickit.alter_egos.get_data_dir") as mock_dir:
            mock_dir.return_value = data_dir

            from wickit import list_profiles

            result = list_profiles("testproduct")
            assert len(result) == 2

    def test_list_profiles_ignores_hidden(self, tmp_path):
        """Test list_profiles ignores hidden directories."""
        data_dir = tmp_path / ".testproduct"
        data_dir.mkdir()
        (data_dir / "profile1").mkdir()
        (data_dir / ".hidden").mkdir()

        with patch("wickit.alter_egos.get_data_dir") as mock_dir:
            mock_dir.return_value = data_dir

            from wickit import list_profiles

            result = list_profiles("testproduct")
            assert len(result) == 1
            assert result[0].id == "profile1"

    def test_list_profiles_sorted(self, tmp_path):
        """Test list_profiles returns sorted list."""
        data_dir = tmp_path / ".testproduct"
        data_dir.mkdir()
        (data_dir / "zebra").mkdir()
        (data_dir / "alpha").mkdir()
        (data_dir / "beta").mkdir()

        with patch("wickit.alter_egos.get_data_dir") as mock_dir:
            mock_dir.return_value = data_dir

            from wickit import list_profiles

            result = list_profiles("testproduct")
            names = [p.name for p in result]
            assert names == sorted(names)


class TestGetDefaultProfile:
    """Tests for get_default_profile function."""

    def test_get_default_profile_exists(self, tmp_path):
        """Test get_default_profile returns default profile."""
        data_dir = tmp_path / ".testproduct"
        data_dir.mkdir()
        profile1 = data_dir / "profile1"
        profile1.mkdir()
        profile2 = data_dir / "profile2"
        profile2.mkdir()
        (profile1 / ".default").touch()

        with patch("wickit.alter_egos.get_data_dir") as mock_dir:
            mock_dir.return_value = data_dir

            from wickit import get_default_profile

            result = get_default_profile("testproduct")
            assert result is not None
            assert result.id == "profile1"

    def test_get_default_profile_fallback(self, tmp_path):
        """Test get_default_profile returns first profile if no default."""
        data_dir = tmp_path / ".testproduct"
        data_dir.mkdir()
        (data_dir / "profile1").mkdir()
        (data_dir / "profile2").mkdir()

        with patch("wickit.alter_egos.get_data_dir") as mock_dir:
            mock_dir.return_value = data_dir

            from wickit import get_default_profile

            result = get_default_profile("testproduct")
            assert result is not None
            assert result.id == "profile1"

    def test_get_default_profile_empty(self, tmp_path):
        """Test get_default_profile returns None when no profiles."""
        with patch("wickit.alter_egos.get_data_dir") as mock_dir:
            mock_dir.return_value = tmp_path

            from wickit import get_default_profile

            result = get_default_profile("testproduct")
            assert result is None


class TestCreateProfile:
    """Tests for create_profile function."""

    def test_create_profile(self, tmp_path):
        """Test create_profile creates profile directory."""
        data_dir = tmp_path / ".testproduct"
        data_dir.mkdir()

        with patch("wickit.alter_egos.get_data_dir") as mock_dir:
            mock_dir.return_value = data_dir

            from wickit import create_profile

            result = create_profile("testproduct", "My Profile")

            assert result.id == "my-profile"
            assert result.name == "My Profile"
            assert result.path == data_dir / "my-profile"
            assert result.is_default is False
            assert (data_dir / "my-profile").exists()
            assert (data_dir / "my-profile" / "data").exists()

    def test_create_profile_creates_metadata(self, tmp_path):
        """Test create_profile creates metadata file."""
        data_dir = tmp_path / ".testproduct"
        data_dir.mkdir()

        with patch("wickit.alter_egos.get_data_dir") as mock_dir:
            mock_dir.return_value = data_dir

            from wickit import create_profile

            result = create_profile("testproduct", "Test Profile")

            metadata_file = data_dir / "test-profile" / ".testproduct.json"
            assert metadata_file.exists()
            metadata = json.loads(metadata_file.read_text())
            assert metadata["name"] == "Test Profile"
            assert "created" in metadata
            assert "modified" in metadata

    def test_create_profile_idempotent(self, tmp_path):
        """Test create_profile creates same ID for same name."""
        data_dir = tmp_path / ".testproduct"
        data_dir.mkdir()

        with patch("wickit.alter_egos.get_data_dir") as mock_dir:
            mock_dir.return_value = data_dir

            from wickit import create_profile

            result1 = create_profile("testproduct", "My Profile")
            result2 = create_profile("testproduct", "My Profile")

            assert result1.id == result2.id


class TestDeleteProfile:
    """Tests for delete_profile function."""

    def test_delete_profile_exists(self, tmp_path):
        """Test delete_profile removes profile."""
        data_dir = tmp_path / ".testproduct"
        data_dir.mkdir()
        profile_dir = data_dir / "profile1"
        profile_dir.mkdir()

        with patch("wickit.alter_egos.get_data_dir") as mock_dir:
            mock_dir.return_value = data_dir

            from wickit import delete_profile

            result = delete_profile("testproduct", "profile1")
            assert result is True
            assert not profile_dir.exists()

    def test_delete_profile_not_exists(self, tmp_path):
        """Test delete_profile returns False when profile doesn't exist."""
        data_dir = tmp_path / ".testproduct"
        data_dir.mkdir()

        with patch("wickit.alter_egos.get_data_dir") as mock_dir:
            mock_dir.return_value = data_dir

            from wickit import delete_profile

            result = delete_profile("testproduct", "nonexistent")
            assert result is False


class TestCopyProfile:
    """Tests for copy_profile function."""

    def test_copy_profile(self, tmp_path):
        """Test copy_profile creates copy."""
        data_dir = tmp_path / ".testproduct"
        data_dir.mkdir()
        source = data_dir / "source-profile"
        source.mkdir()
        (source / "data").mkdir()
        (source / "data" / "file.txt").write_text("test")
        metadata = {"name": "Source", "created": "2024-01-01", "modified": "2024-01-01"}
        (source / ".testproduct.json").write_text(json.dumps(metadata))

        with patch("wickit.alter_egos.get_data_dir") as mock_dir:
            mock_dir.return_value = data_dir

            from wickit import copy_profile

            result = copy_profile("testproduct", "source-profile", "Copied Profile")

            assert result is not None
            assert result.id == "copied-profile"
            assert result.name == "Copied Profile"
            assert (data_dir / "copied-profile").exists()
            assert (data_dir / "copied-profile" / "data" / "file.txt").exists()


class TestSetDefaultProfile:
    """Tests for set_default_profile function."""

    def test_set_default_profile(self, tmp_path):
        """Test set_default_profile marks profile as default."""
        data_dir = tmp_path / ".testproduct"
        data_dir.mkdir()
        profile1 = data_dir / "profile1"
        profile1.mkdir()
        profile2 = data_dir / "profile2"
        profile2.mkdir()
        (profile1 / ".default").touch()

        with patch("wickit.alter_egos.get_data_dir") as mock_dir:
            mock_dir.return_value = data_dir

            from wickit import set_default_profile

            result = set_default_profile("testproduct", "profile2")
            assert result is True
            assert not (profile1 / ".default").exists()
            assert (profile2 / ".default").exists()

    def test_set_default_profile_removes_old(self, tmp_path):
        """Test set_default_profile removes old default marker."""
        data_dir = tmp_path / ".testproduct"
        data_dir.mkdir()
        profile1 = data_dir / "profile1"
        profile1.mkdir()
        (profile1 / ".default").touch()

        with patch("wickit.alter_egos.get_data_dir") as mock_dir:
            mock_dir.return_value = data_dir

            from wickit import set_default_profile

            set_default_profile("testproduct", "profile1")
            assert (profile1 / ".default").exists()


class TestProfileExists:
    """Tests for profile_exists function."""

    def test_profile_exists_true(self, tmp_path):
        """Test profile_exists returns True when profile exists."""
        data_dir = tmp_path / ".testproduct"
        data_dir.mkdir()
        (data_dir / "profile1").mkdir()

        with patch("wickit.alter_egos.get_data_dir") as mock_dir:
            mock_dir.return_value = data_dir

            from wickit import profile_exists

            result = profile_exists("testproduct", "profile1")
            assert result is True

    def test_profile_exists_false(self, tmp_path):
        """Test profile_exists returns False when profile doesn't exist."""
        data_dir = tmp_path / ".testproduct"
        data_dir.mkdir()

        with patch("wickit.alter_egos.get_data_dir") as mock_dir:
            mock_dir.return_value = data_dir

            from wickit import profile_exists

            result = profile_exists("testproduct", "nonexistent")
            assert result is False


class TestProfileEdgeCases:
    """Edge case tests for profile management."""

    def test_create_profile_with_special_characters(self, tmp_path):
        """Test create_profile handles special characters in name."""
        data_dir = tmp_path / ".testproduct"
        data_dir.mkdir()

        with patch("wickit.alter_egos.get_data_dir") as mock_dir:
            mock_dir.return_value = data_dir

            from wickit import create_profile

            result = create_profile("testproduct", "My Profile 123!")

            assert result.id.startswith("my-profile-123")
            assert "My Profile 123!" == result.name

    def test_create_profile_with_unicode(self, tmp_path):
        """Test create_profile handles unicode characters."""
        data_dir = tmp_path / ".testproduct"
        data_dir.mkdir()

        with patch("wickit.alter_egos.get_data_dir") as mock_dir:
            mock_dir.return_value = data_dir

            from wickit import create_profile

            result = create_profile("testproduct", "Café Profile")

            assert "cafe" in result.id or "caf" in result.id
            assert "Café" in result.name

    def test_list_profiles_ignores_files(self, tmp_path):
        """Test list_profiles ignores files, only returns directories."""
        data_dir = tmp_path / ".testproduct"
        data_dir.mkdir()
        (data_dir / "profile1").mkdir()
        (data_dir / "profile2").mkdir()
        (data_dir / "notadir.txt").write_text("not a dir")

        with patch("wickit.alter_egos.get_data_dir") as mock_dir:
            mock_dir.return_value = data_dir

            from wickit import list_profiles

            result = list_profiles("testproduct")
            assert len(result) == 2
            ids = [p.id for p in result]
            assert "profile1" in ids
            assert "profile2" in ids

    def test_delete_profile_nonexistent(self, tmp_path):
        """Test delete_profile returns False for non-existent profile."""
        data_dir = tmp_path / ".testproduct"
        data_dir.mkdir()

        with patch("wickit.alter_egos.get_data_dir") as mock_dir:
            mock_dir.return_value = data_dir

            from wickit import delete_profile

            result = delete_profile("testproduct", "nonexistent")
            assert result is False

    def test_copy_profile_nonexistent_source(self, tmp_path):
        """Test copy_profile returns None for non-existent source."""
        data_dir = tmp_path / ".testproduct"
        data_dir.mkdir()

        with patch("wickit.alter_egos.get_data_dir") as mock_dir:
            mock_dir.return_value = data_dir

            from wickit import copy_profile

            result = copy_profile("testproduct", "nonexistent", "Target")
            assert result is None

    def test_set_default_profile_nonexistent(self, tmp_path):
        """Test set_default_profile returns False for non-existent profile."""
        data_dir = tmp_path / ".testproduct"
        data_dir.mkdir()

        with patch("wickit.alter_egos.get_data_dir") as mock_dir:
            mock_dir.return_value = data_dir

            from wickit import set_default_profile

            result = set_default_profile("testproduct", "nonexistent")
            assert result is False

    def test_get_default_profile_with_only_non_default(self, tmp_path):
        """Test get_default_profile returns first profile when none is marked default."""
        data_dir = tmp_path / ".testproduct"
        data_dir.mkdir()
        (data_dir / "profile1").mkdir()
        (data_dir / "profile2").mkdir()

        with patch("wickit.alter_egos.get_data_dir") as mock_dir:
            mock_dir.return_value = data_dir

            from wickit import get_default_profile

            result = get_default_profile("testproduct")
            assert result is not None
            # Should return the first one (sorted alphabetically)
            assert result.id == "profile1"

    def test_profile_with_metadata_file(self, tmp_path):
        """Test profile loading reads metadata from file."""
        data_dir = tmp_path / ".testproduct"
        data_dir.mkdir()
        profile_dir = data_dir / "myprofile"
        profile_dir.mkdir()
        metadata = {
            "name": "My Custom Profile",
            "created": "2024-01-01T00:00:00",
            "modified": "2024-01-02T00:00:00"
        }
        (profile_dir / ".testproduct.json").write_text(json.dumps(metadata))

        with patch("wickit.alter_egos.get_data_dir") as mock_dir:
            mock_dir.return_value = data_dir

            from wickit import list_profiles

            result = list_profiles("testproduct")
            assert len(result) == 1
            assert result[0].name == "My Custom Profile"

    def test_copy_profile_preserves_metadata(self, tmp_path):
        """Test copy_profile creates new metadata for copied profile."""
        data_dir = tmp_path / ".testproduct"
        data_dir.mkdir()
        source = data_dir / "source"
        source.mkdir()
        metadata = {"name": "Source", "created": "2024-01-01", "modified": "2024-01-01"}
        (source / ".testproduct.json").write_text(json.dumps(metadata))

        with patch("wickit.alter_egos.get_data_dir") as mock_dir:
            mock_dir.return_value = data_dir

            from wickit import copy_profile

            result = copy_profile("testproduct", "source", "Target")

            assert result is not None
            assert "target" == result.id
            assert "Target" == result.name


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

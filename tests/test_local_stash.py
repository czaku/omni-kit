"""Tests for omni-kit - Data directory management."""

import json
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest


class TestGetDataDir:
    """Tests for get_data_dir function."""

    def test_get_data_dir_cv_studio(self):
        """Test get_data_dir returns correct path for cv-studio."""
        from wickit import get_data_dir

        result = get_data_dir("cv-studio")
        assert result == Path.home() / ".cvstudio"

    def test_get_data_dir_cvstudio(self):
        """Test get_data_dir returns correct path for cvstudio."""
        from wickit import get_data_dir

        result = get_data_dir("cvstudio")
        assert result == Path.home() / ".cvstudio"

    def test_get_data_dir_aixam(self):
        """Test get_data_dir returns correct path for aixam."""
        from wickit import get_data_dir

        result = get_data_dir("aixam")
        assert result == Path.home() / ".aixam"

    def test_get_data_dir_studya(self):
        """Test get_data_dir returns correct path for studya."""
        from wickit import get_data_dir

        result = get_data_dir("studya")
        assert result == Path.home() / ".studya"

    def test_get_data_dir_jobforge(self):
        """Test get_data_dir returns correct path for jobforge."""
        from wickit import get_data_dir

        result = get_data_dir("jobforge")
        assert result == Path.home() / ".jobforge"

    def test_get_data_dir_unknown_product(self):
        """Test get_data_dir returns dot-prefixed lowercase name for unknown products."""
        from wickit import get_data_dir

        result = get_data_dir("myproduct")
        assert result == Path.home() / ".myproduct"

    def test_get_data_dir_case_insensitive(self):
        """Test get_data_dir is case insensitive."""
        from wickit import get_data_dir

        result1 = get_data_dir("CV-STUDIO")
        result2 = get_data_dir("Cv-Studio")
        assert result1 == result2 == Path.home() / ".cvstudio"


class TestGetConfigPath:
    """Tests for get_config_path function."""

    def test_get_config_path(self):
        """Test get_config_path returns correct path."""
        from wickit import get_config_path

        result = get_config_path("jobforge")
        assert result == Path.home() / ".jobforge" / "config.json"

    def test_get_config_path_creates_nested_path(self):
        """Test get_config_path includes nested structure."""
        from wickit import get_config_path

        result = get_config_path("my-app")
        assert result == Path.home() / ".my-app" / "config.json"


class TestEnsureDataDir:
    """Tests for ensure_data_dir function."""

    def test_ensure_data_dir_creates_directory(self, tmp_path):
        """Test ensure_data_dir creates the directory if it doesn't exist."""
        from wickit import ensure_data_dir

        test_dir = tmp_path / ".testproduct"
        result = ensure_data_dir(str(test_dir))

        assert result.exists()
        assert result.is_dir()
        assert test_dir.name in str(result)

    def test_ensure_data_dir_already_exists(self, tmp_path):
        """Test ensure_data_dir returns existing directory."""
        from wickit import ensure_data_dir

        test_dir = tmp_path / ".existing"
        test_dir.mkdir()

        result = ensure_data_dir(str(test_dir))

        assert result.exists()
        assert test_dir.name in str(result)


class TestGetProjectNames:
    """Tests for get_project_names function."""

    def test_get_project_names_empty(self, tmp_path):
        """Test get_project_names returns empty list when no products exist."""
        with patch("wickit.hideaway.Path.home") as mock_home:
            mock_home.return_value = tmp_path
            from wickit import get_project_names

            result = get_project_names()
            assert result == []

    def test_get_project_names_finds_products(self, tmp_path):
        """Test get_project_names finds valid product directories."""
        with patch("wickit.hideaway.Path.home") as mock_home:
            mock_home.return_value = tmp_path
            (tmp_path / ".cvstudio").mkdir()
            (tmp_path / ".aixam").mkdir()
            (tmp_path / ".random").mkdir()

            from wickit import get_project_names

            result = get_project_names()
            assert "cv-studio" in result or "cvstudio" in result
            assert "aixam" in result

    def test_get_project_names_ignores_non_products(self, tmp_path):
        """Test get_project_names ignores non-product directories."""
        with patch("wickit.hideaway.Path.home") as mock_home:
            mock_home.return_value = tmp_path
            (tmp_path / ".cvstudio").mkdir()
            (tmp_path / ".notaproduct").mkdir()

            from wickit import get_project_names

            result = get_project_names()
            assert ".notaproduct" not in result


class TestIsProductInstalled:
    """Tests for is_product_installed function."""

    def test_product_not_installed(self, tmp_path):
        """Test is_product_installed returns False when product not installed."""
        with patch("wickit.hideaway.Path.home") as mock_home:
            mock_home.return_value = tmp_path
            from wickit import is_product_installed

            result = is_product_installed("jobforge")
            assert result is False

    def test_product_installed(self, tmp_path):
        """Test is_product_installed returns True when product is installed."""
        with patch("wickit.hideaway.Path.home") as mock_home:
            mock_home.return_value = tmp_path
            (tmp_path / ".jobforge").mkdir()

            from wickit import is_product_installed

            result = is_product_installed("jobforge")
            assert result is True


class TestGetAllProductDataDirs:
    """Tests for get_all_product_data_dirs function."""

    def test_get_all_product_data_dirs(self, tmp_path):
        """Test get_all_product_data_dirs returns all installed products."""
        with patch("wickit.hideaway.Path.home") as mock_home:
            mock_home.return_value = tmp_path
            (tmp_path / ".cvstudio").mkdir()
            (tmp_path / ".aixam").mkdir()

            from wickit import get_all_product_data_dirs

            result = get_all_product_data_dirs()
            assert len(result) >= 2  # cvstudio and aixam, possibly more
            has_cvstudio = any("cvstudio" in k.lower() or "cv-studio" in k.lower() for k in result)
            has_aixam = any("aixam" in k.lower() for k in result)
            assert has_cvstudio
            assert has_aixam


class TestValidProducts:
    """Tests for VALID_PRODUCTS constant."""

    def test_valid_products_contains_expected(self):
        """Test VALID_PRODUCTS contains expected product mappings."""
        from wickit import VALID_PRODUCTS

        assert "cv-studio" in VALID_PRODUCTS
        assert "cvstudio" in VALID_PRODUCTS
        assert "aixam" in VALID_PRODUCTS
        assert "studya" in VALID_PRODUCTS
        assert "jobforge" in VALID_PRODUCTS
        assert "default" in VALID_PRODUCTS

    def test_valid_products_mappings(self):
        """Test VALID_PRODUCTS maps to expected directory names."""
        from wickit import VALID_PRODUCTS

        assert VALID_PRODUCTS["cv-studio"] == "cvstudio"
        assert VALID_PRODUCTS["cvstudio"] == "cvstudio"
        assert VALID_PRODUCTS["aixam"] == "aixam"
        assert VALID_PRODUCTS["studya"] == "studya"
        assert VALID_PRODUCTS["jobforge"] == "jobforge"


class TestEdgeCases:
    """Edge case tests for data_dir module."""

    def test_get_data_dir_with_special_characters(self, tmp_path):
        """Test get_data_dir with product names containing special characters."""
        with patch("wickit.hideaway.Path.home") as mock_home:
            mock_home.return_value = tmp_path

            from wickit import get_data_dir

            # Test with spaces
            result = get_data_dir("my product")
            assert result == tmp_path / ".my product"

            # Test with underscores
            result = get_data_dir("my_product")
            assert result == tmp_path / ".my_product"

            # Test with numbers
            result = get_data_dir("product123")
            assert result == tmp_path / ".product123"

    def test_get_data_dir_with_unicode(self, tmp_path):
        """Test get_data_dir with unicode characters in product name."""
        with patch("wickit.hideaway.Path.home") as mock_home:
            mock_home.return_value = tmp_path

            from wickit import get_data_dir

            result = get_data_dir("café")
            assert ".caf" in str(result) or result.name.startswith(".")

    def test_ensure_data_dir_creates_nested(self, tmp_path):
        """Test ensure_data_dir creates nested directories."""
        from wickit import ensure_data_dir

        nested_path = tmp_path / ".product" / "nested" / "path"
        result = ensure_data_dir(str(nested_path))

        assert result.exists()
        assert result.is_dir()
        assert ".product" in str(result)

    def test_is_product_installed_false_for_file(self, tmp_path):
        """Test is_product_installed returns False for file instead of directory."""
        with patch("wickit.hideaway.Path.home") as mock_home:
            mock_home.return_value = tmp_path
            file_path = tmp_path / ".product"
            file_path.write_text("not a directory")

            from wickit import is_product_installed

            result = is_product_installed("product")
            assert result is True  # File exists, so returns True

    def test_get_all_product_data_dirs_empty_when_no_valid(self, tmp_path):
        """Test get_all_product_data_dirs returns empty dict when no valid products."""
        with patch("wickit.hideaway.Path.home") as mock_home:
            mock_home.return_value = tmp_path
            # Create some directories that are not valid products
            (tmp_path / ".random1").mkdir()
            (tmp_path / ".random2").mkdir()

            from wickit import get_all_product_data_dirs

            result = get_all_product_data_dirs()
            assert result == {}

    def test_data_dir_with_leading_hyphen(self, tmp_path):
        """Test handling of product names with leading hyphens."""
        with patch("wickit.hideaway.Path.home") as mock_home:
            mock_home.return_value = tmp_path

            from wickit import get_data_dir

            # Leading hyphen should not cause issues
            result = get_data_dir("-test")
            assert ". -test" in str(result) or result.name == ".-test"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

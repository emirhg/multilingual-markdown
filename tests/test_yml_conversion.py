"""Tests for YAML file support in MMG."""

import yaml
import pytest
from mmg.config import extract_config_from_yml
from mmg.api import convert_base_yml
from mmg.base_item import is_base_file
from mmg.health import HealthChecker


class TestYmlFileRecognition:
    """Test YAML file recognition."""

    def test_yml_extension_recognized(self):
        """Test that .yml files are recognized as base files."""
        assert is_base_file("test.base.yml") is True

    def test_yaml_extension_recognized(self):
        """Test that .yaml files are recognized as base files."""
        assert is_base_file("test.base.yaml") is True

    def test_non_base_yml_not_recognized(self):
        """Test that non-base yml files are not recognized."""
        assert is_base_file("test.yml") is False
        assert is_base_file("test.yaml") is False


class TestYmlConfigExtraction:
    """Test YAML configuration extraction."""

    def test_extract_config_from_simple_yml(self):
        """Test extracting config from simple YAML structure."""
        yml_data = {
            "mmg": {
                "lang_tags": ["en-US", "fr-FR"],
                "no_suffix": "en-US"
            },
            "title": "Test"
        }
        cfg = extract_config_from_yml(yml_data)
        assert cfg.lang_tags == ["en-US", "fr-FR"]
        assert cfg.no_suffix == "en-US"

    def test_extract_config_with_list_lang_tags(self):
        """Test extracting config with list format for lang_tags."""
        yml_data = {
            "mmg": {
                "lang_tags": ["en", "es", "fr"],
            }
        }
        cfg = extract_config_from_yml(yml_data)
        assert cfg.lang_tags == ["en", "es", "fr"]

    def test_extract_config_with_string_lang_tags(self):
        """Test extracting config with string format for lang_tags."""
        yml_data = {
            "mmg": {
                "lang_tags": "en, es, fr",
            }
        }
        cfg = extract_config_from_yml(yml_data)
        assert cfg.lang_tags == ["en", "es", "fr"]

    def test_extract_config_empty_yml(self):
        """Test extracting config from YAML with no mmg section."""
        yml_data = {"title": "Test"}
        cfg = extract_config_from_yml(yml_data)
        assert cfg.lang_tags == []
        assert cfg.no_suffix is None

    def test_extract_config_with_no_suffix(self):
        """Test extracting config with no_suffix option."""
        yml_data = {
            "mmg": {
                "lang_tags": ["en", "es"],
                "no_suffix": "en"
            }
        }
        cfg = extract_config_from_yml(yml_data)
        assert cfg.no_suffix == "en"


class TestYmlConversion:
    """Test YAML content conversion."""

    def test_convert_simple_multilingual_yml(self):
        """Test converting simple multilingual YAML."""
        yml_data = {
            "mmg": {
                "lang_tags": ["en", "es"],
                "no_suffix": "en"
            },
            "message": "<!-- [en] -->\nHello\n<!-- [es] -->\nHola"
        }
        result = convert_base_yml(yml_data)
        
        assert "en" in result
        assert "es" in result
        assert "Hello" in result["en"]["message"]
        assert "Hola" in result["es"]["message"]

    def test_convert_yml_with_nested_content(self):
        """Test converting YAML with nested multilingual content."""
        yml_data = {
            "mmg": {
                "lang_tags": ["en-US", "es-MX"],
                "no_suffix": "en-US"
            },
            "app": {
                "name": "<!-- [en-US] -->\nMyApp\n<!-- [es-MX] -->\nMiApp",
                "description": "<!-- [en-US] -->\nA great app\n<!-- [es-MX] -->\nUna gran aplicación"
            }
        }
        result = convert_base_yml(yml_data)
        
        assert result["en-US"]["app"]["name"] == "MyApp"
        assert result["es-MX"]["app"]["name"] == "MiApp"
        assert "great app" in result["en-US"]["app"]["description"]
        assert "gran aplicación" in result["es-MX"]["app"]["description"]

    def test_convert_yml_with_list(self):
        """Test converting YAML with lists containing multilingual content."""
        yml_data = {
            "mmg": {
                "lang_tags": ["en", "fr"],
                "no_suffix": "en"
            },
            "items": [
                "<!-- [en] -->\nFirst\n<!-- [fr] -->\nPremier",
                "<!-- [en] -->\nSecond\n<!-- [fr] -->\nDeuxième"
            ]
        }
        result = convert_base_yml(yml_data)
        
        assert result["en"]["items"][0] == "First"
        assert result["fr"]["items"][0] == "Premier"
        assert result["en"]["items"][1] == "Second"
        assert result["fr"]["items"][1] == "Deuxième"

    def test_convert_yml_with_hash_comments(self):
        """Test converting YAML with hash-style comments."""
        yml_data = {
            "mmg": {
                "lang_tags": ["en", "es"],
                "no_suffix": "en"
            },
            "title": "# [en]\nEnglish Title\n# [es]\nTítulo en Español"
        }
        result = convert_base_yml(yml_data)
        
        assert "English Title" in result["en"]["title"]
        assert "Título en Español" in result["es"]["title"]

    def test_convert_yml_preserves_structure(self):
        """Test that YAML structure is preserved after conversion."""
        yml_data = {
            "mmg": {
                "lang_tags": ["en", "es"],
                "no_suffix": "en"
            },
            "config": {
                "version": "1.0.0",
                "author": "Test"
            },
            "content": "<!-- [en] -->\nTest\n<!-- [es] -->\nPrueba"
        }
        result = convert_base_yml(yml_data)
        
        # Check that non-content fields are preserved
        assert result["en"]["config"]["version"] == "1.0.0"
        assert result["es"]["config"]["author"] == "Test"
        assert result["en"]["mmg"]["lang_tags"] == ["en", "es"]

    def test_convert_yml_with_scalar_values(self):
        """Test converting YAML with non-string scalar values."""
        yml_data = {
            "mmg": {
                "lang_tags": ["en", "es"],
                "no_suffix": "en"
            },
            "version": 1.5,
            "count": 42,
            "enabled": True,
            "message": "<!-- [en] -->\nEnabled\n<!-- [es] -->\nHabilitado"
        }
        result = convert_base_yml(yml_data)
        
        # Scalar values should be preserved
        assert result["en"]["version"] == 1.5
        assert result["es"]["count"] == 42
        assert result["en"]["enabled"] is True
        assert "Enabled" in result["en"]["message"]
        assert "Habilitado" in result["es"]["message"]

    def test_convert_yml_skips_mmg_section(self):
        """Test that mmg config section is not modified during conversion."""
        yml_data = {
            "mmg": {
                "lang_tags": ["en", "es"],
                "no_suffix": "en"
            },
            "content": "<!-- [en] -->\nTest\n<!-- [es] -->\nPrueba"
        }
        result = convert_base_yml(yml_data)
        
        # mmg section should be identical in all languages
        assert result["en"]["mmg"] == yml_data["mmg"]
        assert result["es"]["mmg"] == yml_data["mmg"]


class TestYmlHealthCheck:
    """Test YAML health checking."""

    def test_health_check_valid_yml(self):
        """Test health check on valid YAML."""
        yml_data = {
            "mmg": {
                "lang_tags": ["en", "es"],
            },
            "message": "<!-- [en] -->\nTest\n<!-- [es] -->\nPrueba"
        }
        cfg = extract_config_from_yml(yml_data)
        hc = HealthChecker()
        status = hc.health_check(yml_data, cfg, extension="yml")
        
        assert status.name == "HEALTHY"

    def test_health_check_detects_tags(self):
        """Test that health check detects language tags."""
        yml_data = {
            "mmg": {
                "lang_tags": ["en", "es", "fr"],
            },
            "content": "<!-- [en] -->\nEnglish\n<!-- [es] -->\nEspañol\n<!-- [fr] -->\nFrançais"
        }
        cfg = extract_config_from_yml(yml_data)
        hc = HealthChecker()
        hc.health_check(yml_data, cfg, extension="yml")
        
        # All three languages should be detected
        assert hc.tag_count["en"] > 0
        assert hc.tag_count["es"] > 0
        assert hc.tag_count["fr"] > 0

    def test_health_check_detects_hash_comments(self):
        """Test that health check detects hash-style comments."""
        yml_data = {
            "mmg": {
                "lang_tags": ["en", "es"],
            },
            "message": "# [en]\nEnglish\n# [es]\nEspañol"
        }
        cfg = extract_config_from_yml(yml_data)
        hc = HealthChecker()
        status = hc.health_check(yml_data, cfg, extension="yml")
        
        assert status.name == "HEALTHY"
        assert hc.tag_count["en"] > 0
        assert hc.tag_count["es"] > 0

    def test_health_check_no_tags_produces_zero_counts(self):
        """Test that YAML with no tags produces zero tag counts."""
        yml_data = {
            "mmg": {
                "lang_tags": ["en", "es"],
            },
            "message": "This has no tags"
        }
        cfg = extract_config_from_yml(yml_data)
        hc = HealthChecker()
        status = hc.health_check(yml_data, cfg, extension="yml")
        
        # All tag counts should be zero
        assert hc.tag_count["en"] == 0
        assert hc.tag_count["es"] == 0

    def test_health_check_with_no_suffix(self):
        """Test health check respects no_suffix option."""
        yml_data = {
            "mmg": {
                "lang_tags": ["en", "es"],
                "no_suffix": "en"
            },
            "content": "<!-- [en] -->\nEnglish\n<!-- [es] -->\nEspañol"
        }
        cfg = extract_config_from_yml(yml_data)
        hc = HealthChecker()
        status = hc.health_check(yml_data, cfg, extension="yml")
        
        assert status.name == "HEALTHY"
        assert cfg.no_suffix == "en"


class TestYmlWithRealExample:
    """Test YAML conversion with realistic examples."""

    def test_config_example_english_spanish(self):
        """Test with a realistic configuration example."""
        yml_data = {
            "mmg": {
                "lang_tags": ["en-US", "es-MX"],
                "no_suffix": "en-US"
            },
            "application": {
                "name": "<!-- [en-US] -->\nMyApp\n<!-- [es-MX] -->\nMiApp",
                "version": "1.0.0",
                "features": [
                    {
                        "name": "Feature One",
                        "description": "<!-- [en-US] -->\nFirst feature\n<!-- [es-MX] -->\nPrimera característica"
                    },
                    {
                        "name": "Feature Two",
                        "description": "<!-- [en-US] -->\nSecond feature\n<!-- [es-MX] -->\nSegunda característica"
                    }
                ]
            },
            "documentation": "<!-- [en-US] -->\nWelcome!\n<!-- [es-MX] -->\n¡Bienvenido!"
        }
        
        result = convert_base_yml(yml_data)
        
        # Check English version
        assert result["en-US"]["application"]["name"] == "MyApp"
        assert result["en-US"]["application"]["version"] == "1.0.0"
        assert len(result["en-US"]["application"]["features"]) == 2
        assert "First feature" in result["en-US"]["application"]["features"][0]["description"]
        
        # Check Spanish version
        assert result["es-MX"]["application"]["name"] == "MiApp"
        assert result["es-MX"]["application"]["version"] == "1.0.0"
        assert len(result["es-MX"]["application"]["features"]) == 2
        assert "Primera característica" in result["es-MX"]["application"]["features"][0]["description"]
        assert "Segunda característica" in result["es-MX"]["application"]["features"][1]["description"]

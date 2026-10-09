from pathlib import Path

import pytest

from banana_system.config import ConfigurationError, load_config


def test_development_example_is_valid() -> None:
    config = load_config(Path("config/development.example.toml"))
    assert config.mode.value == "development"
    assert config.input_provenance.value == "synthetic"


def test_hardware_example_is_rejected_until_real_adapters_exist() -> None:
    with pytest.raises(ConfigurationError, match="hardware mode"):
        load_config(Path("config/hardware.example.toml"))

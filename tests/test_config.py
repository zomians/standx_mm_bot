"""Tests for configuration management."""

import pytest
from pydantic import ValidationError

from standx_mm_bot.config import Settings


def test_settings_with_valid_values(monkeypatch):
    """Test Settings with valid environment variables."""
    # Set environment variables
    monkeypatch.setenv("STANDX_PRIVATE_KEY", "test_private_key")
    monkeypatch.setenv("STANDX_WALLET_ADDRESS", "0x1234567890abcdef")
    monkeypatch.setenv("STANDX_CHAIN", "bsc")
    monkeypatch.setenv("SYMBOL", "ETH_USDC")
    monkeypatch.setenv("ORDER_SIZE", "0.5")
    monkeypatch.setenv("TARGET_DISTANCE_BPS", "8.0")

    settings = Settings()

    assert settings.standx_private_key == "test_private_key"
    assert settings.standx_wallet_address == "0x1234567890abcdef"
    assert settings.standx_chain == "bsc"
    assert settings.symbol == "ETH_USDC"
    assert settings.order_size == 0.5
    assert settings.target_distance_bps == 8.0


def test_settings_with_defaults(monkeypatch):
    """Test Settings with default values."""
    # Set only required fields
    monkeypatch.setenv("STANDX_PRIVATE_KEY", "test_private_key")
    monkeypatch.setenv("STANDX_WALLET_ADDRESS", "0x1234567890abcdef")

    settings = Settings()

    # Check defaults
    assert settings.standx_chain == "bsc"
    assert settings.symbol == "ETH_USDC"
    assert settings.order_size == 0.1
    assert settings.target_distance_bps == 8.0
    assert settings.escape_threshold_bps == 3.0
    assert settings.outer_escape_distance_bps == 15.0
    assert settings.reposition_threshold_bps == 2.0
    assert settings.price_move_threshold_bps == 5.0
    assert settings.ws_reconnect_interval == 5000
    assert settings.jwt_expires_seconds == 604800


def test_target_distance_bps_validation_too_small(monkeypatch):
    """Test target_distance_bps validation with value <= 0."""
    monkeypatch.setenv("STANDX_PRIVATE_KEY", "test_private_key")
    monkeypatch.setenv("STANDX_WALLET_ADDRESS", "0x1234567890abcdef")
    monkeypatch.setenv("TARGET_DISTANCE_BPS", "0")

    with pytest.raises(ValidationError) as exc_info:
        Settings()

    assert "target_distance_bps must be between 0 and 10" in str(exc_info.value)


def test_target_distance_bps_validation_too_large(monkeypatch):
    """Test target_distance_bps validation with value >= 10."""
    monkeypatch.setenv("STANDX_PRIVATE_KEY", "test_private_key")
    monkeypatch.setenv("STANDX_WALLET_ADDRESS", "0x1234567890abcdef")
    monkeypatch.setenv("TARGET_DISTANCE_BPS", "10")

    with pytest.raises(ValidationError) as exc_info:
        Settings()

    assert "target_distance_bps must be between 0 and 10" in str(exc_info.value)


def test_target_distance_bps_validation_negative(monkeypatch):
    """Test target_distance_bps validation with negative value."""
    monkeypatch.setenv("STANDX_PRIVATE_KEY", "test_private_key")
    monkeypatch.setenv("STANDX_WALLET_ADDRESS", "0x1234567890abcdef")
    monkeypatch.setenv("TARGET_DISTANCE_BPS", "-1")

    with pytest.raises(ValidationError) as exc_info:
        Settings()

    assert "target_distance_bps must be between 0 and 10" in str(exc_info.value)


def test_escape_threshold_bps_validation_zero(monkeypatch):
    """Test escape_threshold_bps validation with value <= 0."""
    monkeypatch.setenv("STANDX_PRIVATE_KEY", "test_private_key")
    monkeypatch.setenv("STANDX_WALLET_ADDRESS", "0x1234567890abcdef")
    monkeypatch.setenv("ESCAPE_THRESHOLD_BPS", "0")

    with pytest.raises(ValidationError) as exc_info:
        Settings()

    assert "escape_threshold_bps must be positive" in str(exc_info.value)


def test_escape_threshold_bps_validation_negative(monkeypatch):
    """Test escape_threshold_bps validation with negative value."""
    monkeypatch.setenv("STANDX_PRIVATE_KEY", "test_private_key")
    monkeypatch.setenv("STANDX_WALLET_ADDRESS", "0x1234567890abcdef")
    monkeypatch.setenv("ESCAPE_THRESHOLD_BPS", "-1")

    with pytest.raises(ValidationError) as exc_info:
        Settings()

    assert "escape_threshold_bps must be positive" in str(exc_info.value)


def test_missing_required_fields(monkeypatch):
    """Test Settings with missing required fields."""
    # Don't set required fields
    monkeypatch.delenv("STANDX_PRIVATE_KEY", raising=False)
    monkeypatch.delenv("STANDX_WALLET_ADDRESS", raising=False)

    with pytest.raises(ValidationError):
        Settings()

"""config.pyのテスト."""

import os
from pathlib import Path

import pytest
from pydantic import ValidationError

from standx_mm_bot.config import Settings


def test_settings_with_env_file(tmp_path: Path) -> None:
    """環境変数ファイルから設定を読み込めることを確認."""
    env_file = tmp_path / ".env"
    env_file.write_text(
        "STANDX_PRIVATE_KEY=0x1234567890abcdef\n"
        "STANDX_WALLET_ADDRESS=0xabcdef1234567890\n"
        "STANDX_CHAIN=bsc\n"
        "SYMBOL=ETH_USDC\n"
        "ORDER_SIZE=0.1\n"
        "TARGET_DISTANCE_BPS=8.0\n"
    )

    # env_fileを指定して設定を読み込む
    settings = Settings(_env_file=str(env_file))

    assert settings.standx_private_key == "0x1234567890abcdef"
    assert settings.standx_wallet_address == "0xabcdef1234567890"
    assert settings.standx_chain == "bsc"
    assert settings.symbol == "ETH_USDC"
    assert settings.order_size == 0.1
    assert settings.target_distance_bps == 8.0


def test_settings_default_values() -> None:
    """デフォルト値が正しく設定されることを確認."""
    # 必須フィールドのみ環境変数で設定
    os.environ["STANDX_PRIVATE_KEY"] = "0xtest"
    os.environ["STANDX_WALLET_ADDRESS"] = "0xtest"

    settings = Settings()

    # デフォルト値の確認
    assert settings.standx_chain == "bsc"
    assert settings.symbol == "ETH-USD"
    assert settings.order_size == 0.1
    assert settings.target_distance_bps == 8.0
    assert settings.escape_threshold_bps == 3.0
    assert settings.outer_escape_distance_bps == 15.0
    assert settings.reposition_threshold_bps == 2.0
    assert settings.price_move_threshold_bps == 5.0
    assert settings.ws_reconnect_interval == 5000
    assert settings.jwt_expires_seconds == 604800

    # クリーンアップ
    del os.environ["STANDX_PRIVATE_KEY"]
    del os.environ["STANDX_WALLET_ADDRESS"]


def test_settings_validation_target_distance_too_small() -> None:
    """target_distance_bpsが小さすぎる場合にエラーが発生することを確認."""
    os.environ["STANDX_PRIVATE_KEY"] = "0xtest"
    os.environ["STANDX_WALLET_ADDRESS"] = "0xtest"
    os.environ["TARGET_DISTANCE_BPS"] = "-1.0"

    with pytest.raises(ValidationError) as exc_info:
        Settings()

    assert "target_distance_bps must be between 0 and 10" in str(exc_info.value)

    # クリーンアップ
    del os.environ["STANDX_PRIVATE_KEY"]
    del os.environ["STANDX_WALLET_ADDRESS"]
    del os.environ["TARGET_DISTANCE_BPS"]


def test_settings_validation_target_distance_too_large() -> None:
    """target_distance_bpsが大きすぎる場合にエラーが発生することを確認."""
    os.environ["STANDX_PRIVATE_KEY"] = "0xtest"
    os.environ["STANDX_WALLET_ADDRESS"] = "0xtest"
    os.environ["TARGET_DISTANCE_BPS"] = "15.0"

    with pytest.raises(ValidationError) as exc_info:
        Settings()

    assert "target_distance_bps must be between 0 and 10" in str(exc_info.value)

    # クリーンアップ
    del os.environ["STANDX_PRIVATE_KEY"]
    del os.environ["STANDX_WALLET_ADDRESS"]
    del os.environ["TARGET_DISTANCE_BPS"]


def test_settings_missing_required_fields() -> None:
    """必須フィールドが欠けている場合にエラーが発生することを確認."""
    # 環境変数をクリア
    for key in ["STANDX_PRIVATE_KEY", "STANDX_WALLET_ADDRESS"]:
        if key in os.environ:
            del os.environ[key]

    # _env_file=Noneで.envファイルを無視
    with pytest.raises(ValidationError):
        Settings(_env_file=None)

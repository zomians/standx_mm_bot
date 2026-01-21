"""設定管理モジュール."""

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """アプリケーション設定."""

    # 認証
    standx_private_key: str = Field(..., description="ウォレット秘密鍵")
    standx_wallet_address: str = Field(..., description="ウォレットアドレス")
    standx_chain: str = Field("bsc", description="チェーン (bsc or solana)")

    # 取引設定
    symbol: str = Field("ETH_USDC", description="取引ペア")
    order_size: float = Field(0.1, description="片側注文サイズ")

    # 距離設定 (bps)
    target_distance_bps: float = Field(8.0, description="目標距離 (bps)")
    escape_threshold_bps: float = Field(3.0, description="約定回避距離 (bps)")
    outer_escape_distance_bps: float = Field(15.0, description="逃げる先の距離 (bps)")
    reposition_threshold_bps: float = Field(2.0, description="10bps境界への接近しきい値 (bps)")
    price_move_threshold_bps: float = Field(5.0, description="価格変動による再配置しきい値 (bps)")

    # 接続設定
    ws_reconnect_interval: int = Field(5000, description="WebSocket再接続間隔 (ms)")
    jwt_expires_seconds: int = Field(604800, description="JWT有効期限 (秒, デフォルト7日)")

    @field_validator("target_distance_bps")
    @classmethod
    def validate_target_distance(cls, v: float) -> float:
        """target_distance_bpsは0-10の範囲である必要がある."""
        if not 0 < v < 10:
            raise ValueError("target_distance_bps must be between 0 and 10")
        return v

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
    }

"""Configuration management for StandX MM Bot."""

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Bot settings loaded from environment variables."""

    # Authentication
    standx_private_key: str = Field(..., description="Wallet private key")
    standx_wallet_address: str = Field(..., description="Wallet address")
    standx_chain: str = Field("bsc", description="Chain (bsc/solana)")

    # Trading settings
    symbol: str = Field("ETH_USDC", description="Trading pair")
    order_size: float = Field(0.1, description="Order size per side")

    # Distance settings (in bps)
    target_distance_bps: float = Field(8.0, description="Target distance from mark price")
    escape_threshold_bps: float = Field(3.0, description="Escape threshold distance")
    outer_escape_distance_bps: float = Field(15.0, description="Outer escape distance")
    reposition_threshold_bps: float = Field(2.0, description="Reposition threshold")
    price_move_threshold_bps: float = Field(5.0, description="Price move threshold")

    # Connection settings
    ws_reconnect_interval: int = Field(5000, description="WebSocket reconnect interval (ms)")
    jwt_expires_seconds: int = Field(604800, description="JWT expiration (seconds, 7 days)")

    @field_validator("target_distance_bps")
    @classmethod
    def validate_target_distance(cls, v: float) -> float:
        """Validate target_distance_bps is between 0 and 10."""
        if not 0 < v < 10:
            raise ValueError("target_distance_bps must be between 0 and 10")
        return v

    @field_validator("escape_threshold_bps")
    @classmethod
    def validate_escape_threshold(cls, v: float) -> float:
        """Validate escape_threshold_bps is positive."""
        if v <= 0:
            raise ValueError("escape_threshold_bps must be positive")
        return v

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
    }

"""Tests for data models."""

from datetime import datetime

import pytest

from standx_mm_bot.models import (
    Action,
    Order,
    OrderStatus,
    OrderType,
    Position,
    PriceUpdate,
    Side,
    Trade,
)


def test_side_enum():
    """Test Side enum values."""
    assert Side.BUY == "BUY"
    assert Side.SELL == "SELL"
    assert Side.BUY.value == "BUY"
    assert Side.SELL.value == "SELL"


def test_order_type_enum():
    """Test OrderType enum values."""
    assert OrderType.LIMIT == "LIMIT"
    assert OrderType.MARKET == "MARKET"


def test_order_status_enum():
    """Test OrderStatus enum values."""
    assert OrderStatus.OPEN == "OPEN"
    assert OrderStatus.FILLED == "FILLED"
    assert OrderStatus.PARTIALLY_FILLED == "PARTIALLY_FILLED"
    assert OrderStatus.CANCELED == "CANCELED"


def test_action_enum():
    """Test Action enum values."""
    assert Action.HOLD == "HOLD"
    assert Action.ESCAPE == "ESCAPE"
    assert Action.REPOSITION == "REPOSITION"


def test_order_creation():
    """Test Order dataclass creation."""
    timestamp = datetime(2025, 1, 21, 12, 0, 0)
    order = Order(
        id="order_123",
        symbol="ETH_USDC",
        side=Side.BUY,
        price=2500.0,
        size=0.1,
        order_type=OrderType.LIMIT,
        status=OrderStatus.OPEN,
        filled_size=0.0,
        timestamp=timestamp,
    )

    assert order.id == "order_123"
    assert order.symbol == "ETH_USDC"
    assert order.side == Side.BUY
    assert order.price == 2500.0
    assert order.size == 0.1
    assert order.order_type == OrderType.LIMIT
    assert order.status == OrderStatus.OPEN
    assert order.filled_size == 0.0
    assert order.timestamp == timestamp


def test_order_with_defaults():
    """Test Order with default values."""
    order = Order(
        id="order_123",
        symbol="ETH_USDC",
        side=Side.BUY,
        price=2500.0,
        size=0.1,
        order_type=OrderType.LIMIT,
        status=OrderStatus.OPEN,
    )

    assert order.filled_size == 0.0
    assert order.timestamp is None


def test_position_creation():
    """Test Position dataclass creation."""
    position = Position(
        symbol="ETH_USDC",
        side=Side.BUY,
        size=0.5,
        entry_price=2500.0,
        unrealized_pnl=10.5,
    )

    assert position.symbol == "ETH_USDC"
    assert position.side == Side.BUY
    assert position.size == 0.5
    assert position.entry_price == 2500.0
    assert position.unrealized_pnl == 10.5


def test_position_with_defaults():
    """Test Position with default values."""
    position = Position(
        symbol="ETH_USDC",
        side=Side.BUY,
        size=0.5,
        entry_price=2500.0,
    )

    assert position.unrealized_pnl == 0.0


def test_price_update_creation():
    """Test PriceUpdate dataclass creation."""
    timestamp = datetime(2025, 1, 21, 12, 0, 0)
    price_update = PriceUpdate(
        symbol="ETH_USDC",
        mark_price=2500.5,
        index_price=2500.3,
        timestamp=timestamp,
    )

    assert price_update.symbol == "ETH_USDC"
    assert price_update.mark_price == 2500.5
    assert price_update.index_price == 2500.3
    assert price_update.timestamp == timestamp


def test_trade_creation():
    """Test Trade dataclass creation."""
    timestamp = datetime(2025, 1, 21, 12, 0, 0)
    trade = Trade(
        id="trade_456",
        order_id="order_123",
        symbol="ETH_USDC",
        side=Side.BUY,
        price=2500.0,
        size=0.1,
        fee=0.025,
        timestamp=timestamp,
    )

    assert trade.id == "trade_456"
    assert trade.order_id == "order_123"
    assert trade.symbol == "ETH_USDC"
    assert trade.side == Side.BUY
    assert trade.price == 2500.0
    assert trade.size == 0.1
    assert trade.fee == 0.025
    assert trade.timestamp == timestamp

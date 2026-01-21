"""models.pyのテスト."""

from datetime import datetime

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


def test_side_enum() -> None:
    """Side Enumの値が正しいことを確認."""
    assert Side.BUY == "BUY"
    assert Side.SELL == "SELL"


def test_order_type_enum() -> None:
    """OrderType Enumの値が正しいことを確認."""
    assert OrderType.LIMIT == "LIMIT"
    assert OrderType.MARKET == "MARKET"


def test_order_status_enum() -> None:
    """OrderStatus Enumの値が正しいことを確認."""
    assert OrderStatus.OPEN == "OPEN"
    assert OrderStatus.FILLED == "FILLED"
    assert OrderStatus.PARTIALLY_FILLED == "PARTIALLY_FILLED"
    assert OrderStatus.CANCELED == "CANCELED"


def test_action_enum() -> None:
    """Action Enumの値が正しいことを確認."""
    assert Action.HOLD == "HOLD"
    assert Action.ESCAPE == "ESCAPE"
    assert Action.REPOSITION == "REPOSITION"


def test_order_creation() -> None:
    """Orderインスタンスが正しく作成されることを確認."""
    now = datetime.now()
    order = Order(
        id="order_123",
        symbol="ETH_USDC",
        side=Side.BUY,
        price=2000.0,
        size=0.1,
        order_type=OrderType.LIMIT,
        status=OrderStatus.OPEN,
        filled_size=0.0,
        timestamp=now,
    )

    assert order.id == "order_123"
    assert order.symbol == "ETH_USDC"
    assert order.side == Side.BUY
    assert order.price == 2000.0
    assert order.size == 0.1
    assert order.order_type == OrderType.LIMIT
    assert order.status == OrderStatus.OPEN
    assert order.filled_size == 0.0
    assert order.timestamp == now


def test_order_default_values() -> None:
    """Orderのデフォルト値が正しく設定されることを確認."""
    order = Order(
        id="order_123",
        symbol="ETH_USDC",
        side=Side.BUY,
        price=2000.0,
        size=0.1,
        order_type=OrderType.LIMIT,
        status=OrderStatus.OPEN,
    )

    assert order.filled_size == 0.0
    assert order.timestamp is None


def test_position_creation() -> None:
    """Positionインスタンスが正しく作成されることを確認."""
    position = Position(
        symbol="ETH_USDC",
        side=Side.BUY,
        size=0.5,
        entry_price=2000.0,
        unrealized_pnl=50.0,
    )

    assert position.symbol == "ETH_USDC"
    assert position.side == Side.BUY
    assert position.size == 0.5
    assert position.entry_price == 2000.0
    assert position.unrealized_pnl == 50.0


def test_position_default_unrealized_pnl() -> None:
    """Positionのunrealized_pnlのデフォルト値が0.0であることを確認."""
    position = Position(
        symbol="ETH_USDC",
        side=Side.BUY,
        size=0.5,
        entry_price=2000.0,
    )

    assert position.unrealized_pnl == 0.0


def test_price_update_creation() -> None:
    """PriceUpdateインスタンスが正しく作成されることを確認."""
    now = datetime.now()
    price_update = PriceUpdate(
        symbol="ETH_USDC",
        mark_price=2000.0,
        index_price=2001.0,
        timestamp=now,
    )

    assert price_update.symbol == "ETH_USDC"
    assert price_update.mark_price == 2000.0
    assert price_update.index_price == 2001.0
    assert price_update.timestamp == now


def test_trade_creation() -> None:
    """Tradeインスタンスが正しく作成されることを確認."""
    now = datetime.now()
    trade = Trade(
        id="trade_123",
        order_id="order_123",
        symbol="ETH_USDC",
        side=Side.BUY,
        price=2000.0,
        size=0.1,
        fee=0.02,
        timestamp=now,
    )

    assert trade.id == "trade_123"
    assert trade.order_id == "order_123"
    assert trade.symbol == "ETH_USDC"
    assert trade.side == Side.BUY
    assert trade.price == 2000.0
    assert trade.size == 0.1
    assert trade.fee == 0.02
    assert trade.timestamp == now

"""Data models for StandX MM Bot."""

from dataclasses import dataclass
from datetime import datetime
from enum import Enum


class Side(str, Enum):
    """Order side."""

    BUY = "BUY"
    SELL = "SELL"


class OrderType(str, Enum):
    """Order type."""

    LIMIT = "LIMIT"
    MARKET = "MARKET"


class OrderStatus(str, Enum):
    """Order status."""

    OPEN = "OPEN"
    FILLED = "FILLED"
    PARTIALLY_FILLED = "PARTIALLY_FILLED"
    CANCELED = "CANCELED"


class Action(str, Enum):
    """Action to take on an order."""

    HOLD = "HOLD"  # Do nothing
    ESCAPE = "ESCAPE"  # Move order away to avoid fill
    REPOSITION = "REPOSITION"  # Move order to target position


@dataclass
class Order:
    """Order representation."""

    id: str
    symbol: str
    side: Side
    price: float
    size: float
    order_type: OrderType
    status: OrderStatus
    filled_size: float = 0.0
    timestamp: datetime | None = None


@dataclass
class Position:
    """Position representation."""

    symbol: str
    side: Side
    size: float
    entry_price: float
    unrealized_pnl: float = 0.0


@dataclass
class PriceUpdate:
    """Price update from WebSocket."""

    symbol: str
    mark_price: float
    index_price: float
    timestamp: datetime


@dataclass
class Trade:
    """Trade (fill) representation."""

    id: str
    order_id: str
    symbol: str
    side: Side
    price: float
    size: float
    fee: float
    timestamp: datetime

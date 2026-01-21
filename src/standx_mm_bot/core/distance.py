"""距離計算モジュール.

このモジュールは注文と mark_price の距離計算、目標価格計算、
価格接近判定を提供します。
"""

from standx_mm_bot.models import Side


def calculate_distance_bps(order_price: float, mark_price: float) -> float:
    """注文と mark_price の距離を bps で計算.

    Args:
        order_price: 注文価格
        mark_price: 現在の mark_price

    Returns:
        float: 距離 (bps)

    Example:
        >>> calculate_distance_bps(2490.0, 2500.0)
        40.0  # (10 / 2500) * 10000 = 40bps
    """
    return abs(order_price - mark_price) / mark_price * 10000


def calculate_target_price(mark_price: float, side: Side, distance_bps: float) -> float:
    """目標価格を計算.

    Args:
        mark_price: 現在の mark_price
        side: 注文サイド (BUY or SELL)
        distance_bps: 目標距離 (bps)

    Returns:
        float: 目標価格

    Example:
        >>> calculate_target_price(2500.0, Side.BUY, 8.0)
        2498.0  # 2500 - (2500 * 0.0008)

        >>> calculate_target_price(2500.0, Side.SELL, 8.0)
        2502.0  # 2500 + (2500 * 0.0008)
    """
    offset = mark_price * (distance_bps / 10000)
    if side == Side.BUY:
        return mark_price - offset
    else:
        return mark_price + offset


def is_approaching(mark_price: float, order_price: float, side: Side) -> bool:
    """価格が注文に接近しているか判定.

    Args:
        mark_price: 現在の mark_price
        order_price: 注文価格
        side: 注文サイド (BUY or SELL)

    Returns:
        bool: 接近している場合 True

    Example:
        >>> # BUY注文: 価格が下がっている = 接近
        >>> is_approaching(2499.0, 2498.0, Side.BUY)
        True

        >>> # BUY注文: 価格が上がっている = 離れている
        >>> is_approaching(2501.0, 2498.0, Side.BUY)
        False

        >>> # SELL注文: 価格が上がっている = 接近
        >>> is_approaching(2503.0, 2502.0, Side.SELL)
        True

        >>> # SELL注文: 価格が下がっている = 離れている
        >>> is_approaching(2499.0, 2502.0, Side.SELL)
        False
    """
    if side == Side.BUY:
        # BUY注文: 価格が下がっている = 約定に近づいている
        return mark_price < order_price
    else:
        # SELL注文: 価格が上がっている = 約定に近づいている
        return mark_price > order_price

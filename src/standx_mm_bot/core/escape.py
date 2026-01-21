"""約定回避ロジックモジュール.

このモジュールは約定回避判定と逃避先価格の計算を提供します。
"""

from standx_mm_bot.core.distance import (
    calculate_distance_bps,
    calculate_target_price,
    is_approaching,
)
from standx_mm_bot.models import Side


def should_escape(
    mark_price: float,
    order_price: float,
    side: Side,
    escape_threshold_bps: float,
) -> bool:
    """約定回避が必要か判定.

    価格が注文に接近している場合のみチェックし、
    距離が escape_threshold_bps 未満なら約定回避が必要。

    Args:
        mark_price: 現在の mark_price
        order_price: 注文価格
        side: 注文サイド (BUY or SELL)
        escape_threshold_bps: 約定回避距離しきい値 (bps)

    Returns:
        bool: 約定回避が必要な場合 True

    Example:
        >>> # BUY注文: 価格が下がっており、3bps以内に接近
        >>> should_escape(2498.5, 2498.0, Side.BUY, 3.0)
        True

        >>> # BUY注文: 価格が上がっている（離れている）
        >>> should_escape(2502.0, 2498.0, Side.BUY, 3.0)
        False

        >>> # SELL注文: 価格が上がっており、3bps以内に接近
        >>> should_escape(2502.5, 2502.0, Side.SELL, 3.0)
        True
    """
    # 優先順位1: 価格が接近しているかチェック
    if not is_approaching(mark_price, order_price, side):
        return False

    # 優先順位2: 距離が escape_threshold_bps 未満かチェック
    distance = calculate_distance_bps(order_price, mark_price)
    return distance < escape_threshold_bps


def calculate_escape_price(
    mark_price: float,
    side: Side,
    outer_escape_distance_bps: float,
) -> float:
    """逃避先価格を計算.

    約定回避時に外側に逃げる先の価格を計算します。

    Args:
        mark_price: 現在の mark_price
        side: 注文サイド (BUY or SELL)
        outer_escape_distance_bps: 逃避先距離 (bps)

    Returns:
        float: 逃避先価格

    Example:
        >>> # BUY注文: mark_price から 15bps 下
        >>> calculate_escape_price(2500.0, Side.BUY, 15.0)
        2496.25  # 2500 - (2500 * 0.0015)

        >>> # SELL注文: mark_price から 15bps 上
        >>> calculate_escape_price(2500.0, Side.SELL, 15.0)
        2503.75  # 2500 + (2500 * 0.0015)
    """
    return calculate_target_price(mark_price, side, outer_escape_distance_bps)

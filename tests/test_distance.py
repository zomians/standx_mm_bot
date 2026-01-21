"""距離計算モジュールのテスト."""

import pytest

from standx_mm_bot.core.distance import (
    calculate_distance_bps,
    calculate_target_price,
    is_approaching,
)
from standx_mm_bot.models import Side


class TestCalculateDistanceBps:
    """calculate_distance_bps のテスト."""

    def test_basic_calculation(self) -> None:
        """基本的な距離計算."""
        # 10 / 2500 * 10000 = 40bps
        assert calculate_distance_bps(2490.0, 2500.0) == pytest.approx(40.0, rel=1e-2)
        assert calculate_distance_bps(2510.0, 2500.0) == pytest.approx(40.0, rel=1e-2)

    def test_zero_distance(self) -> None:
        """距離がゼロの場合."""
        assert calculate_distance_bps(2500.0, 2500.0) == pytest.approx(0.0, rel=1e-2)

    def test_small_distance(self) -> None:
        """小さい距離（1bps, 5bps, 10bps）."""
        mark_price = 2500.0

        # 1bps = 0.01%
        order_price_1bps = 2500.0 - (2500.0 * 0.0001)  # 2499.75
        assert calculate_distance_bps(order_price_1bps, mark_price) == pytest.approx(1.0, rel=1e-2)

        # 5bps = 0.05%
        order_price_5bps = 2500.0 - (2500.0 * 0.0005)  # 2498.75
        assert calculate_distance_bps(order_price_5bps, mark_price) == pytest.approx(5.0, rel=1e-2)

        # 10bps = 0.1%
        order_price_10bps = 2500.0 - (2500.0 * 0.001)  # 2497.5
        assert calculate_distance_bps(order_price_10bps, mark_price) == pytest.approx(
            10.0, rel=1e-2
        )

    def test_large_distance(self) -> None:
        """大きい距離（100bps, 1000bps）."""
        mark_price = 2500.0

        # 100bps = 1%
        order_price_100bps = 2500.0 - (2500.0 * 0.01)  # 2475.0
        assert calculate_distance_bps(order_price_100bps, mark_price) == pytest.approx(
            100.0, rel=1e-2
        )

        # 1000bps = 10%
        order_price_1000bps = 2500.0 - (2500.0 * 0.1)  # 2250.0
        assert calculate_distance_bps(order_price_1000bps, mark_price) == pytest.approx(
            1000.0, rel=1e-2
        )


class TestCalculateTargetPrice:
    """calculate_target_price のテスト."""

    def test_buy_side(self) -> None:
        """BUY サイドの目標価格計算."""
        mark_price = 2500.0

        # 8bps下
        target = calculate_target_price(mark_price, Side.BUY, 8.0)
        assert target == pytest.approx(2498.0, rel=1e-2)  # 2500 - (2500 * 0.0008)

        # 10bps下
        target = calculate_target_price(mark_price, Side.BUY, 10.0)
        assert target == pytest.approx(2497.5, rel=1e-2)

    def test_sell_side(self) -> None:
        """SELL サイドの目標価格計算."""
        mark_price = 2500.0

        # 8bps上
        target = calculate_target_price(mark_price, Side.SELL, 8.0)
        assert target == pytest.approx(2502.0, rel=1e-2)  # 2500 + (2500 * 0.0008)

        # 10bps上
        target = calculate_target_price(mark_price, Side.SELL, 10.0)
        assert target == pytest.approx(2502.5, rel=1e-2)

    def test_zero_distance(self) -> None:
        """距離ゼロの場合."""
        mark_price = 2500.0

        # BUY: mark_price と同じ
        target = calculate_target_price(mark_price, Side.BUY, 0.0)
        assert target == pytest.approx(mark_price, rel=1e-2)

        # SELL: mark_price と同じ
        target = calculate_target_price(mark_price, Side.SELL, 0.0)
        assert target == pytest.approx(mark_price, rel=1e-2)

    def test_large_distance(self) -> None:
        """大きい距離の場合（100bps, 1000bps）."""
        mark_price = 2500.0

        # BUY: 100bps下 = 1%
        target = calculate_target_price(mark_price, Side.BUY, 100.0)
        assert target == pytest.approx(2475.0, rel=1e-2)

        # SELL: 100bps上 = 1%
        target = calculate_target_price(mark_price, Side.SELL, 100.0)
        assert target == pytest.approx(2525.0, rel=1e-2)


class TestIsApproaching:
    """is_approaching のテスト."""

    def test_buy_approaching(self) -> None:
        """BUY注文: 価格が注文価格より下にある = 接近."""
        order_price = 2498.0

        # mark_price < order_price → 接近（約定の危険）
        assert is_approaching(2497.0, order_price, Side.BUY) is True
        assert is_approaching(2497.5, order_price, Side.BUY) is True
        assert is_approaching(2490.0, order_price, Side.BUY) is True

    def test_buy_not_approaching(self) -> None:
        """BUY注文: 価格が上がっている = 離れている."""
        order_price = 2498.0

        # 価格が上がっている → 離れている
        assert is_approaching(2501.0, order_price, Side.BUY) is False
        assert is_approaching(2500.0, order_price, Side.BUY) is False
        assert is_approaching(2499.0, order_price, Side.BUY) is False

    def test_sell_approaching(self) -> None:
        """SELL注文: 価格が上がっている = 接近."""
        order_price = 2502.0

        # 価格が上がっている → 接近
        assert is_approaching(2503.0, order_price, Side.SELL) is True
        assert is_approaching(2502.5, order_price, Side.SELL) is True
        assert is_approaching(2505.0, order_price, Side.SELL) is True

    def test_sell_not_approaching(self) -> None:
        """SELL注文: 価格が下がっている = 離れている."""
        order_price = 2502.0

        # 価格が下がっている → 離れている
        assert is_approaching(2499.0, order_price, Side.SELL) is False
        assert is_approaching(2500.0, order_price, Side.SELL) is False
        assert is_approaching(2501.0, order_price, Side.SELL) is False

    def test_at_order_price(self) -> None:
        """価格が注文価格と同じ場合."""
        order_price = 2500.0

        # BUY: mark_price == order_price → 接近していない（まだ余裕あり）
        assert is_approaching(2500.0, order_price, Side.BUY) is False

        # SELL: mark_price == order_price → 接近していない（まだ余裕あり）
        assert is_approaching(2500.0, order_price, Side.SELL) is False


class TestIntegration:
    """統合テスト（複数関数の連携）."""

    def test_calculate_and_verify_distance(self) -> None:
        """目標価格計算後、距離を検証."""
        mark_price = 2500.0
        target_distance = 8.0

        # BUY側の目標価格を計算
        buy_target = calculate_target_price(mark_price, Side.BUY, target_distance)

        # 計算した目標価格の距離を検証
        distance = calculate_distance_bps(buy_target, mark_price)
        assert distance == pytest.approx(target_distance, rel=1e-2)

        # SELL側の目標価格を計算
        sell_target = calculate_target_price(mark_price, Side.SELL, target_distance)

        # 計算した目標価格の距離を検証
        distance = calculate_distance_bps(sell_target, mark_price)
        assert distance == pytest.approx(target_distance, rel=1e-2)

    def test_approaching_scenario(self) -> None:
        """約定回避シナリオ: 価格が接近してきた場合."""
        mark_price = 2500.0
        escape_threshold = 3.0

        # BUY注文を8bpsの位置に配置
        buy_order_price = calculate_target_price(mark_price, Side.BUY, 8.0)
        assert buy_order_price == pytest.approx(2498.0, rel=1e-2)

        # 価格が大きく下がり、注文価格を下回る
        new_mark_price = 2497.5  # 注文価格より下（約2bps）

        # 接近判定（約定の危険）
        assert is_approaching(new_mark_price, buy_order_price, Side.BUY) is True

        # 距離計算
        distance = calculate_distance_bps(buy_order_price, new_mark_price)
        assert distance < escape_threshold  # 3bps以内に接近

    def test_reposition_scenario(self) -> None:
        """再配置シナリオ: 価格が離れた場合."""
        initial_mark_price = 2500.0
        target_distance = 8.0

        # BUY注文を8bpsの位置に配置
        buy_order_price = calculate_target_price(initial_mark_price, Side.BUY, target_distance)
        assert buy_order_price == pytest.approx(2498.0, rel=1e-2)

        # 価格が大きく上昇（注文が遠くなる）
        new_mark_price = 2520.0

        # 距離を計算
        distance = calculate_distance_bps(buy_order_price, new_mark_price)
        assert distance > 10.0  # 10bps以上離れた

        # 新しい目標価格を計算（再配置）
        new_target = calculate_target_price(new_mark_price, Side.BUY, target_distance)
        assert new_target == pytest.approx(2518.0, rel=1e-2)

"""約定回避ロジックのテスト."""

import pytest

from standx_mm_bot.core.escape import calculate_escape_price, should_escape
from standx_mm_bot.models import Side


class TestShouldEscape:
    """should_escape のテスト."""

    def test_buy_approaching_within_threshold(self) -> None:
        """BUY注文: 価格が注文価格より下にあり、しきい値以内."""
        mark_price = 2497.5  # order_priceより下
        order_price = 2498.0
        escape_threshold = 3.0

        # 距離: 約2bps < 3bps かつ mark_price < order_price → 約定回避必要
        assert should_escape(mark_price, order_price, Side.BUY, escape_threshold) is True

    def test_buy_approaching_outside_threshold(self) -> None:
        """BUY注文: 価格が接近しているが、しきい値外."""
        mark_price = 2490.0
        order_price = 2498.0
        escape_threshold = 3.0

        # 距離: 約32bps > 3bps → 約定回避不要（まだ余裕あり）
        assert should_escape(mark_price, order_price, Side.BUY, escape_threshold) is False

    def test_buy_not_approaching(self) -> None:
        """BUY注文: 価格が離れている."""
        mark_price = 2510.0
        order_price = 2498.0
        escape_threshold = 3.0

        # 価格が上がっている → 接近していない → 約定回避不要
        assert should_escape(mark_price, order_price, Side.BUY, escape_threshold) is False

    def test_sell_approaching_within_threshold(self) -> None:
        """SELL注文: 価格が接近しており、しきい値以内."""
        mark_price = 2502.5
        order_price = 2502.0
        escape_threshold = 3.0

        # 距離: 約0.2bps < 3bps → 約定回避必要
        assert should_escape(mark_price, order_price, Side.SELL, escape_threshold) is True

    def test_sell_approaching_outside_threshold(self) -> None:
        """SELL注文: 価格が接近しているが、しきい値外."""
        mark_price = 2510.0
        order_price = 2502.0
        escape_threshold = 3.0

        # 距離: 約32bps > 3bps → 約定回避不要（まだ余裕あり）
        assert should_escape(mark_price, order_price, Side.SELL, escape_threshold) is False

    def test_sell_not_approaching(self) -> None:
        """SELL注文: 価格が離れている."""
        mark_price = 2490.0
        order_price = 2502.0
        escape_threshold = 3.0

        # 価格が下がっている → 接近していない → 約定回避不要
        assert should_escape(mark_price, order_price, Side.SELL, escape_threshold) is False

    def test_at_order_price(self) -> None:
        """価格が注文価格と同じ場合."""
        order_price = 2500.0
        mark_price = 2500.0
        escape_threshold = 3.0

        # 距離: 0bps < 3bps だが、接近していない → 約定回避不要
        assert should_escape(mark_price, order_price, Side.BUY, escape_threshold) is False
        assert should_escape(mark_price, order_price, Side.SELL, escape_threshold) is False

    def test_different_thresholds(self) -> None:
        """異なるしきい値でのテスト."""
        mark_price = 2497.0  # order_priceより下
        order_price = 2498.0
        side = Side.BUY

        # 距離: 約4bps

        # しきい値 5bps: 約定回避必要（距離4bps < 5bps）
        assert should_escape(mark_price, order_price, side, 5.0) is True

        # しきい値 3bps: 約定回避不要（距離4bps > 3bps）
        assert should_escape(mark_price, order_price, side, 3.0) is False


class TestCalculateEscapePrice:
    """calculate_escape_price のテスト."""

    def test_buy_escape_price(self) -> None:
        """BUY注文の逃避先価格."""
        mark_price = 2500.0
        outer_distance = 15.0

        escape_price = calculate_escape_price(mark_price, Side.BUY, outer_distance)

        # 2500 - (2500 * 0.0015) = 2496.25
        assert escape_price == pytest.approx(2496.25, rel=1e-2)

    def test_sell_escape_price(self) -> None:
        """SELL注文の逃避先価格."""
        mark_price = 2500.0
        outer_distance = 15.0

        escape_price = calculate_escape_price(mark_price, Side.SELL, outer_distance)

        # 2500 + (2500 * 0.0015) = 2503.75
        assert escape_price == pytest.approx(2503.75, rel=1e-2)

    def test_different_distances(self) -> None:
        """異なる逃避距離でのテスト."""
        mark_price = 2500.0

        # 10bps
        escape_price = calculate_escape_price(mark_price, Side.BUY, 10.0)
        assert escape_price == pytest.approx(2497.5, rel=1e-2)

        # 20bps
        escape_price = calculate_escape_price(mark_price, Side.BUY, 20.0)
        assert escape_price == pytest.approx(2495.0, rel=1e-2)

        # 50bps
        escape_price = calculate_escape_price(mark_price, Side.BUY, 50.0)
        assert escape_price == pytest.approx(2487.5, rel=1e-2)


class TestEscapeScenarios:
    """約定回避シナリオの統合テスト."""

    def test_buy_escape_scenario(self) -> None:
        """BUY注文の約定回避シナリオ.

        1. 注文を8bpsに配置
        2. 価格が注文価格を下回り3bps以内に接近
        3. 約定回避判定 → True
        4. 15bpsの逃避先価格を計算
        """
        initial_mark_price = 2500.0
        target_distance = 8.0
        escape_threshold = 3.0
        outer_distance = 15.0

        # 1. 注文を8bpsに配置
        from standx_mm_bot.core.distance import calculate_target_price

        order_price = calculate_target_price(initial_mark_price, Side.BUY, target_distance)
        assert order_price == pytest.approx(2498.0, rel=1e-2)

        # 2. 価格が大きく下がり、注文価格を下回る
        new_mark_price = 2497.5  # order_priceより下

        # 3. 約定回避判定（mark_price < order_price かつ 距離 < threshold）
        assert should_escape(new_mark_price, order_price, Side.BUY, escape_threshold) is True

        # 4. 逃避先価格を計算（新しいmark_priceから15bps）
        escape_price = calculate_escape_price(new_mark_price, Side.BUY, outer_distance)
        expected = 2497.5 - (2497.5 * 0.0015)
        assert escape_price == pytest.approx(expected, rel=1e-2)

    def test_sell_escape_scenario(self) -> None:
        """SELL注文の約定回避シナリオ.

        1. 注文を8bpsに配置
        2. 価格が注文価格を上回り3bps以内に接近
        3. 約定回避判定 → True
        4. 15bpsの逃避先価格を計算
        """
        initial_mark_price = 2500.0
        target_distance = 8.0
        escape_threshold = 3.0
        outer_distance = 15.0

        # 1. 注文を8bpsに配置
        from standx_mm_bot.core.distance import calculate_target_price

        order_price = calculate_target_price(initial_mark_price, Side.SELL, target_distance)
        assert order_price == pytest.approx(2502.0, rel=1e-2)

        # 2. 価格が大きく上がり、注文価格を上回る
        new_mark_price = 2502.5  # order_priceより上

        # 3. 約定回避判定（mark_price > order_price かつ 距離 < threshold）
        assert should_escape(new_mark_price, order_price, Side.SELL, escape_threshold) is True

        # 4. 逃避先価格を計算（新しいmark_priceから15bps）
        escape_price = calculate_escape_price(new_mark_price, Side.SELL, outer_distance)
        expected = 2502.5 + (2502.5 * 0.0015)
        assert escape_price == pytest.approx(expected, rel=1e-2)

    def test_no_escape_needed(self) -> None:
        """約定回避が不要なケース.

        価格が離れている、または距離が十分ある場合。
        """
        mark_price = 2500.0
        order_price = 2498.0
        escape_threshold = 3.0

        # BUY注文: 価格が上がっている → 約定回避不要
        assert should_escape(mark_price, order_price, Side.BUY, escape_threshold) is False

        # SELL注文: 注文が遠い
        sell_order_price = 2502.0
        assert should_escape(mark_price, sell_order_price, Side.SELL, escape_threshold) is False

    def test_edge_case_exact_threshold(self) -> None:
        """エッジケース: 距離がしきい値ちょうどの場合."""
        escape_threshold = 3.0

        # BUY注文を配置
        order_price = 2500.0

        # mark_priceが注文価格より3bps下（ちょうどしきい値）
        from standx_mm_bot.core.distance import calculate_target_price

        mark_price = calculate_target_price(order_price, Side.BUY, 3.0)
        assert mark_price == pytest.approx(2497.5, rel=1e-2)

        # 距離がちょうど3bps → しきい値未満ではない → 約定回避不要
        result = should_escape(mark_price, order_price, Side.BUY, escape_threshold)
        assert result is False

        # 少し近い位置（約2bps）→ しきい値未満 → 約定回避必要
        # 2bps = 0.0002 * 2500 = 0.5
        closer_mark_price = 2500.0 - 0.5 - 0.5 * 0.0002  # 約1.9bps
        closer_mark_price = 2499.5
        result = should_escape(closer_mark_price, order_price, Side.BUY, escape_threshold)
        assert result is True

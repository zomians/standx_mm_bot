"""注文管理モジュール."""

import asyncio
import logging
from typing import Any, Literal

from standx_mm_bot.client import StandXHTTPClient
from standx_mm_bot.config import Settings
from standx_mm_bot.models import Order, OrderStatus, OrderType, Side

logger = logging.getLogger(__name__)


class OrderManager:
    """
    注文管理クラス.

    注文の発注・キャンセル・再配置を管理し、asyncio.Lockで競合を防止する。
    """

    def __init__(self, http_client: StandXHTTPClient, config: Settings):
        """
        OrderManagerを初期化.

        Args:
            http_client: StandX HTTPクライアント
            config: アプリケーション設定
        """
        self.client = http_client
        self.config = config
        self._lock = asyncio.Lock()

    async def place_order(
        self,
        side: Side,
        price: float,
        size: float,
        time_in_force: str = "alo",
    ) -> Order:
        """
        注文を発注.

        Args:
            side: 注文サイド (BUY/SELL)
            price: 注文価格
            size: 注文サイズ
            time_in_force: 注文有効期限 (デフォルト: alo = Add Liquidity Only)

        Returns:
            Order: 発注された注文情報

        Raises:
            APIError: API呼び出しに失敗
        """
        async with self._lock:
            logger.info(
                f"Placing {side.value} order: price={price:.2f}, size={size}, "
                f"time_in_force={time_in_force}"
            )

            response = await self.client.new_order(
                symbol=self.config.symbol,
                side=side.value.lower(),
                price=price,
                size=size,
                order_type="limit",
                time_in_force=time_in_force,
                reduce_only=False,
            )

            order = self._parse_order_response(response, side, price, size)
            logger.info(f"Order placed: order_id={order.id}, status={order.status}")

            return order

    async def cancel_order(self, order_id: str) -> None:
        """
        注文をキャンセル.

        Args:
            order_id: キャンセルする注文ID

        Raises:
            APIError: API呼び出しに失敗
        """
        async with self._lock:
            logger.info(f"Cancelling order: order_id={order_id}")

            await self.client.cancel_order(
                order_id=order_id,
                symbol=self.config.symbol,
            )

            logger.info(f"Order cancelled: order_id={order_id}")

    async def reposition_order(
        self,
        old_order_id: str,
        new_price: float,
        side: Side,
        size: float,
        strategy: Literal["place_first", "cancel_first"] = "place_first",
    ) -> Order:
        """
        注文を再配置.

        Args:
            old_order_id: 旧注文ID
            new_price: 新しい価格
            side: 注文サイド
            size: 注文サイズ
            strategy: 再配置戦略
                - "place_first": 新規注文発注 → 確認 → 旧注文キャンセル（空白時間最小）
                - "cancel_first": 旧注文キャンセル → 新規注文発注（資金効率優先）

        Returns:
            Order: 新規注文情報

        Raises:
            APIError: API呼び出しに失敗
        """
        async with self._lock:
            logger.info(
                f"Repositioning order: old_order_id={old_order_id}, "
                f"new_price={new_price:.2f}, strategy={strategy}"
            )

            if strategy == "place_first":
                # 発注先行: 空白時間ゼロ
                new_order = await self._place_order_unlocked(side, new_price, size)

                # 新規注文が成功した場合のみ、旧注文をキャンセル
                if new_order.status == OrderStatus.OPEN:
                    await self._cancel_order_unlocked(old_order_id)
                    logger.info(f"Reposition completed (place_first): new_order_id={new_order.id}")
                else:
                    logger.warning(
                        f"New order not OPEN (status={new_order.status}), old order not cancelled"
                    )

                return new_order

            else:  # cancel_first
                # キャンセル先行: 資金効率優先
                await self._cancel_order_unlocked(old_order_id)
                new_order = await self._place_order_unlocked(side, new_price, size)

                logger.info(f"Reposition completed (cancel_first): new_order_id={new_order.id}")

                return new_order

    async def _place_order_unlocked(
        self,
        side: Side,
        price: float,
        size: float,
    ) -> Order:
        """
        注文を発注（ロックなし、内部使用専用）.

        Args:
            side: 注文サイド
            price: 注文価格
            size: 注文サイズ

        Returns:
            Order: 発注された注文情報
        """
        response = await self.client.new_order(
            symbol=self.config.symbol,
            side=side.value.lower(),
            price=price,
            size=size,
            order_type="limit",
            time_in_force="alo",
            reduce_only=False,
        )

        return self._parse_order_response(response, side, price, size)

    async def _cancel_order_unlocked(self, order_id: str) -> None:
        """
        注文をキャンセル（ロックなし、内部使用専用）.

        Args:
            order_id: キャンセルする注文ID
        """
        await self.client.cancel_order(
            order_id=order_id,
            symbol=self.config.symbol,
        )

    def _parse_order_response(
        self,
        response: dict[str, Any],
        side: Side,
        price: float,
        size: float,
    ) -> Order:
        """
        API レスポンスを Order オブジェクトにパース.

        Args:
            response: API レスポンス
            side: 注文サイド
            price: 注文価格
            size: 注文サイズ

        Returns:
            Order: パースされた注文情報
        """
        # StandX APIのレスポンス形式:
        # {"code": 0, "message": "success", "request_id": "xxx"}
        # または
        # {"order_id": "xxx", "status": "OPEN", ...}

        # order_id を取得（レスポンス形式によって異なる可能性がある）
        order_id = response.get("order_id") or response.get("request_id", "unknown")

        # status を取得（デフォルトはOPEN）
        status_str = response.get("status", "OPEN")
        try:
            status = OrderStatus(status_str)
        except ValueError:
            status = OrderStatus.OPEN

        return Order(
            id=order_id,
            symbol=self.config.symbol,
            side=side,
            price=price,
            size=size,
            order_type=OrderType.LIMIT,
            status=status,
        )

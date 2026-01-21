"""WebSocket クライアント."""

import asyncio
import json
import logging
from collections.abc import Awaitable, Callable
from typing import Any

import websockets
from websockets.asyncio.client import ClientConnection

from standx_mm_bot.config import Settings

logger = logging.getLogger(__name__)


class StandXWebSocketClient:
    """StandX WebSocket クライアント."""

    def __init__(self, config: Settings):
        """
        WebSocketクライアントを初期化.

        Args:
            config: アプリケーション設定
        """
        self.config = config
        self.ws_url = "wss://perps.standx.com/ws-stream/v1"
        self.reconnect_interval = config.ws_reconnect_interval / 1000  # ms to seconds
        self.ws: ClientConnection | None = None
        self._running = False
        self._callbacks: dict[str, list[Callable[[dict[str, Any]], Awaitable[None]]]] = {
            "price": [],
            "order": [],
            "trade": [],
        }

    def on_price_update(self, callback: Callable[[dict[str, Any]], Awaitable[None]]) -> None:
        """
        価格更新コールバックを登録.

        Args:
            callback: 価格更新時に呼ばれる非同期関数
        """
        self._callbacks["price"].append(callback)

    def on_order_update(self, callback: Callable[[dict[str, Any]], Awaitable[None]]) -> None:
        """
        注文更新コールバックを登録.

        Args:
            callback: 注文更新時に呼ばれる非同期関数
        """
        self._callbacks["order"].append(callback)

    def on_trade(self, callback: Callable[[dict[str, Any]], Awaitable[None]]) -> None:
        """
        約定コールバックを登録.

        Args:
            callback: 約定時に呼ばれる非同期関数
        """
        self._callbacks["trade"].append(callback)

    async def _subscribe_channels(self, ws: ClientConnection) -> None:
        """
        チャンネルを購読.

        Args:
            ws: WebSocket接続
        """
        # price チャンネル購読
        price_sub = {
            "method": "subscribe",
            "params": [f"price@{self.config.symbol}"],
            "id": 1,
        }
        await ws.send(json.dumps(price_sub))
        logger.info(f"Subscribed to price channel: {self.config.symbol}")

        # order チャンネル購読 (認証必要)
        order_sub = {"method": "subscribe", "params": ["order"], "id": 2}
        await ws.send(json.dumps(order_sub))
        logger.info("Subscribed to order channel")

        # trade チャンネル購読 (認証必要)
        trade_sub = {"method": "subscribe", "params": ["trade"], "id": 3}
        await ws.send(json.dumps(trade_sub))
        logger.info("Subscribed to trade channel")

    async def _dispatch_message(self, message: dict[str, Any]) -> None:
        """
        受信メッセージを適切なコールバックにディスパッチ.

        Args:
            message: 受信したメッセージ
        """
        channel = message.get("channel", "")

        # price チャンネル
        if channel.startswith("price@"):
            for callback in self._callbacks["price"]:
                try:
                    await callback(message.get("data", {}))
                except Exception as e:
                    logger.error(f"Error in price callback: {e}")

        # order チャンネル
        elif channel == "order":
            for callback in self._callbacks["order"]:
                try:
                    await callback(message.get("data", {}))
                except Exception as e:
                    logger.error(f"Error in order callback: {e}")

        # trade チャンネル
        elif channel == "trade":
            for callback in self._callbacks["trade"]:
                try:
                    await callback(message.get("data", {}))
                except Exception as e:
                    logger.error(f"Error in trade callback: {e}")

    async def _receive_messages(self, ws: ClientConnection) -> None:
        """
        メッセージを受信してディスパッチ.

        Args:
            ws: WebSocket接続
        """
        async for message in ws:
            if not self._running:
                break

            try:
                data = json.loads(message)
                await self._dispatch_message(data)
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse WebSocket message: {e}")
            except Exception as e:
                logger.error(f"Error processing WebSocket message: {e}")

    async def connect(self) -> None:
        """
        WebSocketに接続し、メッセージを受信.

        自動再接続機能付き。
        """
        self._running = True
        logger.info(f"Connecting to WebSocket: {self.ws_url}")

        while self._running:
            try:
                async with websockets.connect(self.ws_url) as ws:
                    self.ws = ws
                    logger.info("WebSocket connected")

                    await self._subscribe_channels(ws)
                    await self._receive_messages(ws)

            except websockets.ConnectionClosed:
                logger.warning("WebSocket disconnected, reconnecting...")
                await asyncio.sleep(self.reconnect_interval)

            except Exception as e:
                logger.error(f"WebSocket error: {e}")
                await asyncio.sleep(self.reconnect_interval)

        logger.info("WebSocket client stopped")

    async def disconnect(self) -> None:
        """WebSocket接続を切断."""
        self._running = False
        if self.ws:
            await self.ws.close()
            logger.info("WebSocket disconnected")

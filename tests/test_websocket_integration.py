"""WebSocketクライアントの統合テスト（実際のサーバー接続）."""

import asyncio
import contextlib

import pytest

from standx_mm_bot.client import StandXWebSocketClient
from standx_mm_bot.config import Settings


@pytest.fixture
def config() -> Settings:
    """テスト用の設定を作成."""
    return Settings(
        standx_private_key="0x1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef",
        standx_wallet_address="test_wallet_address",
        symbol="ETH-USD",
        ws_reconnect_interval=1000,
    )


@pytest.mark.asyncio
@pytest.mark.integration
async def test_real_websocket_price_channel(config: Settings) -> None:
    """実際のWebSocketサーバーからpriceメッセージを受信できることを確認."""
    client = StandXWebSocketClient(config)

    received_messages = []

    async def price_callback(data: dict) -> None:
        received_messages.append(data)
        print(f"Received price data: {data}")

    client.on_price_update(price_callback)

    # WebSocket接続を開始（バックグラウンド）
    connect_task = asyncio.create_task(client.connect())

    try:
        # 10秒待ってメッセージを受信
        await asyncio.sleep(10)

        # メッセージが受信されたことを確認
        assert len(received_messages) > 0, "No price messages received"

        # メッセージ形式を確認
        first_message = received_messages[0]
        assert "mark_price" in first_message or "markPrice" in first_message
        print(f"✅ Received {len(received_messages)} price messages")

    finally:
        # 切断
        await client.disconnect()
        connect_task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await connect_task


@pytest.mark.asyncio
@pytest.mark.integration
async def test_real_websocket_reconnection(config: Settings) -> None:
    """WebSocketの自動再接続が動作することを確認."""
    # 再接続間隔を短く設定
    config.ws_reconnect_interval = 1000  # 1秒

    client = StandXWebSocketClient(config)

    received_messages = []

    async def price_callback(data: dict) -> None:
        received_messages.append(data)

    client.on_price_update(price_callback)

    # WebSocket接続を開始
    connect_task = asyncio.create_task(client.connect())

    try:
        # 5秒待ってメッセージを受信
        await asyncio.sleep(5)
        assert len(received_messages) > 0, "No messages received before disconnect"

        # 強制切断
        if client.ws:
            await client.ws.close()
            print("✅ WebSocket forcefully closed")

        # 再接続を待つ
        await asyncio.sleep(3)

        # 再接続後もメッセージを受信できることを確認
        initial_count = len(received_messages)
        await asyncio.sleep(5)

        assert len(received_messages) > initial_count, "No messages received after reconnection"
        print(f"✅ Reconnected and received {len(received_messages) - initial_count} new messages")

    finally:
        await client.disconnect()
        connect_task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await connect_task


@pytest.mark.asyncio
@pytest.mark.integration
async def test_real_websocket_multiple_callbacks(config: Settings) -> None:
    """複数のコールバックが正しく呼ばれることを確認."""
    client = StandXWebSocketClient(config)

    callback1_count = 0
    callback2_count = 0

    async def callback1(_data: dict) -> None:
        nonlocal callback1_count
        callback1_count += 1

    async def callback2(_data: dict) -> None:
        nonlocal callback2_count
        callback2_count += 1

    client.on_price_update(callback1)
    client.on_price_update(callback2)

    connect_task = asyncio.create_task(client.connect())

    try:
        await asyncio.sleep(5)

        assert callback1_count > 0, "Callback 1 was not called"
        assert callback2_count > 0, "Callback 2 was not called"
        assert callback1_count == callback2_count, "Callbacks received different number of messages"
        print(f"✅ Both callbacks received {callback1_count} messages")

    finally:
        await client.disconnect()
        connect_task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await connect_task

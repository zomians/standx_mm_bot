"""REST APIクライアントのテスト."""

from unittest.mock import patch

import pytest
from aioresponses import aioresponses

from standx_mm_bot.client import (
    APIError,
    AuthenticationError,
    StandXHTTPClient,
)
from standx_mm_bot.config import Settings


@pytest.fixture
def config() -> Settings:
    """テスト用設定を生成."""
    return Settings(
        standx_private_key="0x" + "a" * 64,
        standx_wallet_address="0x1234567890abcdef",
        standx_chain="bsc",
        symbol="ETH_USDC",
        order_size=0.1,
        dry_run=False,  # テストではドライラン無効
    )


@pytest.fixture
def dry_run_config() -> Settings:
    """ドライランモード用設定を生成."""
    return Settings(
        standx_private_key="0x" + "a" * 64,
        standx_wallet_address="0x1234567890abcdef",
        standx_chain="bsc",
        symbol="ETH_USDC",
        order_size=0.1,
        dry_run=True,  # ドライラン有効
    )


@pytest.mark.asyncio
async def test_context_manager(config: Settings) -> None:
    """コンテキストマネージャーが正しく動作することを確認."""
    # テスト用のJWTトークンを指定
    async with StandXHTTPClient(config, jwt_token="test_jwt_token") as client:
        assert client.session is not None

    # コンテキスト終了後はセッションがクローズされる
    assert client.session.closed


@pytest.mark.asyncio
async def test_get_symbol_price(config: Settings) -> None:
    """シンボル価格取得が正しく動作することを確認."""
    with aioresponses() as mocked:
        # モックレスポンスを設定
        mocked.get(
            "https://perps.standx.com/api/query_symbol_price?symbol=ETH_USDC",
            payload={
                "symbol": "ETH_USDC",
                "mark_price": 3500.0,
                "index_price": 3498.5,
            },
        )

        async with StandXHTTPClient(config, jwt_token="test_jwt_token") as client:
            response = await client.get_symbol_price("ETH_USDC")

        assert response["symbol"] == "ETH_USDC"
        assert response["mark_price"] == 3500.0


@pytest.mark.asyncio
async def test_new_order_dry_run(dry_run_config: Settings) -> None:
    """ドライランモードで注文発注がモックされることを確認."""
    async with StandXHTTPClient(dry_run_config, jwt_token="test_jwt_token") as client:
        response = await client.new_order(
            symbol="ETH_USDC",
            side="BUY",
            price=3500.0,
            size=0.1,
        )

    # ドライランモードではモックレスポンスが返される
    assert response["order_id"] == "dry_run_order_id"
    assert response["symbol"] == "ETH_USDC"
    assert response["side"] == "BUY"
    assert response["status"] == "OPEN"


@pytest.mark.asyncio
async def test_new_order(config: Settings) -> None:
    """注文発注が正しく動作することを確認."""
    with aioresponses() as mocked:
        # モックレスポンスを設定
        mocked.post(
            "https://perps.standx.com/api/new_order",
            payload={
                "order_id": "order_123",
                "symbol": "ETH_USDC",
                "side": "BUY",
                "price": 3500.0,
                "size": 0.1,
                "order_type": "LIMIT",
                "status": "OPEN",
            },
        )

        async with StandXHTTPClient(config, jwt_token="test_jwt_token") as client:
            response = await client.new_order(
                symbol="ETH_USDC",
                side="BUY",
                price=3500.0,
                size=0.1,
            )

        assert response["order_id"] == "order_123"
        assert response["status"] == "OPEN"


@pytest.mark.asyncio
async def test_cancel_order_dry_run(dry_run_config: Settings) -> None:
    """ドライランモードで注文キャンセルがモックされることを確認."""
    async with StandXHTTPClient(dry_run_config, jwt_token="test_jwt_token") as client:
        response = await client.cancel_order(
            order_id="order_123",
            symbol="ETH_USDC",
        )

    # ドライランモードではモックレスポンスが返される
    assert response["order_id"] == "order_123"
    assert response["status"] == "CANCELED"


@pytest.mark.asyncio
async def test_cancel_order(config: Settings) -> None:
    """注文キャンセルが正しく動作することを確認."""
    with aioresponses() as mocked:
        # モックレスポンスを設定
        mocked.post(
            "https://perps.standx.com/api/cancel_order",
            payload={
                "order_id": "order_123",
                "symbol": "ETH_USDC",
                "status": "CANCELED",
            },
        )

        async with StandXHTTPClient(config, jwt_token="test_jwt_token") as client:
            response = await client.cancel_order(
                order_id="order_123",
                symbol="ETH_USDC",
            )

        assert response["order_id"] == "order_123"
        assert response["status"] == "CANCELED"


@pytest.mark.asyncio
async def test_get_open_orders(config: Settings) -> None:
    """未決注文一覧取得が正しく動作することを確認."""
    with aioresponses() as mocked:
        # モックレスポンスを設定
        mocked.get(
            "https://perps.standx.com/api/query_open_orders?symbol=ETH_USDC",
            payload={
                "orders": [
                    {"order_id": "order_1", "side": "BUY", "price": 3500.0},
                    {"order_id": "order_2", "side": "SELL", "price": 3510.0},
                ],
            },
        )

        async with StandXHTTPClient(config, jwt_token="test_jwt_token") as client:
            response = await client.get_open_orders("ETH_USDC")

        assert len(response["orders"]) == 2
        assert response["orders"][0]["order_id"] == "order_1"


@pytest.mark.asyncio
async def test_get_position(config: Settings) -> None:
    """ポジション情報取得が正しく動作することを確認."""
    with aioresponses() as mocked:
        # モックレスポンスを設定
        mocked.get(
            "https://perps.standx.com/api/query_positions?symbol=ETH_USDC",
            payload={
                "symbol": "ETH_USDC",
                "side": "LONG",
                "size": 1.0,
                "entry_price": 3500.0,
            },
        )

        async with StandXHTTPClient(config, jwt_token="test_jwt_token") as client:
            response = await client.get_position("ETH_USDC")

        assert response["symbol"] == "ETH_USDC"
        assert response["size"] == 1.0


@pytest.mark.asyncio
async def test_get_balance(config: Settings) -> None:
    """残高情報取得が正しく動作することを確認."""
    with aioresponses() as mocked:
        # モックレスポンスを設定
        mocked.get(
            "https://perps.standx.com/api/query_balance",
            payload={
                "equity": 10000.0,
                "cross_available": 8000.0,
                "upnl": 500.0,
                "locked": 2000.0,
                "balance": 9500.0,
            },
        )

        async with StandXHTTPClient(config, jwt_token="test_jwt_token") as client:
            response = await client.get_balance()

        assert response["equity"] == 10000.0
        assert response["cross_available"] == 8000.0
        assert response["upnl"] == 500.0
        assert response["locked"] == 2000.0


@pytest.mark.asyncio
async def test_authentication_error(config: Settings) -> None:
    """認証エラー (401) が正しく処理されることを確認."""
    with aioresponses() as mocked:
        # 401エラーを返すモックレスポンス
        mocked.get(
            "https://perps.standx.com/api/query_symbol_price?symbol=ETH_USDC",
            status=401,
        )

        async with StandXHTTPClient(config, jwt_token="test_jwt_token") as client:
            with pytest.raises(AuthenticationError, match="JWT expired or invalid"):
                await client.get_symbol_price("ETH_USDC")


@pytest.mark.asyncio
async def test_rate_limit_retry(config: Settings) -> None:
    """レート制限 (429) 時にリトライされることを確認."""
    with aioresponses() as mocked:
        # 1回目: 429エラー
        mocked.get(
            "https://perps.standx.com/api/query_symbol_price?symbol=ETH_USDC",
            status=429,
        )
        # 2回目: 成功
        mocked.get(
            "https://perps.standx.com/api/query_symbol_price?symbol=ETH_USDC",
            payload={"symbol": "ETH_USDC", "mark_price": 3500.0},
        )

        # asyncio.sleepをモック
        with patch("asyncio.sleep", return_value=None):
            async with StandXHTTPClient(config, jwt_token="test_jwt_token") as client:
                response = await client.get_symbol_price("ETH_USDC")

        # リトライ後に成功
        assert response["mark_price"] == 3500.0


@pytest.mark.asyncio
async def test_api_error(config: Settings) -> None:
    """APIエラー (その他のステータスコード) が正しく処理されることを確認."""
    with aioresponses() as mocked:
        # 400エラーを返すモックレスポンス
        mocked.get(
            "https://perps.standx.com/api/query_symbol_price?symbol=ETH_USDC",
            status=400,
            body="Bad Request",
        )

        async with StandXHTTPClient(config, jwt_token="test_jwt_token") as client:
            with pytest.raises(APIError, match="HTTP 400"):
                await client.get_symbol_price("ETH_USDC")


@pytest.mark.asyncio
async def test_session_not_initialized(config: Settings) -> None:
    """セッション未初期化時にエラーが発生することを確認."""
    client = StandXHTTPClient(config, jwt_token="test_jwt_token")

    with pytest.raises(RuntimeError, match="Session not initialized"):
        await client.get_symbol_price("ETH_USDC")

"""注文管理モジュールのテスト."""

import asyncio
from unittest.mock import AsyncMock, Mock

import pytest

from standx_mm_bot.client import StandXHTTPClient
from standx_mm_bot.config import Settings
from standx_mm_bot.core.order import OrderManager
from standx_mm_bot.models import OrderStatus, Side


@pytest.fixture
def config() -> Settings:
    """テスト用設定."""
    return Settings(
        standx_private_key="0x" + "a" * 64,
        standx_wallet_address="0x1234567890abcdef",
        standx_chain="bsc",
        symbol="ETH-USD",
        order_size=0.001,
    )


@pytest.fixture
def mock_client() -> Mock:
    """モックHTTPクライアント."""
    client = Mock(spec=StandXHTTPClient)
    client.new_order = AsyncMock()
    client.cancel_order = AsyncMock()
    return client


class TestPlaceOrder:
    """place_order のテスト."""

    @pytest.mark.asyncio
    async def test_place_order_success(self, mock_client: Mock, config: Settings) -> None:
        """注文発注が成功することを確認."""
        # モックレスポンス
        mock_client.new_order.return_value = {
            "order_id": "test123",
            "status": "OPEN",
        }

        order_mgr = OrderManager(mock_client, config)
        order = await order_mgr.place_order(
            side=Side.BUY,
            price=3500.0,
            size=0.001,
        )

        # 注文情報の確認
        assert order.id == "test123"
        assert order.symbol == "ETH-USD"
        assert order.side == Side.BUY
        assert order.price == 3500.0
        assert order.size == 0.001
        assert order.status == OrderStatus.OPEN

        # API呼び出しの確認
        mock_client.new_order.assert_called_once_with(
            symbol="ETH-USD",
            side="buy",
            price=3500.0,
            size=0.001,
            order_type="limit",
            time_in_force="alo",
            reduce_only=False,
        )

    @pytest.mark.asyncio
    async def test_place_order_with_request_id(self, mock_client: Mock, config: Settings) -> None:
        """request_idのみのレスポンスでも動作することを確認."""
        # レスポンスにorder_idがない場合
        mock_client.new_order.return_value = {
            "code": 0,
            "message": "success",
            "request_id": "req456",
        }

        order_mgr = OrderManager(mock_client, config)
        order = await order_mgr.place_order(
            side=Side.SELL,
            price=3600.0,
            size=0.001,
        )

        # request_idがorder_idとして使われる
        assert order.id == "req456"
        assert order.side == Side.SELL
        assert order.status == OrderStatus.OPEN  # デフォルト


class TestCancelOrder:
    """cancel_order のテスト."""

    @pytest.mark.asyncio
    async def test_cancel_order_success(self, mock_client: Mock, config: Settings) -> None:
        """注文キャンセルが成功することを確認."""
        mock_client.cancel_order.return_value = {"status": "CANCELLED"}

        order_mgr = OrderManager(mock_client, config)
        await order_mgr.cancel_order("test123")

        # API呼び出しの確認
        mock_client.cancel_order.assert_called_once_with(
            order_id="test123",
            symbol="ETH-USD",
        )


class TestRepositionOrder:
    """reposition_order のテスト."""

    @pytest.mark.asyncio
    async def test_reposition_place_first(self, mock_client: Mock, config: Settings) -> None:
        """発注先行の再配置が正しく動作することを確認."""
        # 新規注文のレスポンス
        mock_client.new_order.return_value = {
            "order_id": "new123",
            "status": "OPEN",
        }
        mock_client.cancel_order.return_value = {"status": "CANCELLED"}

        order_mgr = OrderManager(mock_client, config)
        new_order = await order_mgr.reposition_order(
            old_order_id="old123",
            new_price=3550.0,
            side=Side.BUY,
            size=0.001,
            strategy="place_first",
        )

        # 新規注文情報の確認
        assert new_order.id == "new123"
        assert new_order.price == 3550.0

        # 呼び出し順序の確認
        assert mock_client.new_order.call_count == 1
        assert mock_client.cancel_order.call_count == 1

        # 発注が先に呼ばれたことを確認
        call_order = list(mock_client.method_calls)
        new_order_call = next(i for i, call in enumerate(call_order) if call[0] == "new_order")
        cancel_call = next(i for i, call in enumerate(call_order) if call[0] == "cancel_order")
        assert new_order_call < cancel_call

    @pytest.mark.asyncio
    async def test_reposition_cancel_first(self, mock_client: Mock, config: Settings) -> None:
        """キャンセル先行の再配置が正しく動作することを確認."""
        mock_client.new_order.return_value = {
            "order_id": "new456",
            "status": "OPEN",
        }
        mock_client.cancel_order.return_value = {"status": "CANCELLED"}

        order_mgr = OrderManager(mock_client, config)
        new_order = await order_mgr.reposition_order(
            old_order_id="old456",
            new_price=3450.0,
            side=Side.SELL,
            size=0.001,
            strategy="cancel_first",
        )

        # 新規注文情報の確認
        assert new_order.id == "new456"
        assert new_order.price == 3450.0

        # 呼び出し順序の確認
        call_order = list(mock_client.method_calls)
        cancel_call = next(i for i, call in enumerate(call_order) if call[0] == "cancel_order")
        new_order_call = next(i for i, call in enumerate(call_order) if call[0] == "new_order")
        assert cancel_call < new_order_call

    @pytest.mark.asyncio
    async def test_reposition_new_order_not_open(self, mock_client: Mock, config: Settings) -> None:
        """新規注文がOPENでない場合、旧注文がキャンセルされないことを確認."""
        # 新規注文が失敗（FILLED）
        mock_client.new_order.return_value = {
            "order_id": "new789",
            "status": "FILLED",
        }

        order_mgr = OrderManager(mock_client, config)
        new_order = await order_mgr.reposition_order(
            old_order_id="old789",
            new_price=3500.0,
            side=Side.BUY,
            size=0.001,
            strategy="place_first",
        )

        # 新規注文は返される
        assert new_order.id == "new789"
        assert new_order.status == OrderStatus.FILLED

        # 旧注文はキャンセルされない
        assert mock_client.cancel_order.call_count == 0


class TestConcurrency:
    """並行処理のテスト."""

    @pytest.mark.asyncio
    async def test_concurrent_place_orders(self, mock_client: Mock, config: Settings) -> None:
        """複数の注文を同時に発注しても競合しないことを確認."""
        call_order = []

        async def mock_new_order(*_args, **_kwargs):
            call_order.append("start")
            await asyncio.sleep(0.01)
            call_order.append("end")
            return {"order_id": f"order{len(call_order)}", "status": "OPEN"}

        mock_client.new_order.side_effect = mock_new_order

        order_mgr = OrderManager(mock_client, config)

        # 3つの注文を同時に発注
        orders = await asyncio.gather(
            order_mgr.place_order(Side.BUY, 3500.0, 0.001),
            order_mgr.place_order(Side.BUY, 3510.0, 0.001),
            order_mgr.place_order(Side.BUY, 3520.0, 0.001),
        )

        # 全て成功
        assert len(orders) == 3

        # Lockにより順序が保証される（インターリーブしない）
        assert call_order == [
            "start",
            "end",
            "start",
            "end",
            "start",
            "end",
        ]


# ========================================
# 統合テスト（実API使用、手動実行）
# ========================================


@pytest.fixture
def real_config() -> Settings:
    """実際の.envから設定を読み込む."""
    return Settings()


@pytest.mark.integration
@pytest.mark.asyncio
async def test_place_and_cancel_order_real(real_config: Settings) -> None:
    """
    実注文テスト: 注文発注 → キャンセル.

    前提条件:
    - StandXに$10以上入金済み
    - ORDER_SIZE=0.001

    手順:
    1. 現在価格を取得
    2. 約定しない価格で注文発注（30bps離す）
    3. 即座にキャンセル（1秒以内）
    4. Position=0を確認
    """
    async with StandXHTTPClient(real_config) as client:
        # 現在価格を取得
        price_data = await client.get_symbol_price(real_config.symbol)
        mark_price = float(price_data["mark_price"])

        # 約定しない価格（BUY: 3%下、SELL: 3%上）
        far_buy_price = round(mark_price * 0.97, 2)

        order_mgr = OrderManager(client, real_config)

        # 注文発注
        order = await order_mgr.place_order(
            side=Side.BUY,
            price=far_buy_price,
            size=0.001,
        )

        assert order.id is not None
        assert order.status == OrderStatus.OPEN

        # 即座にキャンセル
        await asyncio.sleep(0.5)
        await order_mgr.cancel_order(order.id)

        # Position確認
        position = await client.get_position(real_config.symbol)
        if isinstance(position, list):
            assert len(position) == 0, "Position should be empty"
        else:
            assert float(position.get("size", 0)) == 0, "Position size should be 0"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_reposition_order_real(real_config: Settings) -> None:
    """
    実注文テスト: 注文再配置.

    手順:
    1. 遠い価格で初回注文
    2. 別の遠い価格に再配置
    3. 両方キャンセル
    4. Position=0を確認
    """
    async with StandXHTTPClient(real_config) as client:
        # 現在価格を取得
        price_data = await client.get_symbol_price(real_config.symbol)
        mark_price = float(price_data["mark_price"])

        # 約定しない価格
        far_price_1 = round(mark_price * 0.97, 2)
        far_price_2 = round(mark_price * 0.96, 2)

        order_mgr = OrderManager(client, real_config)

        # 初回注文
        order1 = await order_mgr.place_order(Side.BUY, far_price_1, 0.001)
        await asyncio.sleep(0.5)

        # 再配置
        order2 = await order_mgr.reposition_order(
            old_order_id=order1.id,
            new_price=far_price_2,
            side=Side.BUY,
            size=0.001,
            strategy="place_first",
        )

        assert order2.id != order1.id
        await asyncio.sleep(0.5)

        # クリーンアップ
        await order_mgr.cancel_order(order2.id)

        # Position確認
        position = await client.get_position(real_config.symbol)
        if isinstance(position, list):
            assert len(position) == 0
        else:
            assert float(position.get("size", 0)) == 0

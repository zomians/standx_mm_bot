"""REST APIクライアントの統合テスト（実際のStandX APIを使用）."""

import pytest

from standx_mm_bot.client import StandXHTTPClient
from standx_mm_bot.config import Settings


@pytest.fixture
def real_config() -> Settings:
    """実際の.envから設定を読み込む."""
    # 統合テストでは実APIを使うため、ドライランを無効化
    return Settings(dry_run=False)


@pytest.mark.integration
@pytest.mark.asyncio
async def test_real_api_order_crud(real_config: Settings) -> None:
    """実際のStandX APIで注文のCRUD操作をテスト（安全性保証）."""
    order_id = None

    async with StandXHTTPClient(real_config) as client:
        try:
            # 現在の価格を取得
            price_response = await client.get_symbol_price(real_config.symbol)
            mark_price = float(price_response["mark_price"])

            # 1. Create: 約定しない価格で注文を発注（mark_priceから50%離れた位置）
            order_price = mark_price * 0.5  # buyの場合、現在価格より50%安い
            order_response = await client.new_order(
                symbol=real_config.symbol,
                side="buy",  # 小文字
                price=order_price,
                size=0.01,  # 最小サイズ
                order_type="limit",
                time_in_force="gtc",
                reduce_only=False,
            )
            assert "order_id" in order_response
            order_id = order_response["order_id"]

            # 2. Read: 未決注文一覧に存在することを確認
            open_orders = await client.get_open_orders(real_config.symbol)
            orders_list = open_orders.get("result") or open_orders.get("data", [])
            order_ids = [order["order_id"] for order in orders_list]
            assert order_id in order_ids

            # 3. Delete: 注文をキャンセル
            cancel_response = await client.cancel_order(order_id, real_config.symbol)
            assert "status" in cancel_response or "code" in cancel_response

            # 4. Read: 削除されたことを確認
            open_orders_after = await client.get_open_orders(real_config.symbol)
            orders_list_after = open_orders_after.get("result") or open_orders_after.get("data", [])
            order_ids_after = [order["order_id"] for order in orders_list_after]
            assert order_id not in order_ids_after

            # 成功時はorder_idをクリア
            order_id = None

        finally:
            # 失敗時のクリーンアップ: 注文が残っている場合はキャンセル
            if order_id is not None:
                try:
                    await client.cancel_order(order_id, real_config.symbol)
                    print(f"[CLEANUP] Cancelled order {order_id}")
                except Exception as cleanup_error:
                    print(f"[CLEANUP ERROR] Failed to cancel order {order_id}: {cleanup_error}")


@pytest.mark.integration
@pytest.mark.asyncio
async def test_real_api_get_symbol_price(real_config: Settings) -> None:
    """実際のStandX APIから価格を取得できることを確認."""
    async with StandXHTTPClient(real_config) as client:
        response = await client.get_symbol_price(real_config.symbol)

    # レスポンスの基本構造を確認（dataラッパーなし）
    assert "mark_price" in response
    assert "index_price" in response
    assert "symbol" in response
    assert response["symbol"] == real_config.symbol

    # 価格が正の数であることを確認
    assert float(response["mark_price"]) > 0
    assert float(response["index_price"]) > 0


@pytest.mark.integration
@pytest.mark.asyncio
async def test_real_api_get_open_orders(real_config: Settings) -> None:
    """実際のStandX APIから未決注文一覧を取得できることを確認."""
    async with StandXHTTPClient(real_config) as client:
        response = await client.get_open_orders(real_config.symbol)

    # レスポンスの基本構造を確認
    # 実際のレスポンス: {'code': 0, 'message': 'success', 'result': [...]}
    assert "result" in response or "data" in response
    orders = response.get("result") or response.get("data", [])

    # 注文リストが存在することを確認（空でも良い）
    assert isinstance(orders, list)


@pytest.mark.integration
@pytest.mark.asyncio
async def test_real_api_get_position(real_config: Settings) -> None:
    """実際のStandX APIからポジション情報を取得できることを確認."""
    async with StandXHTTPClient(real_config) as client:
        response = await client.get_position(real_config.symbol)

    # レスポンスの基本構造を確認
    # ポジションがない場合は空配列が返る可能性がある
    if isinstance(response, list):
        # 空配列の場合はポジションなし
        assert isinstance(response, list)
    elif isinstance(response, dict):
        # オブジェクトの場合はポジション情報あり
        # sizeフィールドが存在することを確認（値は0でもOK）
        assert "size" in response or "data" in response

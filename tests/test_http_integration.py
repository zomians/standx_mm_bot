"""REST APIクライアントの統合テスト（実際のStandX APIを使用）."""

import pytest

from standx_mm_bot.client import StandXHTTPClient
from standx_mm_bot.config import Settings


@pytest.fixture
def real_config() -> Settings:
    """実際の.envから設定を読み込む."""
    return Settings()


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

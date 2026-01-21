"""REST API クライアント."""

import asyncio
import logging
from typing import Any, cast

import aiohttp

from standx_mm_bot.auth import generate_auth_headers, generate_jwt
from standx_mm_bot.client.exceptions import (
    APIError,
    AuthenticationError,
    NetworkError,
)
from standx_mm_bot.config import Settings

logger = logging.getLogger(__name__)


class StandXHTTPClient:
    """StandX REST API クライアント."""

    def __init__(self, config: Settings):
        """
        HTTPクライアントを初期化.

        Args:
            config: アプリケーション設定
        """
        self.config = config
        self.base_url = "https://perps.standx.com"
        self.jwt_token = generate_jwt(
            config.standx_private_key,
            config.standx_wallet_address,
            config.standx_chain,
            config.jwt_expires_seconds,
        )
        self.session: aiohttp.ClientSession | None = None

    async def __aenter__(self) -> "StandXHTTPClient":
        """非同期コンテキストマネージャー (enter)."""
        self.session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """非同期コンテキストマネージャー (exit)."""
        if self.session:
            await self.session.close()

    async def _request(
        self,
        method: str,
        path: str,
        body: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """
        HTTPリクエストを送信.

        Args:
            method: HTTPメソッド (GET, POST)
            path: リクエストパス
            body: リクエストボディ

        Returns:
            dict: レスポンスJSON

        Raises:
            AuthenticationError: 認証エラー (401)
            APIError: APIエラー
            NetworkError: ネットワークエラー
        """
        if self.session is None:
            raise RuntimeError("Session not initialized. Use 'async with' context manager.")

        # 認証ヘッダー生成
        headers = generate_auth_headers(
            self.jwt_token,
            self.config.standx_private_key,
            method,
            path,
            body,
        )
        headers["Content-Type"] = "application/json"

        try:
            async with self.session.request(
                method,
                self.base_url + path,
                json=body,
                headers=headers,
            ) as resp:
                if resp.status == 200:
                    return cast(dict[str, Any], await resp.json())
                elif resp.status == 401:
                    raise AuthenticationError("JWT expired or invalid")
                elif resp.status == 429:
                    # レート制限: 1秒待機してリトライ
                    logger.warning("Rate limited (429). Retrying after 1 second...")
                    await asyncio.sleep(1)
                    return await self._request(method, path, body)
                else:
                    error_text = await resp.text()
                    raise APIError(f"HTTP {resp.status}: {error_text}")
        except aiohttp.ClientError as e:
            raise NetworkError(f"Network error: {e}") from e

    async def get_symbol_price(self, symbol: str) -> dict[str, Any]:
        """
        シンボル価格を取得.

        Args:
            symbol: 取引ペア (例: "ETH_USDC")

        Returns:
            dict: 価格情報
        """
        path = f"/api/query_symbol_price?symbol={symbol}"
        return await self._request("GET", path)

    async def new_order(
        self,
        symbol: str,
        side: str,
        price: float,
        size: float,
        order_type: str = "LIMIT",
        post_only: bool = True,
    ) -> dict[str, Any]:
        """
        新規注文を発注.

        Args:
            symbol: 取引ペア
            side: 注文サイド (BUY/SELL)
            price: 注文価格
            size: 注文サイズ
            order_type: 注文タイプ (LIMIT/MARKET)
            post_only: Post-Onlyフラグ

        Returns:
            dict: 注文情報
        """
        if self.config.dry_run:
            logger.info(
                f"[DRY RUN] new_order: symbol={symbol}, side={side}, "
                f"price={price}, size={size}, type={order_type}, post_only={post_only}"
            )
            # ドライランモード: モックレスポンスを返す
            return {
                "order_id": "dry_run_order_id",
                "symbol": symbol,
                "side": side,
                "price": price,
                "size": size,
                "order_type": order_type,
                "status": "OPEN",
            }

        body = {
            "symbol": symbol,
            "side": side,
            "price": price,
            "size": size,
            "order_type": order_type,
            "post_only": post_only,
        }
        return await self._request("POST", "/api/new_order", body)

    async def cancel_order(self, order_id: str, symbol: str) -> dict[str, Any]:
        """
        注文をキャンセル.

        Args:
            order_id: 注文ID
            symbol: 取引ペア

        Returns:
            dict: キャンセル結果
        """
        if self.config.dry_run:
            logger.info(f"[DRY RUN] cancel_order: order_id={order_id}, symbol={symbol}")
            # ドライランモード: モックレスポンスを返す
            return {
                "order_id": order_id,
                "symbol": symbol,
                "status": "CANCELED",
            }

        body = {"order_id": order_id, "symbol": symbol}
        return await self._request("POST", "/api/cancel_order", body)

    async def get_open_orders(self, symbol: str) -> dict[str, Any]:
        """
        未決注文一覧を取得.

        Args:
            symbol: 取引ペア

        Returns:
            dict: 未決注文一覧
        """
        path = f"/api/query_open_orders?symbol={symbol}"
        return await self._request("GET", path)

    async def get_position(self, symbol: str) -> dict[str, Any]:
        """
        ポジション情報を取得.

        Args:
            symbol: 取引ペア

        Returns:
            dict: ポジション情報
        """
        path = f"/api/query_position?symbol={symbol}"
        return await self._request("GET", path)

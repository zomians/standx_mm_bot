"""REST API クライアント."""

import asyncio
import logging
import uuid
from typing import Any, cast

import aiohttp
import jwt as pyjwt

from standx_mm_bot.auth import (
    generate_auth_headers,
    sign_message_evm,
    sign_message_solana,
)
from standx_mm_bot.client.exceptions import (
    APIError,
    AuthenticationError,
    NetworkError,
)
from standx_mm_bot.config import Settings

logger = logging.getLogger(__name__)


class StandXHTTPClient:
    """StandX REST API クライアント."""

    def __init__(self, config: Settings, jwt_token: str | None = None):
        """
        HTTPクライアントを初期化.

        Args:
            config: アプリケーション設定
            jwt_token: JWTトークン（テスト用、省略時は自動取得）
        """
        self.config = config
        self.base_url = "https://perps.standx.com"
        self.auth_base_url = "https://api.standx.com"
        self.jwt_token = jwt_token
        self.session: aiohttp.ClientSession | None = None

    async def __aenter__(self) -> "StandXHTTPClient":
        """非同期コンテキストマネージャー (enter)."""
        self.session = aiohttp.ClientSession()
        # JWTトークンが未設定の場合のみ取得
        if self.jwt_token is None:
            self.jwt_token = await self._obtain_jwt()
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """非同期コンテキストマネージャー (exit)."""
        if self.session:
            await self.session.close()

    async def _obtain_jwt(self) -> str:
        """
        StandX APIからJWTトークンを取得.

        Returns:
            str: JWTトークン

        Raises:
            AuthenticationError: JWT取得に失敗
        """
        if self.session is None:
            raise RuntimeError("Session not initialized")

        try:
            # Step 1: prepare-signin でsignedDataを取得
            request_id = str(uuid.uuid4())
            prepare_url = (
                f"{self.auth_base_url}/v1/offchain/prepare-signin?chain={self.config.standx_chain}"
            )
            prepare_body = {
                "address": self.config.standx_wallet_address,
                "requestId": request_id,
            }

            async with self.session.post(
                prepare_url,
                json=prepare_body,
                headers={"Content-Type": "application/json"},
            ) as resp:
                if resp.status != 200:
                    error_text = await resp.text()
                    raise AuthenticationError(
                        f"Failed to prepare signin: HTTP {resp.status}: {error_text}"
                    )
                prepare_result = await resp.json()

            signed_data = prepare_result.get("signedData")
            if not signed_data:
                raise AuthenticationError("No signedData in prepare-signin response")

            # Step 2: signedDataをデコードしてmessageを取得
            # signedDataはJWT形式の文字列
            try:
                # JWTをデコード（署名検証なし）
                decoded_payload = pyjwt.decode(signed_data, options={"verify_signature": False})
                message = decoded_payload.get("message")
                if not message:
                    raise AuthenticationError("No message in decoded signedData")
            except Exception as e:
                raise AuthenticationError(f"Failed to decode signedData: {e}") from e

            # チェーン別の署名形式を使用
            chain = self.config.standx_chain.lower()
            if chain == "solana":
                # Solana: JSON+Base64形式
                signature = sign_message_solana(
                    self.config.standx_private_key, message, decoded_payload
                )
            elif chain == "bsc":
                # BSC (EVM): 16進数署名
                signature = sign_message_evm(self.config.standx_private_key, message)
            else:
                raise AuthenticationError(f"Unsupported chain: {self.config.standx_chain}")

            # Step 3: login でJWTトークンを取得
            login_url = f"{self.auth_base_url}/v1/offchain/login?chain={self.config.standx_chain}"
            # signedDataが文字列の場合は元のprepare_resultから取得し直す
            login_signed_data = prepare_result.get("signedData")
            login_body = {
                "signature": signature,
                "signedData": login_signed_data,
                "expiresSeconds": self.config.jwt_expires_seconds,
            }

            async with self.session.post(
                login_url,
                json=login_body,
                headers={"Content-Type": "application/json"},
            ) as resp:
                if resp.status != 200:
                    error_text = await resp.text()
                    raise AuthenticationError(f"Failed to login: HTTP {resp.status}: {error_text}")
                login_result = await resp.json()

            token = login_result.get("token")
            if not token:
                raise AuthenticationError("No token in login response")

            logger.info("Successfully obtained JWT token")
            return str(token)

        except aiohttp.ClientError as e:
            raise AuthenticationError(f"Network error during JWT acquisition: {e}") from e

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

        if self.jwt_token is None:
            raise RuntimeError("JWT token not initialized. Use 'async with' context manager.")

        # チェーンに応じて適切な署名鍵を選択
        # BSC: APIリクエスト署名用Ed25519鍵を使用（JWT認証とは別の鍵）
        # Solana: ウォレット秘密鍵（Ed25519）を使用
        if self.config.standx_chain.lower() == "bsc":
            if not self.config.standx_request_signing_key:
                raise RuntimeError(
                    "BSC chain requires STANDX_REQUEST_SIGNING_KEY in .env. "
                    "Generate wallet with: make wallet-bsc"
                )
            signing_key = self.config.standx_request_signing_key
        else:
            signing_key = self.config.standx_private_key

        # 認証ヘッダー生成（署名計算で使用したペイロード文字列も返される）
        headers, payload_str = generate_auth_headers(
            self.jwt_token,
            signing_key,
            method,
            path,
            body,
            self.config.standx_chain,
        )
        headers["Content-Type"] = "application/json"

        # POSTの場合、署名計算と完全に同じJSON文字列を送信
        request_kwargs: dict[str, Any]
        if method.upper() == "POST" and payload_str:
            logger.debug(f"Request body (exact string used in signature): {payload_str}")
            request_kwargs = {"data": payload_str}
        else:
            request_kwargs = {}

        logger.debug(f"Request headers: {headers}")

        try:
            async with self.session.request(
                method,
                self.base_url + path,
                headers=headers,
                **request_kwargs,
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
        order_type: str = "limit",
        time_in_force: str = "gtc",
        reduce_only: bool = False,
    ) -> dict[str, Any]:
        """
        新規注文を発注.

        Args:
            symbol: 取引ペア
            side: 注文サイド (buy/sell、小文字)
            price: 注文価格
            size: 注文サイズ
            order_type: 注文タイプ (limit/market、小文字)
            time_in_force: 注文有効期限 (gtc/ioc/fok)
            reduce_only: ポジション縮小のみフラグ

        Returns:
            dict: 注文情報
        """
        # API仕様に従ったボディ構築
        body = {
            "symbol": symbol,
            "side": side.lower(),  # 小文字に変換
            "order_type": order_type.lower(),  # 小文字に変換
            "qty": str(size),  # 文字列として送信
            "price": str(price),  # 文字列として送信
            "time_in_force": time_in_force,
            "reduce_only": reduce_only,
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
        path = f"/api/query_positions?symbol={symbol}"
        return await self._request("GET", path)

    async def get_balance(self) -> dict[str, Any]:
        """
        残高情報を取得.

        Returns:
            dict: 残高情報
                - isolated_balance: 隔離ウォレット合計
                - isolated_upnl: 隔離未実現損益
                - cross_balance: クロス自由残高
                - cross_margin: クロス証拠金使用額
                - cross_upnl: クロス未実現損益
                - locked: オーダーロック額
                - cross_available: 利用可能額
                - balance: 総資産
                - upnl: 合計未実現損益
                - equity: アカウント資産額
                - pnl_freeze: 24時間実現損益
        """
        return await self._request("GET", "/api/query_balance")

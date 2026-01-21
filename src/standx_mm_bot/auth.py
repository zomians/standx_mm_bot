"""JWT認証とリクエスト署名モジュール."""

import json
import time

import jwt
from cryptography.hazmat.primitives.asymmetric import ed25519
from nacl.signing import SigningKey


def generate_jwt(
    private_key: str,
    wallet_address: str,
    chain: str,
    expires_seconds: int = 604800,
) -> str:
    """
    JWT生成.

    Args:
        private_key: Ed25519秘密鍵（hex形式、0xプレフィックス付き）
        wallet_address: ウォレットアドレス
        chain: チェーン（bsc/solana）
        expires_seconds: 有効期限（秒、デフォルト7日）

    Returns:
        str: JWTトークン
    """
    # 0xプレフィックスを除去
    key_hex = private_key.removeprefix("0x")
    # hex形式の秘密鍵をバイト列に変換
    key_bytes = bytes.fromhex(key_hex)

    # cryptographyのEd25519PrivateKeyに変換
    ed25519_key = ed25519.Ed25519PrivateKey.from_private_bytes(key_bytes)

    payload = {
        "wallet_address": wallet_address,
        "chain": chain,
        "exp": int(time.time()) + expires_seconds,
    }

    token = jwt.encode(payload, ed25519_key, algorithm="EdDSA")
    return token


def sign_request(
    private_key: str,
    method: str,
    path: str,
    body: dict[str, object] | None = None,
) -> dict[str, str]:
    """
    リクエスト署名.

    Args:
        private_key: Ed25519秘密鍵（hex形式、0xプレフィックス付き）
        method: HTTPメソッド（GET, POST, etc.）
        path: リクエストパス（/api/new_order）
        body: リクエストボディ（JSON）

    Returns:
        dict: 署名ヘッダー（X-Standx-Timestamp, X-Standx-Signature）
    """
    # 0xプレフィックスを除去してbytes型に変換
    key_hex = private_key.removeprefix("0x")
    key_bytes = bytes.fromhex(key_hex)
    signing_key = SigningKey(key_bytes)

    timestamp = str(int(time.time() * 1000))

    # 署名対象: timestamp + method + path + body
    message = timestamp + method.upper() + path
    if body:
        message += json.dumps(body, separators=(",", ":"))

    signature = signing_key.sign(message.encode()).signature.hex()

    return {
        "X-Standx-Timestamp": timestamp,
        "X-Standx-Signature": signature,
    }


def generate_auth_headers(
    jwt_token: str,
    private_key: str,
    method: str,
    path: str,
    body: dict[str, object] | None = None,
) -> dict[str, str]:
    """
    認証ヘッダー生成.

    Args:
        jwt_token: JWTトークン
        private_key: Ed25519秘密鍵（hex形式、0xプレフィックス付き）
        method: HTTPメソッド
        path: リクエストパス
        body: リクエストボディ

    Returns:
        dict: 認証ヘッダー（Authorization + 署名ヘッダー）
    """
    signature_headers = sign_request(private_key, method, path, body)

    return {
        "Authorization": f"Bearer {jwt_token}",
        **signature_headers,
    }

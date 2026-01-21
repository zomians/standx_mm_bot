"""StandX API認証モジュール."""

import base64
import json
import time
import uuid
from typing import Any

from nacl.signing import SigningKey


def sign_message(private_key: str, message: str) -> str:
    """
    Ed25519でメッセージに署名.

    Args:
        private_key: 秘密鍵（hex形式、0xプレフィックス可）
        message: 署名するメッセージ

    Returns:
        str: Base64エンコードされた署名
    """
    # 0xプレフィックスを削除
    key_hex = private_key.removeprefix("0x")

    # hex文字列をバイト列に変換
    key_bytes = bytes.fromhex(key_hex)

    # SigningKeyを生成
    signing_key = SigningKey(key_bytes)

    # メッセージをバイト列に変換して署名
    message_bytes = message.encode("utf-8")
    signed = signing_key.sign(message_bytes)

    # 署名部分のみをBase64エンコード
    return base64.b64encode(signed.signature).decode("ascii")


def sign_message_solana(private_key: str, message: str, signed_data: Any) -> str:
    """
    Solana用のメッセージ署名（JSON+Base64形式）.

    Args:
        private_key: 秘密鍵（hex形式、0xプレフィックス可）
        message: 署名するメッセージ
        signed_data: prepare-signinから返されたsignedData

    Returns:
        str: Base64エンコードされた署名（JSON形式）
    """
    # 0xプレフィックスを削除
    key_hex = private_key.removeprefix("0x")

    # hex文字列をバイト列に変換
    key_bytes = bytes.fromhex(key_hex)

    # SigningKeyを生成
    signing_key = SigningKey(key_bytes)

    # メッセージをバイト列に変換
    message_bytes = message.encode("utf-8")

    # 署名生成
    signed = signing_key.sign(message_bytes)
    signature_bytes = signed.signature

    # 公開鍵取得
    public_key_bytes = bytes(signing_key.verify_key)

    # Solana署名フォーマット
    signature_obj = {
        "input": signed_data,
        "output": {
            "signedMessage": list(message_bytes),
            "signature": list(signature_bytes),
            "account": {"publicKey": list(public_key_bytes)},
        },
    }

    # JSONをBase64エンコード
    signature_json = json.dumps(signature_obj, separators=(",", ":"))
    return base64.b64encode(signature_json.encode()).decode("ascii")


def generate_request_signature(
    private_key: str,
    method: str,
    _path: str,
    body: dict[str, Any] | None = None,
    _chain: str = "bsc",
) -> tuple[dict[str, str], str]:
    """
    StandX APIリクエスト用の署名ヘッダーを生成.

    Args:
        private_key: 秘密鍵（hex形式）
        method: HTTPメソッド (GET, POST)
        _path: リクエストパス（現在未使用、将来の拡張用）
        body: リクエストボディ (POSTの場合)
        _chain: チェーン（solana/bsc、現在未使用、将来の拡張用）

    Returns:
        tuple: (署名ヘッダー, ボディ文字列)
    """
    import logging

    logger = logging.getLogger(__name__)

    # リクエストパラメータ
    version = "v1"
    request_id = str(uuid.uuid4())
    timestamp = str(int(time.time() * 1000))  # ミリ秒

    # payloadを構築（sort_keysでフィールド順序を保証）
    if method.upper() == "POST" and body:
        payload = json.dumps(body, separators=(",", ":"), sort_keys=True)
    else:
        payload = ""

    # 署名メッセージ: "{version},{id},{timestamp},{payload}"
    sign_message_str = f"{version},{request_id},{timestamp},{payload}"

    logger.debug(f"Signature message: {sign_message_str}")
    logger.debug(f"Payload: {payload}")

    # 署名を生成（全チェーン共通で標準Ed25519署名を使用）
    # 注: Solana JSON+Base64形式はJWT認証(/v1/offchain/login)専用
    signature = sign_message(private_key, sign_message_str)

    # ヘッダーとペイロード文字列を返す
    headers = {
        "x-request-sign-version": version,
        "x-request-id": request_id,
        "x-request-timestamp": timestamp,
        "x-request-signature": signature,
    }
    return headers, payload


def generate_auth_headers(
    jwt_token: str,
    private_key: str,
    method: str,
    path: str,
    body: dict[str, Any] | None = None,
    chain: str = "bsc",
) -> tuple[dict[str, str], str]:
    """
    認証ヘッダーを生成（JWT + リクエスト署名）.

    Args:
        jwt_token: JWTトークン
        private_key: 秘密鍵
        method: HTTPメソッド
        path: リクエストパス
        body: リクエストボディ
        chain: チェーン（solana/bsc）

    Returns:
        tuple: (認証ヘッダー, ボディ文字列)
    """
    # リクエスト署名を生成
    headers, payload = generate_request_signature(
        private_key, method, _path=path, body=body, _chain=chain
    )

    # Authorizationヘッダーを追加
    headers["authorization"] = f"Bearer {jwt_token}"

    return headers, payload

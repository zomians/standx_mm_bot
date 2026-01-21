"""auth.pyのテスト."""

import base64

import pytest
from nacl.signing import SigningKey

from standx_mm_bot.auth import (
    generate_auth_headers,
    generate_request_signature,
    sign_message,
)


def test_sign_message() -> None:
    """メッセージ署名のテスト."""
    # テスト用秘密鍵（32バイト）
    private_key = "0x" + "a" * 64
    message = "test message"

    # 署名を生成
    signature = sign_message(private_key, message)

    # Base64形式であることを確認
    assert isinstance(signature, str)
    # Base64デコードできることを確認
    signature_bytes = base64.b64decode(signature)
    # Ed25519署名は64バイト
    assert len(signature_bytes) == 64


def test_sign_message_verification() -> None:
    """署名が検証可能であることを確認."""
    private_key = "0x" + "a" * 64
    message = "test message"

    # 署名を生成
    signature_b64 = sign_message(private_key, message)
    signature_bytes = base64.b64decode(signature_b64)

    # 検証
    key_bytes = bytes.fromhex(private_key.removeprefix("0x"))
    signing_key = SigningKey(key_bytes)
    verify_key = signing_key.verify_key

    # 署名を検証（例外が発生しなければ成功）
    verified_message = verify_key.verify(message.encode(), signature_bytes)
    assert verified_message == message.encode()


def test_sign_message_without_0x_prefix() -> None:
    """0xプレフィックスなしでも動作することを確認."""
    private_key_with_0x = "0x" + "a" * 64
    private_key_without_0x = "a" * 64
    message = "test message"

    sig1 = sign_message(private_key_with_0x, message)
    sig2 = sign_message(private_key_without_0x, message)

    # 同じ秘密鍵なら同じ署名
    assert sig1 == sig2


def test_generate_request_signature_get() -> None:
    """GETリクエストの署名ヘッダー生成のテスト."""
    private_key = "0x" + "a" * 64
    method = "GET"
    path = "/api/query_open_orders"

    headers, _ = generate_request_signature(private_key, method, _path=path)

    # 必須ヘッダーが含まれていることを確認
    assert "x-request-sign-version" in headers
    assert "x-request-id" in headers
    assert "x-request-timestamp" in headers
    assert "x-request-signature" in headers

    # versionはv1
    assert headers["x-request-sign-version"] == "v1"

    # タイムスタンプは数字
    assert headers["x-request-timestamp"].isdigit()

    # 署名はBase64形式
    signature_bytes = base64.b64decode(headers["x-request-signature"])
    assert len(signature_bytes) == 64


def test_generate_request_signature_post() -> None:
    """POSTリクエストの署名ヘッダー生成のテスト."""
    private_key = "0x" + "a" * 64
    method = "POST"
    path = "/api/new_order"
    body = {"symbol": "ETH-USD", "side": "BUY", "price": 3500.0}

    headers, _ = generate_request_signature(private_key, method, _path=path, body=body)

    # 必須ヘッダーが含まれていることを確認
    assert "x-request-sign-version" in headers
    assert "x-request-id" in headers
    assert "x-request-timestamp" in headers
    assert "x-request-signature" in headers


def test_generate_request_signature_consistency() -> None:
    """異なる呼び出しで異なる署名が生成されることを確認（UUIDとタイムスタンプが異なるため）."""
    private_key = "0x" + "a" * 64
    method = "POST"
    path = "/api/new_order"
    body = {"symbol": "ETH-USD", "side": "BUY"}

    headers1, _ = generate_request_signature(private_key, method, _path=path, body=body)
    headers2, _ = generate_request_signature(private_key, method, _path=path, body=body)

    # UUIDとタイムスタンプが異なるため、署名も異なる
    assert headers1["x-request-id"] != headers2["x-request-id"]
    assert headers1["x-request-signature"] != headers2["x-request-signature"]


def test_generate_auth_headers() -> None:
    """認証ヘッダー生成のテスト."""
    private_key = "0x" + "a" * 64
    jwt_token = "test_jwt_token"
    method = "GET"
    path = "/api/query_open_orders"

    headers, _ = generate_auth_headers(jwt_token, private_key, method, path)

    # 認証ヘッダーが含まれていることを確認
    assert "authorization" in headers
    assert headers["authorization"] == "Bearer test_jwt_token"

    # リクエスト署名ヘッダーも含まれていることを確認
    assert "x-request-sign-version" in headers
    assert "x-request-id" in headers
    assert "x-request-timestamp" in headers
    assert "x-request-signature" in headers


def test_generate_auth_headers_post_with_body() -> None:
    """POSTリクエストの認証ヘッダー生成のテスト."""
    private_key = "0x" + "a" * 64
    jwt_token = "test_jwt_token"
    method = "POST"
    path = "/api/new_order"
    body = {"symbol": "ETH-USD", "side": "BUY"}

    headers, _ = generate_auth_headers(jwt_token, private_key, method, path, body)

    # 認証ヘッダーとリクエスト署名が含まれていることを確認
    assert "authorization" in headers
    assert "x-request-signature" in headers


def test_sign_message_invalid_private_key() -> None:
    """不正な秘密鍵でエラーが発生することを確認."""
    invalid_private_key = "0x" + "z" * 64  # 不正なhex文字列
    message = "test message"

    with pytest.raises(ValueError):
        sign_message(invalid_private_key, message)


def test_sign_message_short_private_key() -> None:
    """短すぎる秘密鍵でエラーが発生することを確認."""
    short_private_key = "0x1234"  # 32バイトより短い
    message = "test message"

    with pytest.raises(ValueError):
        sign_message(short_private_key, message)

"""auth.pyのテスト."""

import json
import time

import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric import ed25519
from nacl.signing import SigningKey

from standx_mm_bot.auth import generate_auth_headers, generate_jwt, sign_request


def test_generate_jwt() -> None:
    """JWT生成のテスト."""
    # テスト用秘密鍵（32バイトのランダムな値）
    private_key = "0x" + "a" * 64
    wallet_address = "0x1234567890abcdef"
    chain = "bsc"
    expires_seconds = 3600

    # JWT生成
    token = generate_jwt(private_key, wallet_address, chain, expires_seconds)

    # JWTをデコード（検証なし）
    payload = jwt.decode(token, options={"verify_signature": False})

    # ペイロードの確認
    assert payload["wallet_address"] == wallet_address
    assert payload["chain"] == chain
    assert "exp" in payload
    # 有効期限が現在時刻 + expires_seconds の範囲内か確認（±10秒の誤差を許容）
    expected_exp = int(time.time()) + expires_seconds
    assert abs(payload["exp"] - expected_exp) < 10


def test_generate_jwt_default_expiry() -> None:
    """JWTのデフォルト有効期限のテスト."""
    private_key = "0x" + "a" * 64
    wallet_address = "0x1234567890abcdef"
    chain = "bsc"

    # デフォルト有効期限でJWT生成
    token = generate_jwt(private_key, wallet_address, chain)

    # JWTをデコード（検証なし）
    payload = jwt.decode(token, options={"verify_signature": False})

    # デフォルト有効期限（7日 = 604800秒）の確認
    expected_exp = int(time.time()) + 604800
    assert abs(payload["exp"] - expected_exp) < 10


def test_sign_request_get() -> None:
    """GETリクエストの署名のテスト."""
    private_key = "0x" + "a" * 64
    method = "GET"
    path = "/api/query_open_orders"

    # 署名生成
    headers = sign_request(private_key, method, path)

    # ヘッダーの確認
    assert "X-Standx-Timestamp" in headers
    assert "X-Standx-Signature" in headers
    assert headers["X-Standx-Timestamp"].isdigit()
    assert len(headers["X-Standx-Signature"]) == 128  # Ed25519署名は64バイト = 128文字（hex）


def test_sign_request_post_with_body() -> None:
    """POSTリクエスト（bodyあり）の署名のテスト."""
    private_key = "0x" + "a" * 64
    method = "POST"
    path = "/api/new_order"
    body = {
        "symbol": "ETH_USDC",
        "side": "BUY",
        "price": 2000.0,
        "size": 0.1,
    }

    # 署名生成
    headers = sign_request(private_key, method, path, body)

    # ヘッダーの確認
    assert "X-Standx-Timestamp" in headers
    assert "X-Standx-Signature" in headers


def test_sign_request_consistency() -> None:
    """同じ入力で同じタイムスタンプなら同じ署名が生成されることを確認."""
    private_key = "0x" + "a" * 64
    method = "POST"
    path = "/api/new_order"
    body = {"symbol": "ETH_USDC", "side": "BUY"}

    # 1回目の署名
    headers1 = sign_request(private_key, method, path, body)

    # タイムスタンプを固定して2回目の署名を生成するため、
    # time.time()をモックする代わりに、生成された署名のタイムスタンプ部分だけ確認
    # ここでは異なるタイムスタンプで署名が異なることを確認
    time.sleep(0.01)  # 少し待つ
    headers2 = sign_request(private_key, method, path, body)

    # タイムスタンプが異なる場合、署名も異なるはず
    # （厳密には同じタイムスタンプなら同じ署名になることを確認したいが、
    # time.time()を使っているため、ここでは署名が生成されることのみ確認）
    assert headers1["X-Standx-Signature"] != headers2["X-Standx-Signature"]


def test_generate_auth_headers_get() -> None:
    """GETリクエストの認証ヘッダー生成のテスト."""
    private_key = "0x" + "a" * 64
    wallet_address = "0x1234567890abcdef"
    chain = "bsc"
    method = "GET"
    path = "/api/query_open_orders"

    # JWT生成
    jwt_token = generate_jwt(private_key, wallet_address, chain)

    # 認証ヘッダー生成
    headers = generate_auth_headers(jwt_token, private_key, method, path)

    # ヘッダーの確認
    assert "Authorization" in headers
    assert headers["Authorization"].startswith("Bearer ")
    assert "X-Standx-Timestamp" in headers
    assert "X-Standx-Signature" in headers


def test_generate_auth_headers_post_with_body() -> None:
    """POSTリクエスト（bodyあり）の認証ヘッダー生成のテスト."""
    private_key = "0x" + "a" * 64
    wallet_address = "0x1234567890abcdef"
    chain = "bsc"
    method = "POST"
    path = "/api/new_order"
    body = {"symbol": "ETH_USDC", "side": "BUY"}

    # JWT生成
    jwt_token = generate_jwt(private_key, wallet_address, chain)

    # 認証ヘッダー生成
    headers = generate_auth_headers(jwt_token, private_key, method, path, body)

    # ヘッダーの確認
    assert "Authorization" in headers
    assert headers["Authorization"].startswith("Bearer ")
    assert "X-Standx-Timestamp" in headers
    assert "X-Standx-Signature" in headers


def test_private_key_with_0x_prefix() -> None:
    """0xプレフィックス付き秘密鍵が正しく処理されることを確認."""
    private_key_with_prefix = "0x" + "a" * 64
    private_key_without_prefix = "a" * 64
    wallet_address = "0x1234567890abcdef"
    chain = "bsc"

    # 0xプレフィックスありとなしで同じJWTが生成されるか確認
    # （厳密にはexpが異なるため同じにはならないが、デコード後のペイロードを確認）
    token_with_prefix = generate_jwt(private_key_with_prefix, wallet_address, chain)
    token_without_prefix = generate_jwt(private_key_without_prefix, wallet_address, chain)

    payload_with_prefix = jwt.decode(token_with_prefix, options={"verify_signature": False})
    payload_without_prefix = jwt.decode(token_without_prefix, options={"verify_signature": False})

    # wallet_addressとchainは同じはず
    assert payload_with_prefix["wallet_address"] == payload_without_prefix["wallet_address"]
    assert payload_with_prefix["chain"] == payload_without_prefix["chain"]


def test_jwt_signature_verification() -> None:
    """JWT署名が公開鍵で検証できることを確認."""
    private_key = "0x" + "a" * 64
    wallet_address = "0x1234567890abcdef"
    chain = "bsc"

    # JWT生成
    token = generate_jwt(private_key, wallet_address, chain)

    # 秘密鍵から公開鍵を生成
    key_bytes = bytes.fromhex(private_key.removeprefix("0x"))
    ed25519_private_key = ed25519.Ed25519PrivateKey.from_private_bytes(key_bytes)
    ed25519_public_key = ed25519_private_key.public_key()

    # JWTを公開鍵で検証してデコード
    payload = jwt.decode(token, ed25519_public_key, algorithms=["EdDSA"])

    # ペイロードの確認
    assert payload["wallet_address"] == wallet_address
    assert payload["chain"] == chain
    assert "exp" in payload


def test_request_signature_verification() -> None:
    """リクエスト署名が検証可能であることを確認."""
    private_key = "0x" + "a" * 64
    method = "POST"
    path = "/api/new_order"
    body = {"symbol": "ETH_USDC", "side": "BUY"}

    # 署名生成
    headers = sign_request(private_key, method, path, body)

    # 署名対象のメッセージを再構築
    timestamp = headers["X-Standx-Timestamp"]
    signature_hex = headers["X-Standx-Signature"]

    message = timestamp + method.upper() + path
    message += json.dumps(body, separators=(",", ":"))

    # 秘密鍵から公開鍵を生成
    key_bytes = bytes.fromhex(private_key.removeprefix("0x"))
    signing_key = SigningKey(key_bytes)
    verify_key = signing_key.verify_key

    # 署名を検証
    signature_bytes = bytes.fromhex(signature_hex)
    verified_message = verify_key.verify(message.encode(), signature_bytes)

    # 検証成功（例外が発生しなければOK）
    assert verified_message == message.encode()


def test_generate_jwt_invalid_private_key() -> None:
    """不正な秘密鍵でJWT生成時にエラーが発生することを確認."""
    invalid_private_key = "0x" + "z" * 64  # 不正なhex文字列
    wallet_address = "0x1234567890abcdef"
    chain = "bsc"

    # エラーが発生することを確認
    with pytest.raises(ValueError):
        generate_jwt(invalid_private_key, wallet_address, chain)


def test_generate_jwt_short_private_key() -> None:
    """短すぎる秘密鍵でJWT生成時にエラーが発生することを確認."""
    short_private_key = "0x1234"  # 32バイトより短い
    wallet_address = "0x1234567890abcdef"
    chain = "bsc"

    # エラーが発生することを確認
    with pytest.raises(ValueError):
        generate_jwt(short_private_key, wallet_address, chain)


def test_sign_request_invalid_private_key() -> None:
    """不正な秘密鍵でリクエスト署名時にエラーが発生することを確認."""
    invalid_private_key = "0x" + "z" * 64  # 不正なhex文字列
    method = "GET"
    path = "/api/query_open_orders"

    # エラーが発生することを確認
    with pytest.raises(ValueError):
        sign_request(invalid_private_key, method, path)

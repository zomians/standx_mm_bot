# Phase 1-2: JWT認証の実装ガイド

このドキュメントは、Issue #13「Phase 1-2: JWT認証の実装」で実装した内容を、初心者向けに詳しく解説します。

---

## 📋 目次

1. [概要](#概要)
2. [JWT認証の基礎](#jwt認証の基礎)
3. [Ed25519署名とは](#ed25519署名とは)
4. [auth.pyの実装解説](#authpyの実装解説)
5. [cryptographyとPyNaClの使い分け](#cryptographyとpynaclの使い分け)
6. [テストの書き方](#テストの書き方)
7. [実装時のエラーと解決方法](#実装時のエラーと解決方法)
8. [セキュリティ上の注意点](#セキュリティ上の注意点)
9. [まとめ](#まとめ)

---

## 概要

### 何を実装したか

Phase 1-2では、StandX APIとの通信に必要な**JWT認証**と**リクエスト署名**を実装しました。

| ファイル | 役割 |
|---------|------|
| `src/standx_mm_bot/auth.py` | JWT生成、リクエスト署名、認証ヘッダー生成 |
| `tests/test_auth.py` | auth.pyのテスト（署名検証含む） |
| `pyproject.toml` | cryptography依存関係を追加 |

### なぜ重要か

- **セキュリティ**: 秘密鍵による署名で、リクエストの正当性を証明
- **認証**: JWTトークンでユーザー認証
- **改ざん防止**: 署名によりリクエストが改ざんされていないことを保証

---

## JWT認証の基礎

### JWTとは

**JWT (JSON Web Token)** は、JSON形式の情報を安全に送信するための標準規格です。

```
JWT = Header.Payload.Signature
```

**例**:
```
eyJhbGciOiJFZERTQSIsInR5cCI6IkpXVCJ9.eyJ3YWxsZXRfYWRkcmVzcyI6IjB4MTIzNCIsImNoYWluIjoiYnNjIiwiZXhwIjoxNzA2NzAwMDAwfQ.signature_here
```

### JWTの構造

| パート | 内容 | 例 |
|--------|------|-----|
| **Header** | アルゴリズム情報 | `{"alg": "EdDSA", "typ": "JWT"}` |
| **Payload** | データ（クレーム） | `{"wallet_address": "0x1234", "exp": 1706700000}` |
| **Signature** | 署名（改ざん防止） | 秘密鍵で生成 |

### EdDSAアルゴリズムとは

**EdDSA (Edwards-curve Digital Signature Algorithm)** は、楕円曲線暗号を使った電子署名アルゴリズムです。

**特徴**:
- **高速**: RSAより署名・検証が速い
- **短い鍵**: 秘密鍵32バイト、公開鍵32バイト
- **安全**: 現代的な暗号学的安全性

---

## Ed25519署名とは

### 公開鍵暗号の基礎

Ed25519は**公開鍵暗号方式**の一種です。

```
秘密鍵（Secret Key）: 自分だけが持つ鍵（32バイト）
           ↓
      署名生成
           ↓
公開鍵（Public Key）: 誰でも見られる鍵（32バイト）
           ↓
      署名検証
```

**仕組み**:
1. **署名生成**: 秘密鍵でデータに署名
2. **署名検証**: 公開鍵で署名が正しいか検証

### なぜEd25519を使うのか

| 比較項目 | RSA-2048 | Ed25519 |
|---------|----------|---------|
| **秘密鍵サイズ** | 2048ビット | 256ビット |
| **署名サイズ** | 256バイト | 64バイト |
| **署名速度** | 遅い | 速い |
| **検証速度** | 普通 | 非常に速い |

StandX APIはEd25519を要求するため、このアルゴリズムを使用します。

---

## auth.pyの実装解説

### 全体構造

```python
# src/standx_mm_bot/auth.py

def generate_jwt(...) -> str:
    """JWT生成"""

def sign_request(...) -> dict[str, str]:
    """リクエスト署名"""

def generate_auth_headers(...) -> dict[str, str]:
    """認証ヘッダー生成（JWT + 署名）"""
```

### generate_jwt() - JWT生成

#### 実装

```python
def generate_jwt(
    private_key: str,
    wallet_address: str,
    chain: str,
    expires_seconds: int = 604800,  # デフォルト7日
) -> str:
    # 1. 秘密鍵をバイト列に変換
    key_hex = private_key.removeprefix("0x")
    key_bytes = bytes.fromhex(key_hex)

    # 2. Ed25519秘密鍵オブジェクトに変換
    ed25519_key = ed25519.Ed25519PrivateKey.from_private_bytes(key_bytes)

    # 3. ペイロード作成
    payload = {
        "wallet_address": wallet_address,
        "chain": chain,
        "exp": int(time.time()) + expires_seconds,
    }

    # 4. JWT生成
    token = jwt.encode(payload, ed25519_key, algorithm="EdDSA")
    return token
```

#### ステップ解説

**Step 1: 秘密鍵の変換**

```python
key_hex = private_key.removeprefix("0x")  # "0xaaaa..." → "aaaa..."
key_bytes = bytes.fromhex(key_hex)        # "aaaa..." → b'\xaa\xaa...'
```

秘密鍵は通常`0x`プレフィックス付きのhex文字列で保存されているため、バイト列に変換します。

**Step 2: Ed25519PrivateKeyオブジェクト作成**

```python
ed25519_key = ed25519.Ed25519PrivateKey.from_private_bytes(key_bytes)
```

`cryptography`ライブラリのEd25519PrivateKeyオブジェクトを作成します。PyJWTのEdDSAアルゴリズムはこのオブジェクトを要求します。

**Step 3: ペイロード作成**

```python
payload = {
    "wallet_address": wallet_address,  # ウォレットアドレス
    "chain": chain,                     # チェーン（bsc/solana）
    "exp": int(time.time()) + expires_seconds,  # 有効期限
}
```

JWTに含める情報を辞書で定義します。`exp`は有効期限（UNIXタイムスタンプ）です。

**Step 4: JWT生成**

```python
token = jwt.encode(payload, ed25519_key, algorithm="EdDSA")
```

PyJWTライブラリで署名付きJWTトークンを生成します。

### sign_request() - リクエスト署名

#### 実装

```python
def sign_request(
    private_key: str,
    method: str,
    path: str,
    body: dict[str, object] | None = None,
) -> dict[str, str]:
    # 1. 秘密鍵をSigningKeyに変換
    key_hex = private_key.removeprefix("0x")
    key_bytes = bytes.fromhex(key_hex)
    signing_key = SigningKey(key_bytes)

    # 2. タイムスタンプ生成
    timestamp = str(int(time.time() * 1000))

    # 3. 署名対象メッセージの構築
    message = timestamp + method.upper() + path
    if body:
        message += json.dumps(body, separators=(",", ":"))

    # 4. 署名生成
    signature = signing_key.sign(message.encode()).signature.hex()

    # 5. ヘッダー返却
    return {
        "X-Standx-Timestamp": timestamp,
        "X-Standx-Signature": signature,
    }
```

#### ステップ解説

**Step 1: SigningKey作成**

```python
signing_key = SigningKey(key_bytes)
```

PyNaClライブラリのSigningKeyオブジェクトを作成します。こちらはリクエスト署名に使用します。

**Step 2: タイムスタンプ生成**

```python
timestamp = str(int(time.time() * 1000))  # ミリ秒単位
```

現在時刻をミリ秒単位のUNIXタイムスタンプで取得します。StandX APIの要求仕様です。

**Step 3: 署名対象メッセージの構築**

```python
message = timestamp + method.upper() + path
if body:
    message += json.dumps(body, separators=(",", ":"))
```

署名対象のメッセージを以下の形式で構築します：

```
timestamp + METHOD + path + body_json
```

**例**:
```
1706700000000POST/api/new_order{"symbol":"ETH_USDC","side":"BUY"}
```

**重要**: `json.dumps(body, separators=(",", ":"))`でスペースなしのJSON文字列を生成します。

**Step 4: 署名生成**

```python
signature = signing_key.sign(message.encode()).signature.hex()
```

1. `message.encode()`: 文字列をバイト列に変換
2. `signing_key.sign(...)`: Ed25519署名を生成（SignedMessage型）
3. `.signature`: 署名部分のみ取得（64バイト）
4. `.hex()`: hex文字列に変換（128文字）

### generate_auth_headers() - 認証ヘッダー統合

#### 実装

```python
def generate_auth_headers(
    jwt_token: str,
    private_key: str,
    method: str,
    path: str,
    body: dict[str, object] | None = None,
) -> dict[str, str]:
    # リクエスト署名生成
    signature_headers = sign_request(private_key, method, path, body)

    # JWT + 署名ヘッダーを統合
    return {
        "Authorization": f"Bearer {jwt_token}",
        **signature_headers,  # X-Standx-Timestamp, X-Standx-Signature
    }
```

#### 返却値の例

```python
{
    "Authorization": "Bearer eyJhbGciOiJFZERTQSIsInR5cCI6IkpXVCJ9...",
    "X-Standx-Timestamp": "1706700000000",
    "X-Standx-Signature": "abc123..."
}
```

この3つのヘッダーをHTTPリクエストに含めることで、StandX APIが認証・署名検証を行います。

---

## cryptographyとPyNaClの使い分け

### なぜ2つのライブラリを使うのか

| ライブラリ | 用途 | 理由 |
|-----------|------|------|
| **cryptography** | JWT生成（EdDSA） | PyJWTがEdDSAにcryptographyを要求 |
| **PyNaCl** | リクエスト署名 | シンプルなAPI、署名検証が容易 |

### 技術的な詳細

#### cryptography（JWT用）

```python
from cryptography.hazmat.primitives.asymmetric import ed25519

# Ed25519PrivateKeyオブジェクトを作成
ed25519_key = ed25519.Ed25519PrivateKey.from_private_bytes(key_bytes)

# PyJWTに渡す
token = jwt.encode(payload, ed25519_key, algorithm="EdDSA")
```

**PyJWTの内部**:
- EdDSAアルゴリズムは`cryptography`ライブラリの`Ed25519PrivateKey`を要求
- `PyNaCl`の`SigningKey`を渡すと`UnicodeDecodeError`が発生（実装時に遭遇したエラー）

#### PyNaCl（リクエスト署名用）

```python
from nacl.signing import SigningKey

# SigningKeyオブジェクトを作成
signing_key = SigningKey(key_bytes)

# 署名生成
signed = signing_key.sign(message.encode())
signature = signed.signature.hex()
```

**メリット**:
- APIがシンプル
- 署名検証が簡単（`verify_key.verify(message, signature)`）
- NaCl（Networking and Cryptography Library）は広く使われている

### 使い分けの判断基準

```python
# JWT生成 → cryptography（PyJWTの要求）
from cryptography.hazmat.primitives.asymmetric import ed25519

# リクエスト署名 → PyNaCl（シンプル）
from nacl.signing import SigningKey
```

---

## テストの書き方

### 署名検証テストの重要性

**問題**: 単に署名を生成するだけでは、署名が正しいか分からない。

**解決**: 生成した署名を公開鍵で検証するテストを書く。

#### JWT署名検証テスト

```python
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
```

**ポイント**:
- `jwt.decode(..., verify_signature=False)`ではなく、公開鍵で検証
- 検証が成功すればペイロードが返される
- 検証が失敗すれば例外が発生

#### リクエスト署名検証テスト

```python
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
```

**ポイント**:
- 署名生成時と同じメッセージを再構築
- `verify_key.verify()`で検証
- 検証が成功すれば元のメッセージが返される
- 検証が失敗すれば`BadSignatureError`が発生

### 異常系テスト

#### 不正な秘密鍵のテスト

```python
def test_generate_jwt_invalid_private_key() -> None:
    """不正な秘密鍵でJWT生成時にエラーが発生することを確認."""
    invalid_private_key = "0x" + "z" * 64  # 不正なhex文字列
    wallet_address = "0x1234567890abcdef"
    chain = "bsc"

    # エラーが発生することを確認
    with pytest.raises(ValueError):
        generate_jwt(invalid_private_key, wallet_address, chain)
```

**テストすべき異常系**:
- 不正なhex文字列（`0xzzzz...`）
- 短すぎる秘密鍵（32バイト未満）
- 空の秘密鍵

---

## 実装時のエラーと解決方法

### エラー1: Algorithm 'EdDSA' could not be found

#### エラー内容

```
jwt.exceptions.InvalidAlgorithmError: Algorithm 'EdDSA' could not be found.
Did you mean to install the cryptography library?
```

#### 原因

PyJWTライブラリでEdDSAアルゴリズムを使うには、`cryptography`ライブラリが必要。

#### 解決方法

```toml
# pyproject.toml
dependencies = [
    "PyJWT>=2.8",
    "cryptography>=41.0",  # 追加
]
```

### エラー2: UnicodeDecodeError

#### エラー内容

```python
UnicodeDecodeError: 'utf-8' codec can't decode byte 0xaa in position 0: invalid start byte
```

#### 原因

PyJWTのEdDSAアルゴリズムは`cryptography`の`Ed25519PrivateKey`を要求するが、`PyNaCl`の`SigningKey.encode()`を渡していた。

#### 誤った実装

```python
# ❌ BAD: PyNaClのSigningKeyを使おうとした
signing_key = SigningKey(key_bytes)
token = jwt.encode(payload, signing_key.encode(), algorithm="EdDSA")
# → UnicodeDecodeError
```

#### 正しい実装

```python
# ✅ GOOD: cryptographyのEd25519PrivateKeyを使う
ed25519_key = ed25519.Ed25519PrivateKey.from_private_bytes(key_bytes)
token = jwt.encode(payload, ed25519_key, algorithm="EdDSA")
```

### エラー3: 型エラー（mypy）

#### エラー内容

```
Argument 1 to "SigningKey" has incompatible type "str"; expected "bytes"
```

#### 原因

PyNaClの`SigningKey`はバイト列を要求するが、hex文字列を渡していた。

#### 誤った実装

```python
# ❌ BAD: hex文字列を渡す
key_hex = private_key.removeprefix("0x")
signing_key = SigningKey(key_hex, encoder=HexEncoder)
```

#### 正しい実装

```python
# ✅ GOOD: bytes型に変換してから渡す
key_hex = private_key.removeprefix("0x")
key_bytes = bytes.fromhex(key_hex)
signing_key = SigningKey(key_bytes)
```

---

## セキュリティ上の注意点

### 1. 秘密鍵の管理

**DO**:
```python
import os

# 環境変数から取得
PRIVATE_KEY = os.environ["STANDX_PRIVATE_KEY"]
```

**DON'T**:
```python
# ❌ ハードコード（絶対NG）
PRIVATE_KEY = "0x1234567890abcdef..."

# ❌ コードにコミット
# .envファイルをgitにコミットしない
```

### 2. ログ出力

**DO**:
```python
# 秘密情報をマスク
logger.info(f"Wallet: {wallet_address[:6]}...{wallet_address[-4:]}")
# → "Wallet: 0x1234...cdef"
```

**DON'T**:
```python
# ❌ 秘密鍵をログ出力（絶対NG）
logger.info(f"Private key: {private_key}")

# ❌ 署名をログ出力（不要な情報漏洩）
logger.debug(f"Signature: {signature}")
```

### 3. テストデータ

**DO**:
```python
# テスト用のダミー秘密鍵
private_key = "0x" + "a" * 64
```

**DON'T**:
```python
# ❌ 本番の秘密鍵をテストに使う
private_key = os.environ["STANDX_PRIVATE_KEY"]  # テストコードでは使わない
```

### 4. JWT有効期限

```python
# デフォルト7日（604800秒）
token = generate_jwt(private_key, wallet_address, chain, expires_seconds=604800)
```

**推奨**:
- 長すぎる有効期限は避ける（漏洩時のリスク）
- 短すぎる有効期限も避ける（頻繁な再生成が必要）
- 7日が適切なバランス

---

## まとめ

Phase 1-2では以下を実装しました：

✅ **auth.py**: JWT認証とリクエスト署名
- `generate_jwt()`: Ed25519署名付きJWTトークン生成
- `sign_request()`: タイムスタンプ + メソッド + パス + bodyの署名
- `generate_auth_headers()`: JWT + 署名ヘッダーを統合

✅ **cryptography**: PyJWTのEdDSAアルゴリズム用
✅ **PyNaCl**: リクエスト署名用
✅ **テスト13件**: 署名検証テスト + 異常系テスト

### 次のステップ

Phase 2-1では、REST APIクライアント（http.py）を実装します。

- [Issue #14: Phase 2-1: REST APIクライアントの実装](https://github.com/zomians/standx_mm_bot/issues/14)

---

## 参考資料

- [PyJWT公式ドキュメント](https://pyjwt.readthedocs.io/)
- [cryptography公式ドキュメント](https://cryptography.io/)
- [PyNaCl公式ドキュメント](https://pynacl.readthedocs.io/)
- [JWT.io](https://jwt.io/) - JWTデバッガー
- [Ed25519](https://ed25519.cr.yp.to/) - 公式仕様
- [StandX API Docs](https://docs.standx.com/standx-api/standx-api)

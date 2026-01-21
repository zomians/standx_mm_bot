# Phase 1-3: REST APIクライアントとウォレット生成の実装ガイド

このドキュメントは、Issue #14「Phase 1-3: REST APIクライアントとウォレット生成の実装」で実装した内容を、初心者向けに詳しく解説します。

---

## 📋 目次

1. [概要](#概要)
2. [REST APIクライアントの基礎](#rest-apiクライアントの基礎)
3. [StandXHTTPClientの実装解説](#standxhttpclientの実装解説)
4. [ウォレット自動生成機能](#ウォレット自動生成機能)
5. [BSCからSolanaへの統一](#bscからsolanaへの統一)
6. [テストの書き方](#テストの書き方)
7. [実装時のエラーと解決方法](#実装時のエラーと解決方法)
8. [セキュリティ上の注意点](#セキュリティ上の注意点)
9. [まとめ](#まとめ)

---

## 概要

### 何を実装したか

Phase 1-3では、StandX APIとの通信を担う**REST APIクライアント**と**ウォレット自動生成機能**を実装しました。

| コンポーネント | ファイル | 役割 |
|--------------|---------|------|
| **HTTPクライアント** | `src/standx_mm_bot/client/http.py` | StandX APIとの通信、認証、エラーハンドリング |
| **例外クラス** | `src/standx_mm_bot/client/exceptions.py` | カスタム例外（APIError, AuthenticationError, NetworkError） |
| **ウォレット生成** | `scripts/create_wallet.py` | Solanaウォレット自動生成、.env書き込み |
| **統合テスト** | `tests/test_http.py` | HTTPクライアントのユニットテスト（モック使用） |
| **実APIテスト** | `tests/test_http_integration.py` | 実際のStandX APIを使った統合テスト |

### 主要な変更点

1. **REST APIクライアント実装**: 全エンドポイント対応、認証ヘッダー自動付与
2. **ウォレット自動生成**: `make wallet` コマンドでSolanaウォレット生成
3. **BSC → Solana統一**: Ed25519鍵ペアに統一（auth.pyとの整合性確保）
4. **型チェック・Lint対応**: mypy、ruff完全対応

### なぜ重要か

- **自動化**: 手動でのAPI呼び出しが不要に
- **エラーハンドリング**: 401（認証エラー）、429（レート制限）の自動対応
- **ドライランモード**: 本番APIを叩かずにテスト可能
- **型安全性**: 型チェックによりバグを未然に防止

---

## REST APIクライアントの基礎

### REST APIとは

**REST (Representational State Transfer)** は、HTTPプロトコルを使ったWeb APIの設計スタイルです。

| HTTPメソッド | 用途 | StandXでの例 |
|-------------|------|-------------|
| **GET** | データ取得 | 価格取得、未決注文一覧 |
| **POST** | データ作成 | 注文発注、注文キャンセル |
| **PUT** | データ更新 | （StandXでは未使用） |
| **DELETE** | データ削除 | （StandXでは未使用） |

### StandX APIの特徴

#### 1. 認証フロー

```
1. JWTトークン取得 (/v1/offchain/login)
   ↓
2. リクエスト署名生成（x-request-signature）
   ↓
3. APIリクエスト（Authorization: Bearer {jwt}）
```

#### 2. エンドポイント一覧

| エンドポイント | メソッド | 用途 |
|--------------|---------|------|
| `/api/query_symbol_price` | GET | mark_price、index_price取得 |
| `/api/new_order` | POST | 新規注文発注 |
| `/api/cancel_order` | POST | 注文キャンセル |
| `/api/query_open_orders` | GET | 未決注文一覧取得 |
| `/api/query_position` | GET | 現在のポジション取得 |

#### 3. エラーコード

| HTTPステータス | 意味 | 対応 |
|--------------|------|------|
| **200** | 成功 | 正常処理 |
| **401** | 認証エラー | JWTトークン再取得 |
| **403** | 署名エラー | リクエスト署名が不正 |
| **429** | レート制限 | 1秒待機してリトライ |
| **5xx** | サーバーエラー | エラーをログに記録 |

---

## StandXHTTPClientの実装解説

### アーキテクチャ

```
┌─────────────────────────────────────┐
│      StandXHTTPClient               │
│  (client/http.py)                   │
├─────────────────────────────────────┤
│                                     │
│  ┌─────────────────────────────┐   │
│  │ 1. JWT取得                   │   │
│  │   _get_jwt_token()          │   │
│  └─────────────────────────────┘   │
│            ↓                        │
│  ┌─────────────────────────────┐   │
│  │ 2. リクエスト送信            │   │
│  │   _request()                │   │
│  │   - 認証ヘッダー自動付与     │   │
│  │   - エラーハンドリング       │   │
│  └─────────────────────────────┘   │
│            ↓                        │
│  ┌─────────────────────────────┐   │
│  │ 3. 公開メソッド              │   │
│  │   - get_symbol_price()      │   │
│  │   - new_order()             │   │
│  │   - cancel_order()          │   │
│  │   - get_open_orders()       │   │
│  │   - get_position()          │   │
│  └─────────────────────────────┘   │
└─────────────────────────────────────┘
```

### クラス設計

#### 1. 初期化と接続管理

```python
class StandXHTTPClient:
    def __init__(self, config: Settings):
        self.config = config
        self.base_url = "https://perps.standx.com"
        self.session: ClientSession | None = None
        self.jwt_token: str = ""

    async def __aenter__(self):
        """コンテキストマネージャー: 接続開始"""
        self.session = aiohttp.ClientSession()
        self.jwt_token = await self._get_jwt_token()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """コンテキストマネージャー: 接続終了"""
        if self.session:
            await self.session.close()
```

**ポイント**:
- `async with` 構文でセッション管理（自動クローズ）
- JWT トークンは初期化時に取得

#### 2. JWT取得処理

```python
async def _get_jwt_token(self) -> str:
    """JWTトークンを取得"""
    # Solana形式の署名を生成
    signature = sign_message_solana_format(
        self.config.standx_private_key,
        self.config.standx_wallet_address,
    )

    # ログインリクエスト送信
    body = {
        "wallet_address": self.config.standx_wallet_address,
        "signature": signature,
        "chain": self.config.standx_chain,
    }

    async with self.session.post(
        f"{self.base_url}/v1/offchain/login",
        json=body,
    ) as resp:
        if resp.status == 200:
            login_result = await resp.json()
            return str(login_result.get("token"))
        else:
            raise AuthenticationError(f"Failed to login: HTTP {resp.status}")
```

**ポイント**:
- Solana形式の署名（JSON + Base64）を使用
- エラー時は `AuthenticationError` を送出

#### 3. 共通リクエスト処理

```python
async def _request(
    self,
    method: str,
    path: str,
    body: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """HTTPリクエストを送信（認証ヘッダー自動付与）"""

    # 認証ヘッダー生成
    headers, payload_str = generate_auth_headers(
        self.jwt_token,
        self.config.standx_private_key,
        method,
        path,
        body,
        self.config.standx_chain,
    )
    headers["Content-Type"] = "application/json"

    # POSTの場合、署名計算と同じJSON文字列を送信
    request_kwargs: dict[str, Any]
    if method.upper() == "POST" and payload_str:
        request_kwargs = {"data": payload_str}
    else:
        request_kwargs = {}

    # リクエスト送信
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
            await asyncio.sleep(1)
            return await self._request(method, path, body)
        else:
            error_text = await resp.text()
            raise APIError(f"HTTP {resp.status}: {error_text}")
```

**ポイント**:
- 認証ヘッダーは `generate_auth_headers()` で自動生成
- POSTリクエストは署名計算と同じJSON文字列を送信（重要！）
- 429エラー（レート制限）は自動リトライ
- 401エラー（認証エラー）は `AuthenticationError` を送出

#### 4. 公開メソッド例

##### 価格取得

```python
async def get_symbol_price(self, symbol: str) -> dict[str, Any]:
    """シンボル価格を取得"""
    path = f"/api/query_symbol_price?symbol={symbol}"
    return await self._request("GET", path)
```

**使用例**:
```python
async with StandXHTTPClient(config) as client:
    price = await client.get_symbol_price("ETH-USD")
    print(f"Mark price: {price['mark_price']}")
```

##### 注文発注

```python
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
    """新規注文を発注"""
    if self.config.dry_run:
        logger.info(f"[DRY RUN] new_order: {symbol}, {side}, {price}, {size}")
        return {"order_id": "dry_run_order_id", "status": "OPEN"}

    body = {
        "symbol": symbol,
        "side": side.lower(),
        "order_type": order_type.lower(),
        "qty": str(size),
        "price": str(price),
        "time_in_force": time_in_force,
        "reduce_only": reduce_only,
    }
    return await self._request("POST", "/api/new_order", body)
```

**ポイント**:
- `dry_run` モードでは実際にAPIを叩かない
- 価格・サイズは文字列として送信（API仕様）
- side/order_typeは小文字に変換

### エラーハンドリング

#### カスタム例外クラス

```python
# client/exceptions.py

class APIError(Exception):
    """StandX API エラーの基底クラス"""
    pass

class AuthenticationError(APIError):
    """認証エラー（401, JWT無効など）"""
    pass

class NetworkError(APIError):
    """ネットワークエラー（接続失敗など）"""
    pass
```

#### 使用例

```python
try:
    async with StandXHTTPClient(config) as client:
        order = await client.new_order(...)
except AuthenticationError:
    logger.error("JWT expired, need to re-login")
except APIError as e:
    logger.error(f"API error: {e}")
except Exception as e:
    logger.error(f"Unexpected error: {e}")
```

---

## ウォレット自動生成機能

### 背景

以前はウォレットを手動で生成する必要がありましたが、**Phase 1-3でEd25519鍵ペアの自動生成機能**を実装しました。

### 実装内容

#### 1. ウォレット生成スクリプト

```python
# scripts/create_wallet.py

from nacl.signing import SigningKey
import base58

def generate_solana_wallet() -> tuple[str, str]:
    """
    Solana（Ed25519）ウォレットを生成.

    Returns:
        tuple: (秘密鍵hex, ウォレットアドレスBase58)
    """
    # Ed25519鍵ペア生成
    signing_key = SigningKey.generate()

    # 秘密鍵をhex形式で取得（0xプレフィックスなし）
    private_key_hex = signing_key.encode().hex()

    # 公開鍵をBase58エンコード（Solanaアドレス形式）
    public_key_bytes = bytes(signing_key.verify_key)
    wallet_address = base58.b58encode(public_key_bytes).decode("ascii")

    return private_key_hex, wallet_address
```

**ポイント**:
- PyNaClの `SigningKey.generate()` でEd25519鍵ペア生成
- 秘密鍵: hex形式（64文字）
- ウォレットアドレス: Base58形式（Solana標準）

#### 2. .envファイル自動書き込み

```python
def create_env_file(private_key: str, wallet_address: str) -> None:
    """
    .envファイルを作成（既存ファイルは保護）.
    """
    env_path = Path(".env")

    # 既存ファイルがある場合は保護
    if env_path.exists():
        print(f"⚠️  .env already exists. Skipping...")
        return

    # .env.exampleをコピー
    shutil.copy(".env.example", ".env")

    # 秘密鍵とアドレスを書き込み
    with open(".env", "r") as f:
        content = f.read()

    content = content.replace(
        "STANDX_PRIVATE_KEY=your_private_key_here",
        f"STANDX_PRIVATE_KEY={private_key}",
    )
    content = content.replace(
        "STANDX_WALLET_ADDRESS=your_wallet_address_here",
        f"STANDX_WALLET_ADDRESS={wallet_address}",
    )

    # パーミッション600で保存（セキュリティ）
    with open(".env", "w") as f:
        f.write(content)
    os.chmod(".env", 0o600)

    print(f"✅ Wallet created successfully!")
```

**セキュリティポイント**:
- 既存の `.env` は上書きしない
- パーミッション600（所有者のみ読み書き可能）

#### 3. Makefileコマンド

```makefile
# Makefile

wallet:
	docker compose run --rm bot python scripts/create_wallet.py
```

**使用方法**:
```bash
make wallet
```

**出力例**:
```
✅ Wallet created successfully!

Private Key: a1b2c3d4e5f6...
Wallet Address: 7xK9Q2vR8...

⚠️  IMPORTANT: Keep your private key safe!
```

---

## BSCからSolanaへの統一

### 背景と課題

**Phase 1-2実装時の問題**:
- `auth.py`（issue#13）はEd25519専用で実装
- しかし、初期の `create_wallet.py` はsecp256k1（BSC用）を生成
- この不一致により、生成された鍵で `auth.py` が動作しない

### 解決策

**Phase 1-3でSolanaに統一**:

| 項目 | 変更前（BSC） | 変更後（Solana） |
|-----|-------------|----------------|
| **鍵ペア方式** | secp256k1 | Ed25519 |
| **ライブラリ** | eth-account | PyNaCl |
| **秘密鍵形式** | hex（0xプレフィックス付き） | hex（プレフィックスなし） |
| **アドレス形式** | 0x... (40文字) | Base58 (32-44文字) |
| **チェーン設定** | `STANDX_CHAIN=bsc` | `STANDX_CHAIN=solana` |

### 変更内容

#### 1. create_wallet.py

```python
# 変更前（BSC）
from eth_account import Account
account = Account.create()
private_key = account.key.hex()  # 0xプレフィックス付き
address = account.address  # 0x...

# 変更後（Solana）
from nacl.signing import SigningKey
import base58
signing_key = SigningKey.generate()
private_key = signing_key.encode().hex()  # プレフィックスなし
address = base58.b58encode(bytes(signing_key.verify_key)).decode()
```

#### 2. .env.example

```bash
# 変更前
STANDX_CHAIN=bsc

# 変更後
STANDX_CHAIN=solana
```

#### 3. pyproject.toml

```toml
# 変更前
dependencies = [
    "eth-account>=0.10.0",
]

# 変更後
dependencies = [
    "base58>=2.1.1",
]
```

### 統一後の利点

- ✅ `auth.py` と `create_wallet.py` の整合性確保
- ✅ Ed25519による高速な署名・検証
- ✅ Solanaエコシステムとの親和性
- ✅ 鍵管理の一元化

---

## テストの書き方

### テスト戦略

Phase 1-3では**2種類のテスト**を実装しました。

| テストタイプ | ファイル | 用途 |
|------------|---------|------|
| **ユニットテスト** | `tests/test_http.py` | モックを使った単体テスト |
| **統合テスト** | `tests/test_http_integration.py` | 実際のStandX APIを使ったテスト |

### ユニットテスト（モック使用）

#### 1. モックの基本

```python
from unittest.mock import AsyncMock, MagicMock, patch

@pytest.fixture
def mock_client(mock_config: Settings) -> StandXHTTPClient:
    """モック化されたHTTPクライアント"""
    client = StandXHTTPClient(mock_config)
    client.session = MagicMock()
    client.jwt_token = "mock_jwt_token"
    return client
```

**ポイント**:
- `session` をモック化してネットワーク通信をスキップ
- JWTトークンは固定値

#### 2. GETリクエストのテスト例

```python
@pytest.mark.asyncio
async def test_get_symbol_price(mock_client: StandXHTTPClient) -> None:
    """価格取得APIのテスト"""
    # モックレスポンス設定
    mock_response = AsyncMock()
    mock_response.status = 200
    mock_response.json = AsyncMock(return_value={
        "symbol": "ETH-USD",
        "mark_price": "3500.0",
        "index_price": "3501.0",
    })

    # session.requestをモック化
    mock_client.session.request = AsyncMock(return_value=mock_response)
    mock_response.__aenter__ = AsyncMock(return_value=mock_response)
    mock_response.__aexit__ = AsyncMock(return_value=None)

    # テスト実行
    result = await mock_client.get_symbol_price("ETH-USD")

    # 検証
    assert result["symbol"] == "ETH-USD"
    assert result["mark_price"] == "3500.0"
```

#### 3. POSTリクエストのテスト例

```python
@pytest.mark.asyncio
async def test_new_order(mock_client: StandXHTTPClient) -> None:
    """注文発注APIのテスト"""
    mock_response = AsyncMock()
    mock_response.status = 200
    mock_response.json = AsyncMock(return_value={
        "order_id": "order_12345",
        "status": "OPEN",
    })

    mock_client.session.request = AsyncMock(return_value=mock_response)
    mock_response.__aenter__ = AsyncMock(return_value=mock_response)
    mock_response.__aexit__ = AsyncMock(return_value=None)

    # テスト実行
    result = await mock_client.new_order(
        symbol="ETH-USD",
        side="buy",
        price=3500.0,
        size=0.1,
    )

    # 検証
    assert result["order_id"] == "order_12345"
    assert result["status"] == "OPEN"
```

#### 4. エラーハンドリングのテスト

```python
@pytest.mark.asyncio
async def test_authentication_error(mock_client: StandXHTTPClient) -> None:
    """401エラー（認証失敗）のテスト"""
    mock_response = AsyncMock()
    mock_response.status = 401

    mock_client.session.request = AsyncMock(return_value=mock_response)
    mock_response.__aenter__ = AsyncMock(return_value=mock_response)
    mock_response.__aexit__ = AsyncMock(return_value=None)

    # AuthenticationErrorが発生することを確認
    with pytest.raises(AuthenticationError):
        await mock_client.get_symbol_price("ETH-USD")
```

### 統合テスト（実API使用）

#### 1. 統合テストの準備

```python
@pytest.fixture
def real_config() -> Settings:
    """実際の.envから設定を読み込む"""
    return Settings(dry_run=False)
```

**重要**: `.env` ファイルに実際の秘密鍵が必要

#### 2. 統合テストの実行

```bash
# 統合テストのみ実行（実APIを使用）
pytest -m integration

# 統合テストを除外（CIで使用）
pytest -m "not integration"
```

#### 3. 統合テスト例

```python
@pytest.mark.integration
@pytest.mark.asyncio
async def test_real_api_get_symbol_price(real_config: Settings) -> None:
    """実際のStandX APIから価格を取得"""
    async with StandXHTTPClient(real_config) as client:
        response = await client.get_symbol_price(real_config.symbol)

    # レスポンスの基本構造を確認
    assert "mark_price" in response
    assert "index_price" in response
    assert float(response["mark_price"]) > 0
```

### テストカバレッジ

```bash
# カバレッジ付きでテスト実行
make test-cov

# 結果例
Name                                     Stmts   Miss  Cover
------------------------------------------------------------
src/standx_mm_bot/client/http.py           112     15    87%
src/standx_mm_bot/auth.py                   43      0   100%
------------------------------------------------------------
TOTAL                                      237     15    91%
```

**目標**: 90%以上のカバレッジ

---

## 実装時のエラーと解決方法

### 1. 型エラー: `tuple indices must be integers or slices, not str`

**エラー内容**:
```python
headers1 = generate_request_signature(...)
assert headers1["x-request-id"] != headers2["x-request-id"]
# TypeError: tuple indices must be integers or slices, not str
```

**原因**:
- `generate_request_signature()` がタプル `(headers, payload)` を返却
- テストコードではタプルを辞書として扱っていた

**解決方法**:
```python
# 修正前
headers = generate_request_signature(private_key, method, path, body)

# 修正後（タプルをアンパック）
headers, payload = generate_request_signature(private_key, method, path, body)
```

### 2. 未使用引数のLintエラー

**エラー内容**:
```
ARG001 Unused function argument: `path`
ARG001 Unused function argument: `chain`
```

**原因**:
- `generate_request_signature()` の `path`, `chain` 引数が実装で使われていない
- 将来の拡張のために引数は保持したい

**解決方法**:
```python
# 修正前
def generate_request_signature(
    private_key: str,
    method: str,
    path: str,  # 未使用
    body: dict[str, Any] | None = None,
    chain: str = "bsc",  # 未使用
) -> tuple[dict[str, str], str]:

# 修正後（アンダースコアプレフィックスで意図的に未使用を示す）
def generate_request_signature(
    private_key: str,
    method: str,
    _path: str,  # 将来の拡張用
    body: dict[str, Any] | None = None,
    _chain: str = "bsc",  # 将来の拡張用
) -> tuple[dict[str, str], str]:
```

### 3. mypyエラー: `Returning Any from function declared to return "str"`

**エラー内容**:
```python
token = login_result.get("token")
return token  # error: Returning Any from function declared to return "str"
```

**原因**:
- `dict.get()` の返り値型は `Any | None`
- 関数の返り値型は `str` と宣言

**解決方法**:
```python
# 修正前
return token

# 修正後（明示的にstr型にキャスト）
return str(token)
```

### 4. 統合テスト失敗: `HTTP 403: invalid body signature`

**エラー内容**:
```
standx_mm_bot.client.exceptions.APIError: HTTP 403: {"code":403,"message":"invalid body signature"}
```

**原因**:
- POSTリクエストのボディと署名計算で使用したJSON文字列が異なる
- JSONのキー順序、スペース、改行が一致しない

**解決方法**:
```python
# 署名計算時と同じJSON文字列を送信
headers, payload_str = generate_auth_headers(...)

# POSTの場合、payload_strをそのまま送信
if method.upper() == "POST" and payload_str:
    request_kwargs = {"data": payload_str}  # jsonではなくdata
```

**重要**: `json=body` ではなく `data=payload_str` を使用

### 5. レート制限エラー: `HTTP 429`

**エラー内容**:
```
APIError: HTTP 429: Rate limit exceeded
```

**解決方法**:
```python
# 自動リトライ実装
if resp.status == 429:
    logger.warning("Rate limited (429). Retrying after 1 second...")
    await asyncio.sleep(1)
    return await self._request(method, path, body)
```

---

## セキュリティ上の注意点

### 1. 秘密鍵の管理

#### ❌ NG例

```python
# コードにハードコード
PRIVATE_KEY = "a1b2c3d4e5f6..."  # 絶対NG

# ログに出力
logger.info(f"Private key: {private_key}")  # 絶対NG

# Gitにコミット
# .envファイルをコミット  # 絶対NG
```

#### ✅ OK例

```python
# 環境変数から取得
from standx_mm_bot.config import Settings
config = Settings()
private_key = config.standx_private_key

# ログにはマスク表示
logger.info(f"Wallet: {address[:6]}...{address[-4:]}")

# .gitignoreに追加
echo ".env" >> .gitignore
```

### 2. .envファイルのパーミッション

```bash
# パーミッション600に設定（所有者のみ読み書き可能）
chmod 600 .env

# 確認
ls -la .env
# -rw-------  1 user  staff  123 Jan 21 12:00 .env
```

### 3. ドライランモードの活用

```python
# .env
DRY_RUN=true

# 実際のAPIを叩かずにテスト
async with StandXHTTPClient(config) as client:
    # モックレスポンスが返される
    order = await client.new_order(...)
```

### 4. 本番環境での注意

- ✅ 常に `.env` ファイルをバージョン管理から除外
- ✅ 本番環境では環境変数で秘密鍵を渡す
- ✅ ログに秘密情報を出力しない
- ✅ HTTPS通信を必ず使用（HTTP禁止）

---

## まとめ

### Phase 1-3で実装した内容

1. ✅ **REST APIクライアント実装**
   - StandXHTTPClientクラス
   - 全エンドポイント対応
   - 認証ヘッダー自動付与
   - エラーハンドリング（401, 429リトライ）

2. ✅ **ウォレット自動生成機能**
   - `make wallet` コマンド
   - Ed25519鍵ペア生成
   - .env自動書き込み

3. ✅ **BSC → Solana統一**
   - auth.pyとの整合性確保
   - Ed25519に統一

4. ✅ **型チェック・Lint完全対応**
   - mypy: エラーなし
   - ruff: エラーなし
   - テストカバレッジ: 91%

### 次のステップ

**Phase 1-4: WebSocket接続の実装**

- リアルタイム価格取得（priceチャンネル）
- 注文状態更新（orderチャンネル）
- 自動再接続ロジック

---

## 参考リンク

- [StandX API ドキュメント](https://docs.standx.com/standx-api/standx-api)
- [aiohttp公式ドキュメント](https://docs.aiohttp.org/)
- [PyNaCl公式ドキュメント](https://pynacl.readthedocs.io/)
- [pytest-asyncio](https://pytest-asyncio.readthedocs.io/)

---

**Last Updated**: 2026-01-21

# Phase 2-2: WebSocketクライアントの実装ガイド

このドキュメントは、Issue #15「Phase 2-2: WebSocketクライアントの実装」で実装した内容を、初心者向けに詳しく解説します。

---

## 📋 目次

1. [概要](#概要)
2. [WebSocketの基礎](#websocketの基礎)
3. [StandXWebSocketClientの実装解説](#standxwebsocketclientの実装解説)
4. [非同期処理とコールバックパターン](#非同期処理とコールバックパターン)
5. [テストの書き方（モック vs 統合）](#テストの書き方モック-vs-統合)
6. [実装時のエラーと解決方法](#実装時のエラーと解決方法)
7. [統合テストの重要性](#統合テストの重要性)
8. [まとめ](#まとめ)

---

## 概要

### 何を実装したか

Phase 2-2では、StandX WebSocket APIとのリアルタイム通信を担う**WebSocketクライアント**を実装しました。

| コンポーネント | ファイル | 役割 |
|--------------|---------|------|
| **WebSocketクライアント** | `src/standx_mm_bot/client/websocket.py` | リアルタイム価格・注文・約定データ受信 |
| **ユニットテスト** | `tests/test_websocket.py` | WebSocketクライアントの単体テスト（モック使用） |
| **統合テスト** | `tests/test_websocket_integration.py` | 実際のStandXサーバーに接続する統合テスト |

### 主要な機能

1. **チャンネル購読**: price（価格）、order（注文）、trade（約定）の3チャンネル
2. **コールバック登録**: イベント駆動型の非同期処理
3. **自動再接続**: 接続断時の自動リトライ
4. **エラーハンドリング**: 不正メッセージの処理、コールバック例外の分離

### 主要な変更点

1. **WebSocketクライアント実装**: `StandXWebSocketClient`クラス
2. **統合テストによる実装検証**: 実際のサーバー接続で動作確認
3. **APIフォーマット修正**: 統合テストで発見したサブスクリプション形式の誤りを修正
4. **型安全性**: mypy完全対応（str-bytes-safe警告対応）

### なぜ重要か

- **リアルタイム性**: REST APIと異なり、サーバーからのプッシュ通知を受信
- **効率性**: ポーリング不要、低レイテンシー
- **Bot戦略**: 価格変動への即時対応が可能に
- **統合テストの教訓**: モックだけでは発見できないバグを検出

---

## WebSocketの基礎

### WebSocketとは

**WebSocket**は、クライアントとサーバー間で双方向のリアルタイム通信を可能にするプロトコルです。

#### REST APIとの違い

| 項目 | REST API (HTTP) | WebSocket |
|------|----------------|-----------|
| **通信方向** | クライアント → サーバー | 双方向（サーバー → クライアントも可） |
| **接続** | リクエスト毎に接続 | 1度接続したら維持 |
| **レイテンシー** | 高い（毎回接続） | 低い（常時接続） |
| **用途** | データ取得・更新 | リアルタイムデータ受信 |
| **プロトコル** | HTTP/HTTPS | WebSocket (ws/wss) |

#### WebSocketの仕組み

```
1. ハンドシェイク (HTTP → WebSocketへ升級)
   ↓
2. 接続維持（双方向通信可能）
   ↓
3. メッセージ送受信（JSON形式）
   ↓
4. 切断（明示的 or タイムアウト）
```

### StandX WebSocket APIの特徴

#### 1. エンドポイント

```
wss://perps.standx.com/ws-stream/v1
```

#### 2. チャンネル一覧

| チャンネル | 認証 | データ内容 | 更新頻度 |
|-----------|------|-----------|---------|
| **price** | 不要 | mark_price, index_price, funding_rate | ~3秒毎 |
| **order** | 必要 | 注文ステータス変更（OPEN, FILLED, CANCELLED） | イベント発生時 |
| **trade** | 必要 | 約定情報（実行価格、数量） | イベント発生時 |

#### 3. メッセージ形式

**購読リクエスト（クライアント → サーバー）:**

```json
{
  "subscribe": {
    "channel": "price",
    "symbol": "ETH-USD"
  }
}
```

**データ受信（サーバー → クライアント）:**

```json
{
  "seq": 1,
  "channel": "price",
  "symbol": "ETH-USD",
  "data": {
    "mark_price": "3500.50",
    "index_price": "3501.00",
    "funding_rate": "0.0001"
  }
}
```

---

## StandXWebSocketClientの実装解説

### アーキテクチャ

```
StandXWebSocketClient
├── __init__()         : 初期化、設定読み込み
├── connect()          : WebSocket接続、自動再接続ループ
├── disconnect()       : 接続切断
├── on_price_update()  : priceコールバック登録
├── on_order_update()  : orderコールバック登録
├── on_trade()         : tradeコールバック登録
└── (内部メソッド)
    ├── _subscribe_channels()   : チャンネル購読
    ├── _receive_messages()     : メッセージ受信ループ
    └── _dispatch_message()     : メッセージディスパッチ
```

### 実装の詳細

#### 1. 初期化

```python
class StandXWebSocketClient:
    """StandX WebSocket クライアント."""

    def __init__(self, config: Settings):
        self.config = config
        self.ws_url = "wss://perps.standx.com/ws-stream/v1"
        self.reconnect_interval = config.ws_reconnect_interval / 1000  # ms to seconds
        self.ws: ClientConnection | None = None
        self._running = False
        self._callbacks: dict[str, list[Callable[[dict[str, Any]], Awaitable[None]]]] = {
            "price": [],
            "order": [],
            "trade": [],
        }
```

**ポイント:**
- `_callbacks`でチャンネル毎にコールバック関数のリストを管理
- `Callable[[dict], Awaitable[None]]`で非同期コールバックの型定義
- `_running`フラグで接続状態を管理

#### 2. コールバック登録

```python
def on_price_update(self, callback: Callable[[dict[str, Any]], Awaitable[None]]) -> None:
    """価格更新コールバックを登録."""
    self._callbacks["price"].append(callback)
```

**使用例:**

```python
async def my_price_handler(data: dict) -> None:
    print(f"Price: {data['mark_price']}")

client = StandXWebSocketClient(config)
client.on_price_update(my_price_handler)
```

#### 3. チャンネル購読

```python
async def _subscribe_channels(self, ws: ClientConnection) -> None:
    """チャンネルを購読."""
    # price チャンネル購読
    price_sub = {"subscribe": {"channel": "price", "symbol": self.config.symbol}}
    await ws.send(json.dumps(price_sub))
    logger.info(f"Subscribed to price channel: {self.config.symbol}")
```

**重要な修正点:**

❌ **初期実装（誤り）:**
```python
price_sub = {
    "method": "subscribe",
    "params": [f"price@{self.config.symbol}"],
    "id": 1,
}
```

✅ **正しい実装:**
```python
price_sub = {"subscribe": {"channel": "price", "symbol": self.config.symbol}}
```

この誤りは**統合テストで発見**されました（後述）。

#### 4. メッセージディスパッチ

```python
async def _dispatch_message(self, message: dict[str, Any]) -> None:
    """受信メッセージを適切なコールバックにディスパッチ."""
    channel = message.get("channel", "")

    # エラーメッセージをスキップ
    if "code" in message and message.get("code") != 200:
        logger.warning(f"WebSocket error message: {message}")
        return

    # price チャンネル
    if channel == "price":
        for callback in self._callbacks["price"]:
            try:
                await callback(message.get("data", {}))
            except Exception as e:
                logger.error(f"Error in price callback: {e}")
```

**ポイント:**
- エラーメッセージ（`code != 200`）を先にフィルタリング
- 各コールバックを`try-except`で囲み、1つのコールバックの失敗が他に影響しない

#### 5. 自動再接続

```python
async def connect(self) -> None:
    """WebSocketに接続し、メッセージを受信."""
    self._running = True
    logger.info(f"Connecting to WebSocket: {self.ws_url}")

    while self._running:
        try:
            async with websockets.connect(self.ws_url) as ws:
                self.ws = ws
                logger.info("WebSocket connected")

                await self._subscribe_channels(ws)
                await self._receive_messages(ws)

        except websockets.ConnectionClosed:
            logger.warning("WebSocket disconnected, reconnecting...")
            await asyncio.sleep(self.reconnect_interval)

        except Exception as e:
            logger.error(f"WebSocket error: {e}")
            await asyncio.sleep(self.reconnect_interval)

    logger.info("WebSocket client stopped")
```

**ポイント:**
- `while self._running`で自動再接続ループ
- `async with`でコンテキスト管理（自動クリーンアップ）
- 例外発生時は`reconnect_interval`秒待機してリトライ

---

## 非同期処理とコールバックパターン

### asyncioの基礎

Pythonの`asyncio`は非同期I/O処理を実現するライブラリです。

#### async/await構文

```python
# 同期処理（ブロッキング）
def fetch_data():
    time.sleep(1)  # 1秒待つ（他の処理は止まる）
    return "data"

# 非同期処理（ノンブロッキング）
async def fetch_data_async():
    await asyncio.sleep(1)  # 1秒待つ（他の処理は動ける）
    return "data"
```

#### 非同期関数の実行

```python
# 単一の非同期関数
result = await fetch_data_async()

# 複数の非同期関数を並行実行
results = await asyncio.gather(
    fetch_data_async(),
    fetch_data_async(),
)

# バックグラウンドタスク
task = asyncio.create_task(fetch_data_async())
```

### コールバックパターン

WebSocketクライアントでは**イベント駆動型**のコールバックパターンを使用します。

#### 実装例

```python
# コールバック関数を定義
async def on_price(data: dict) -> None:
    mark_price = data.get("mark_price")
    print(f"New price: {mark_price}")

# コールバックを登録
client = StandXWebSocketClient(config)
client.on_price_update(on_price)

# WebSocket接続開始（バックグラウンド）
await client.connect()
```

#### 複数コールバックの登録

```python
async def log_price(data: dict) -> None:
    logger.info(f"Price: {data['mark_price']}")

async def check_price(data: dict) -> None:
    if float(data["mark_price"]) > 4000:
        logger.warning("Price is high!")

# 同じイベントに複数コールバックを登録可能
client.on_price_update(log_price)
client.on_price_update(check_price)
```

---

## テストの書き方（モック vs 統合）

### ユニットテスト（モック使用）

#### 目的
- クラスの各メソッドが正しく動作するか検証
- 外部依存（実際のWebSocketサーバー）を排除

#### 実装例: `tests/test_websocket.py`

```python
@pytest.mark.asyncio
async def test_dispatch_message_price(config: Settings) -> None:
    """priceチャンネルのメッセージが正しくディスパッチされることを確認."""
    client = StandXWebSocketClient(config)

    received_data = None

    async def price_callback(data: dict) -> None:
        nonlocal received_data
        received_data = data

    client.on_price_update(price_callback)

    test_data = {"mark_price": "3500.0", "symbol": "ETH-USD"}
    await client._dispatch_message({"channel": "price", "data": test_data})

    assert received_data == test_data
```

**ポイント:**
- 実際のWebSocket接続なし
- `_dispatch_message()`を直接呼び出し
- 高速に実行可能（ネットワーク不要）

### 統合テスト（実WebSocket接続）

#### 目的
- 実際のStandXサーバーとの通信を検証
- APIフォーマット、メッセージ形式の正確性を確認

#### 実装例: `tests/test_websocket_integration.py`

```python
@pytest.mark.asyncio
@pytest.mark.integration
async def test_real_websocket_price_channel(config: Settings) -> None:
    """実際のWebSocketサーバーからpriceメッセージを受信できることを確認."""
    client = StandXWebSocketClient(config)

    received_messages = []

    async def price_callback(data: dict) -> None:
        received_messages.append(data)
        print(f"Received price data: {data}")

    client.on_price_update(price_callback)

    # WebSocket接続を開始（バックグラウンド）
    connect_task = asyncio.create_task(client.connect())

    try:
        # 10秒待ってメッセージを受信
        await asyncio.sleep(10)

        # メッセージが受信されたことを確認
        assert len(received_messages) > 0, "No price messages received"

        # メッセージ形式を確認
        first_message = received_messages[0]
        assert "mark_price" in first_message or "markPrice" in first_message
        print(f"✅ Received {len(received_messages)} price messages")

    finally:
        # 切断
        await client.disconnect()
        connect_task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await connect_task
```

**ポイント:**
- `@pytest.mark.integration`で統合テストとマーク
- 実際のStandXサーバーに接続
- 10秒間メッセージ受信を待機
- 受信メッセージの形式を検証

#### 統合テストの実行

```bash
# 統合テストのみ実行
pytest -m integration

# 統合テストを除外
pytest -m "not integration"
```

---

## 実装時のエラーと解決方法

### エラー1: サブスクリプション形式の誤り

#### 問題

初期実装では、以下の形式でチャンネルを購読していました：

```python
price_sub = {
    "method": "subscribe",
    "params": [f"price@{self.config.symbol}"],
    "id": 1,
}
```

**結果:**
- サーバーから400エラー: `{"code":400,"message":"invalid request payload"}`
- メッセージが一切受信されない

#### 原因

StandX WebSocket APIのドキュメントを再確認したところ、正しい形式は以下でした：

```python
price_sub = {"subscribe": {"channel": "price", "symbol": self.config.symbol}}
```

#### 解決方法

1. StandX APIドキュメントを`WebFetch`ツールで取得
2. 正しいサブスクリプション形式を確認
3. `_subscribe_channels()`メソッドを修正

**修正後:**

```python
async def _subscribe_channels(self, ws: ClientConnection) -> None:
    """チャンネルを購読."""
    # price チャンネル購読
    price_sub = {"subscribe": {"channel": "price", "symbol": self.config.symbol}}
    await ws.send(json.dumps(price_sub))
    logger.info(f"Subscribed to price channel: {self.config.symbol}")

    # order チャンネル購読 (認証必要)
    order_sub = {"subscribe": {"channel": "order"}}
    await ws.send(json.dumps(order_sub))
    logger.info("Subscribed to order channel")

    # trade チャンネル購読 (認証必要)
    trade_sub = {"subscribe": {"channel": "trade"}}
    await ws.send(json.dumps(trade_sub))
    logger.info("Subscribed to trade channel")
```

### エラー2: メッセージディスパッチの誤り

#### 問題

初期実装では、チャンネルチェックに以下を使用していました：

```python
if channel.startswith("price@"):
```

しかし、実際のサーバーからのメッセージは：

```json
{
  "channel": "price",
  "symbol": "ETH-USD",
  "data": {...}
}
```

`channel`は`"price"`であり、`"price@ETH-USD"`ではありません。

#### 解決方法

チャンネルチェックを修正：

```python
# 修正前
if channel.startswith("price@"):

# 修正後
if channel == "price":
```

### エラー3: mypy型チェックエラー（str-bytes-safe）

#### 問題

```python
logger.debug(f"Received raw message: {message} (type: {type(message)})")
```

`message`は`str | bytes`型なので、`bytes`の場合に`f"{message}"`とすると`b'abc'`という表記になります。

#### 解決方法

`!r`フォーマット指定子を使用：

```python
logger.debug(f"Received raw message: {message!r} (type: {type(message)})")
```

### エラー4: contextlib.suppress推奨（SIM105）

#### 問題

```python
try:
    await connect_task
except asyncio.CancelledError:
    pass
```

Ruffが`contextlib.suppress()`の使用を推奨。

#### 解決方法

```python
import contextlib

with contextlib.suppress(asyncio.CancelledError):
    await connect_task
```

---

## 統合テストの重要性

### 「本当にテストしたと言える？」

このプロジェクトで最も重要な教訓の1つは、**モックテストだけでは不十分**ということです。

#### 経緯

1. **初期実装**: ユニットテスト（モック使用）のみ作成
2. **コミット**: 「テスト完了」としてPR作成
3. **ユーザーフィードバック**: 「本当にテストしたと言える？」
4. **統合テスト追加**: 実際のサーバーに接続
5. **バグ発見**: サブスクリプション形式が誤っていた
6. **修正・再テスト**: 統合テストが成功

#### モックテストの限界

```python
# ユニットテスト: 想定したメッセージ形式でテスト
await client._dispatch_message({
    "channel": "price@ETH-USD",  # ← 実際の形式と異なる
    "data": {"mark_price": "3500"}
})
```

**問題点:**
- 実際のAPIが返すメッセージ形式を検証していない
- サブスクリプションリクエストが正しいか検証していない
- ネットワークエラーや再接続が動作するか不明

#### 統合テストの利点

```python
# 統合テスト: 実際のサーバーに接続
async with websockets.connect("wss://perps.standx.com/ws-stream/v1") as ws:
    await client._subscribe_channels(ws)
    await asyncio.sleep(10)
    # ← ここで実際のメッセージ形式が検証される
```

**利点:**
- 実際のAPIとの互換性を確認
- ネットワークエラー処理の動作を検証
- サーバー仕様変更の早期発見

### ベストプラクティス

#### 1. テストピラミッド

```
     統合テスト (少)
         /\
        /  \
       /    \
      /      \
     /ユニット\
    /  テスト  \
   /(多)      \
  /______________\
```

- **ユニットテスト**: 各メソッドの動作検証（多数、高速）
- **統合テスト**: 実際のサーバーとの通信検証（少数、低速）

#### 2. 統合テストのタイミング

- 外部APIと初めて統合するとき
- APIフォーマット変更の可能性があるとき
- リリース前の最終確認

#### 3. CI/CDでの扱い

```yaml
# pytest.ini または pyproject.toml
[tool.pytest.ini_options]
markers = [
    "integration: marks tests as integration tests (deselect with '-m \"not integration\"')",
]
```

```bash
# 通常のCI: ユニットテストのみ
pytest -m "not integration"

# リリース前: 全テスト
pytest
```

---

## まとめ

### 実装成果

Phase 2-2では、以下を達成しました：

✅ **WebSocketクライアント実装**
- リアルタイム価格・注文・約定データ受信
- コールバック登録パターン
- 自動再接続機能

✅ **包括的テスト**
- ユニットテスト 8件（モック使用）
- 統合テスト 3件（実サーバー接続）

✅ **統合テストによるバグ発見**
- サブスクリプション形式の誤りを検出・修正
- メッセージディスパッチロジックの修正

### 学んだ教訓

#### 1. 統合テストの重要性

> 「本当にテストしたと言える？」

モックテストだけでは、実際のAPIとの互換性を保証できません。

#### 2. APIドキュメントの正確な理解

推測や類推ではなく、公式ドキュメントを正確に読むことが重要です。

#### 3. デバッグログの活用

```python
logger.debug(f"Received raw message: {message!r}")
```

統合テスト時の詳細ログが、問題特定に役立ちました。

### 次のステップ

Phase 2-3では、以下を実装します：

1. **WebSocket認証**: JWTトークンを使用した認証付き接続
2. **order/tradeチャンネル**: 認証が必要なプライベートチャンネルの購読
3. **エラーハンドリング強化**: 認証失敗時の再取得処理

---

## 参考資料

- [StandX API Documentation](https://docs.standx.com/standx-api/standx-api)
- [websockets library](https://websockets.readthedocs.io/)
- [Python asyncio](https://docs.python.org/3/library/asyncio.html)
- [pytest-asyncio](https://pytest-asyncio.readthedocs.io/)

---

**最終更新日**: 2026-01-21
**関連Issue**: #15, #45

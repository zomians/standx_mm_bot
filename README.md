# StandX MM Bot

StandX の Maker Points / Maker Uptime を最大化するための Market Making Bot。

**目的**: **約定させずに板に居続けること**を自動化する。

---

## 概要

StandX は「板に居続けること」に報酬が出る Perp DEX。このBotは以下を自動化する：

| 報酬プログラム | 条件 | Bot の役割 |
|----------------|------|-----------|
| **Maker Points** | 板上に3秒以上、mark_price ± 10bps 以内で 100% | 距離を維持し続ける |
| **Maker Uptime** | 毎時間30分以上、両サイド ± 10bps 以内 | 空白時間ゼロで板に居続ける |

### 設計思想

```
約定 = 失敗
```

| 項目 | 方針 |
|------|------|
| 約定 | **しない**（手数料ゼロ、FRリスクゼロ） |
| 建玉 | **持たない**（清算リスクゼロ） |
| 距離 | 10bps以内だが約定しない位置 |

価格が近づいてきたら → **逃げる**（キャンセル or 外側に移動）

### 現実的な制約

完全に約定を避けることは不可能：

| シナリオ | 発生確率 | 影響 |
|----------|----------|------|
| 急激な価格変動 | 中 | 逃げ遅れて約定 |
| WebSocket遅延 | 低〜中 | 反応遅れて約定 |
| API遅延 | 低 | キャンセル間に合わず |

### 厳格モード（即クローズ）

意図せず約定した場合の対処：

```
約定検知 → 即座に成行で反対売買 → 建玉ゼロに戻す
```

- 手数料は発生する
- しかし建玉リスク（FR、清算）はゼロを維持

---

## 技術スタック

| カテゴリ | 技術 |
|----------|------|
| 言語 | Python 3.12+ |
| 非同期 | asyncio, aiohttp |
| WebSocket | websockets |
| 型チェック | mypy |
| Lint/Format | Ruff |
| テスト | pytest, pytest-asyncio |
| 設定管理 | pydantic-settings |

---

## クイックスタート

### 1. 環境構築

```bash
# リポジトリクローン
git clone https://github.com/zomians/standx_mm_bot.git
cd standx_mm_bot

# 仮想環境作成
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# 依存関係インストール
pip install -e ".[dev]"
```

### 2. 環境変数設定

```bash
cp .env.example .env
```

`.env` を編集：

```env
# 必須
STANDX_PRIVATE_KEY=0x...      # ウォレット秘密鍵
STANDX_WALLET_ADDRESS=0x...   # ウォレットアドレス
STANDX_CHAIN=bsc              # bsc or solana

# オプション
SYMBOL=ETH_USDC               # 取引ペア
TARGET_DISTANCE_BPS=8         # 目標距離 (bps)
ORDER_SIZE=0.1                # 片側注文サイズ
ESCAPE_THRESHOLD_BPS=3        # この距離まで近づいたら逃げる
```

### 3. 起動

```bash
# Bot 起動
python -m standx_mm_bot

# または
make run
```

---

## ディレクトリ構成

```
standx_mm_bot/
├── src/
│   └── standx_mm_bot/
│       ├── __init__.py
│       ├── __main__.py        # エントリーポイント
│       ├── config.py          # 設定管理
│       ├── auth.py            # JWT認証
│       ├── client/
│       │   ├── http.py        # REST API クライアント
│       │   └── websocket.py   # WebSocket クライアント
│       ├── core/
│       │   ├── order.py       # 注文管理
│       │   └── escape.py      # 約定回避ロジック
│       └── strategy/
│           └── maker.py       # Maker戦略ロジック
├── tests/
│   ├── test_auth.py
│   ├── test_order.py
│   └── test_escape.py
├── .env.example
├── .gitignore
├── pyproject.toml
├── Makefile
├── README.md
├── CONTRIBUTING.md
└── CLAUDE.md
```

---

## よく使うコマンド

### 開発

```bash
# Bot 起動
make run

# テスト実行
make test

# 型チェック
make typecheck

# Lint
make lint

# フォーマット
make format

# 全チェック (lint + typecheck + test)
make check
```

### Git

```bash
# ブランチ作成
git checkout main && git pull
git checkout -b feature/XX-description

# コミット
git commit -m "feat(scope): 内容 (issue#XX)"

# PR作成
gh pr create --title "タイトル" --body "Closes #XX"
```

---

## 設定パラメータ

### 基本設定

| パラメータ | 環境変数 | デフォルト | 説明 |
|-----------|----------|-----------|------|
| symbol | `SYMBOL` | `ETH_USDC` | 取引ペア |
| target_distance_bps | `TARGET_DISTANCE_BPS` | `8` | 目標距離 (10bps境界から2bps内側) |
| order_size | `ORDER_SIZE` | `0.1` | 片側注文サイズ |

### 約定回避設定

| パラメータ | 環境変数 | デフォルト | 説明 |
|-----------|----------|-----------|------|
| escape_threshold_bps | `ESCAPE_THRESHOLD_BPS` | `3` | 価格がこの距離まで近づいたら逃げる |
| outer_escape_distance_bps | `OUTER_ESCAPE_DISTANCE_BPS` | `15` | 逃げる先の距離 |

### 再配置トリガー

| パラメータ | 環境変数 | デフォルト | 説明 |
|-----------|----------|-----------|------|
| reposition_threshold_bps | `REPOSITION_THRESHOLD_BPS` | `2` | 10bps境界に近づいたら再配置 |
| price_move_threshold_bps | `PRICE_MOVE_THRESHOLD_BPS` | `5` | 価格変動トリガー |

### 接続設定

| パラメータ | 環境変数 | デフォルト | 説明 |
|-----------|----------|-----------|------|
| ws_reconnect_interval | `WS_RECONNECT_INTERVAL` | `5000` | 再接続間隔 (ms) |
| jwt_expires_seconds | `JWT_EXPIRES_SECONDS` | `604800` | JWT有効期限 (7日) |

---

## API エンドポイント

### Base URL

```
REST: https://perps.standx.com
WebSocket: wss://perps.standx.com/ws-stream/v1
```

### 主要エンドポイント

| 用途 | メソッド | パス |
|------|---------|------|
| 価格取得 | GET | `/api/query_symbol_price?symbol=ETH_USDC` |
| 注文発注 | POST | `/api/new_order` |
| 注文キャンセル | POST | `/api/cancel_order` |
| 未決注文一覧 | GET | `/api/query_open_orders` |

### WebSocket チャンネル

| チャンネル | 認証 | 用途 |
|-----------|------|------|
| `price` | 不要 | mark_price リアルタイム |
| `order` | 必要 | 注文状態変化 |
| `depth_book` | 不要 | 板情報（約定回避判断用） |

---

## 報酬条件まとめ

### Maker Points

| 距離帯 | 倍率 |
|--------|------|
| 0–10 bps | 100% |
| 10–30 bps | 50% |
| 30–100 bps | 10% |

**計算式**: `points = notional × multiplier × time / 86400`

**要件**: 板上に **3秒以上** 存在（約定不要）

### Maker Uptime

| 条件 | 値 |
|------|-----|
| 距離 | mark_price ± 10bps 以内 |
| サイド | Bid + Ask 両方必須 |
| 時間 | 毎時間 30分以上 |
| Boosted Tier | 70%以上稼働で 1.0x |
| Standard Tier | 50%以上稼働で 0.5x |

---

## Bot ロジック

### 基本フロー

```
1. 両サイドに指値注文を配置（mark_price ± 8bps）
2. 価格を監視
3. 価格が近づいてきたら → 逃げる
4. 価格が離れたら → 戻る
5. 10bps境界を超えそうなら → 再配置
```

### 約定回避ロジック

```
価格が注文に近づく（3bps以内）
  ↓
即座にキャンセル or 外側（15bps）に移動
  ↓
価格が離れたら元の位置（8bps）に戻る
```

### 優先順位

1. **約定回避** — 最優先。建玉を持たない
2. **10bps維持** — Uptime条件を満たす
3. **空白時間最小化** — 板に常に存在

---

## トラブルシューティング

### 認証エラー

```
Error: JWT authentication failed
```

**対処**:
1. `STANDX_PRIVATE_KEY` が正しいか確認
2. `STANDX_CHAIN` が正しいか確認 (bsc/solana)
3. JWT の有効期限切れ → 再認証

### WebSocket 切断

```
Warning: WebSocket disconnected, reconnecting...
```

**対処**:
- 自動再接続を待つ (デフォルト5秒間隔)
- ネットワーク接続を確認

### 意図せず約定した場合

```
Warning: Order filled unexpectedly
```

**原因**:
- 急激な価格変動で逃げが間に合わなかった
- WebSocket遅延

**対処**:
- `ESCAPE_THRESHOLD_BPS` を大きくする（早めに逃げる）
- 建玉が発生した場合は手動でクローズ

### 注文が通らない

```
Error: Order rejected
```

**対処**:
1. 残高確認: `GET /api/query_balance`
2. 価格が mark_price から離れすぎていないか確認
3. 注文サイズが最小単位を満たしているか確認

---

## 参考リンク

- [StandX API Docs](https://docs.standx.com/standx-api/standx-api)
- [Maker Uptime Program](https://docs.standx.com/docs/stand-x-campaigns/market-maker-uptime-program)
- [Mainnet Campaigns](https://docs.standx.com/docs/stand-x-campaigns/mainnet-campaigns)
